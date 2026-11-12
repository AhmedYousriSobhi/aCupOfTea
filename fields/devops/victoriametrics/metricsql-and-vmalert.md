---
id: vm-metricsql-vmalert
title: "MetricsQL Surprises and Alerts You Can Test"
sidebar_label: "5. MetricsQL and tested alerts"
order: 5
summary: Why increase() gives different answers in Prometheus and VictoriaMetrics on the same data, and alert rules whose tests are proven to fail when the rule is wrong.
level: intermediate
type: [concept, guide]
domains: [devops, systems-and-hpc]
tags: [victoriametrics, prometheus, monitoring]
relations:
  prerequisites: [vm-single-node]
  related: [vm-retention-backups, vm-vmagent-buffering]
---

# MetricsQL Surprises and Alerts You Can Test

> **Part 5 of the [VictoriaMetrics series](/fields/devops/victoriametrics/README.md).** [Part 4](/fields/devops/victoriametrics/retention-disk-and-backups.md) kept the data safe. This page is about asking it questions: where MetricsQL and PromQL disagree on the same data, and how to write alert rules with tests that would actually catch a broken rule.

- [MetricsQL Surprises and Alerts You Can Test](#metricsql-surprises-and-alerts-you-can-test)
  - [The bug report that wasn't](#the-bug-report-that-wasnt)
  - [Same data, two answers](#same-data-two-answers)
  - [Why they disagree](#why-they-disagree)
  - [Prometheus 3.16 closed the gap, and VictoriaMetrics can't read it](#prometheus-316-closed-the-gap-and-victoriametrics-cant-read-it)
  - [Other differences you'll notice](#other-differences-youll-notice)
  - [Three rules that watch the watchers](#three-rules-that-watch-the-watchers)
  - [Tests that can fail](#tests-that-can-fail)
  - [How our own tests lied to us](#how-our-own-tests-lied-to-us)
  - [Run vmalert](#run-vmalert)
  - [Back to the bug report](#back-to-the-bug-report)
  - [References](#references)

---

## The bug report that wasn't

You're halfway through a migration. Prometheus and VictoriaMetrics both scrape the Slurm exporter, and someone puts the same panel on both: "jobs finished in the last 5 minutes". Prometheus says 15.79. VictoriaMetrics says 15. The ticket says "VictoriaMetrics is losing data".

It isn't. Fifteen is the right answer, and 15.79 is a deliberate estimate. Here's the proof.

---

## Same data, two answers

> [!NOTE]
> Lab: Prometheus **3.16.0** and VictoriaMetrics **v1.156.0** on a throwaway Ubuntu 24.04.5 sandbox.

Our first try scraped one counter with both databases at once. Even the raw value disagreed (5 vs 4), because the two scrapers hit the target at different moments. That compares scrape timing, not query languages. So we loaded **identical samples** into both: a counter `jobs_finished_total`, sampled every 15 seconds for 30 minutes, going up by exactly 1 every 20 seconds. Prometheus got it through `promtool tsdb create-blocks-from openmetrics`, VictoriaMetrics through `/api/v1/import/prometheus`. Then we asked both the same questions at the same timestamp, 15 minutes in:

| Query | Truth | Prometheus 3.16.0 | VictoriaMetrics v1.156.0 |
| --- | --- | --- | --- |
| `jobs_finished_total` | 45 | 45 | 45 |
| `increase(jobs_finished_total[1m])` | 3 | 4 | 3 |
| `increase(jobs_finished_total[2m])` | 6 | 6.857142857142857 | 6 |
| `increase(jobs_finished_total[5m])` | 15 | 15.789473684210526 | 15 |
| `rate(jobs_finished_total[5m])` | 0.05 | 0.05263157894736842 | 0.05 |

"Truth" is the counter's value at the query time minus its value one window earlier. VictoriaMetrics matched it every time. Prometheus was off by up to a third.

---

## Why they disagree

A window like `[5m]` rarely starts and ends exactly on a sample. Each database fills the gaps at the edges differently.

**Prometheus** uses only the samples inside the window, then **extrapolates** the slope out to the window's edges. That's why it returns fractions for a counter that only ever moves in whole steps.

**MetricsQL** also uses the **last sample before the window** as the starting point, and doesn't extrapolate. So `increase()` over a whole-number counter returns a whole number: the actual difference.

Neither is a bug; they answer slightly different questions. But for counters you'll read as "how many", like jobs, restarts or ECC errors, the MetricsQL answer is the one a human expects.

Rule of thumb: **when two dashboards disagree during a migration, compare raw samples first, functions second.** Most "data loss" turns out to be scrape timing or extrapolation.

---

## Prometheus 3.16 closed the gap, and VictoriaMetrics can't read it

Before writing "Prometheus can't do this", we checked. Prometheus 3.7.0 added two experimental **range selector modifiers** behind the `promql-extended-range-selectors` flag, and 3.16.0 made them stable and always on. Starting 3.16.0 with the old flag just logs that it's a no-op. On the same data:

| Query | Prometheus 3.16.0 |
| --- | --- |
| `increase(jobs_finished_total[5m] anchored)` | 15 |
| `increase(jobs_finished_total[1m] anchored)` | 3 |
| `increase(jobs_finished_total[5m] smoothed)` | 15 |

`anchored` uses the sample in effect at the window's start and the last sample at its end, without extrapolation. That's the same idea as MetricsQL.

Now the trap. Send that to VictoriaMetrics v1.156.0:

```text
{"status":"error","errorType":"400","error":"... argList: unexpected token \"anchored\"; want \",\", \")\"; unparsed data: \"anchored)\""}
```

HTTP 400. A Grafana dashboard written against Prometheus 3.16 with `anchored` will break when you point it at VictoriaMetrics, and plain `increase()` will quietly change its numbers in the other direction.

**Recommendation:** while you run both, keep shared dashboards to plain `increase()`/`rate()` and accept that the numbers differ slightly. Once you've moved, write queries for the database you actually run.

---

## Other differences you'll notice

From the MetricsQL docs, the ones that show up on real dashboards. We ran the first three on the same lab data; the last row is from the docs only.

| What | Prometheus 3.16.0 | VictoriaMetrics v1.156.0 |
| --- | --- | --- |
| `(-1)^0.5` | `NaN` | Empty result: `NaN` is dropped |
| `round(jobs_finished_total)`, `min_over_time(jobs_finished_total[1m])` | Result has no `__name__` | Keeps `__name__="jobs_finished_total"` |
| `rate(jobs_finished_total)`, no window | `parse error: expected type range vector` | `0.05`; window picked from `step` and the scrape interval |
| `rate()` when Grafana's `step` is smaller than the scrape interval | Can return empty, per the MetricsQL docs | Returns values, per the docs (not tested) |

Grafana doesn't draw `NaN` either, so the first row usually looks identical on screen. The last row is handy, but a query using it won't run on Prometheus.

---

## Three rules that watch the watchers

Parts 2 to 4 each found a failure the database won't announce. Here they are as alert rules, in a file vmalert reads:

```yaml
groups:
  - name: vm-self
    interval: 30s
    rules:
      - alert: VMStorageReadOnly
        expr: vm_storage_is_read_only == 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "VictoriaMetrics at {{ $labels.instance }} is read-only and rejecting writes"
      - alert: VMScrapeConfigReloadFailed
        expr: vm_promscrape_config_last_reload_successful == 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Scrape config reload failed on {{ $labels.instance }}; old config still active"
      - alert: VMAgentQueueBacklog
        expr: sum by (instance) (vmagent_remotewrite_pending_data_bytes) > 100e6
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "vmagent {{ $labels.instance }} has over 100 MB waiting to be sent"
```

| Rule | Comes from | Why this `for` |
| --- | --- | --- |
| `VMStorageReadOnly` | Part 4: `/health` says OK while writes fail | Every minute is lost data for unbuffered targets. Page fast |
| `VMScrapeConfigReloadFailed` | Part 2: a bad HUP keeps the old config silently | Gives a human time to fix their own typo before it pages |
| `VMAgentQueueBacklog` | Part 3: the queue grows during any outage | Short blips drain on their own. Fifteen minutes means it's not a blip |

Pick the 100 MB threshold from your own queue cap in part 3, not ours.

> [!IMPORTANT]
> These rules must run against a VictoriaMetrics that isn't the one being watched. Part 4 showed a read-only instance can't store its own `vm_storage_is_read_only`.

---

## Tests that can fail

**vmalert-tool** runs alert rules against fake series and checks what fires and when. The test file uses the Prometheus rule-test format, except that `promql_expr_test` is called `metricsql_expr_test`. Save this as `rules_test.yml` next to `rules.yml`:

```yaml
rule_files:
  - rules.yml
evaluation_interval: 30s
tests:
  - name: read-only fires after 1m, not before
    interval: 30s
    input_series:
      - series: 'vm_storage_is_read_only{instance="vm1:8428",path="/var/lib/victoriametrics"}'
        values: '0 0 1 1 1 1'
    alert_rule_test:
      - eval_time: 1m
        groupname: vm-self
        alertname: VMStorageReadOnly
        exp_alerts: []
      - eval_time: 2m
        groupname: vm-self
        alertname: VMStorageReadOnly
        exp_alerts:
          - exp_labels:
              severity: critical
              instance: vm1:8428
              path: /var/lib/victoriametrics
            exp_annotations:
              summary: "VictoriaMetrics at vm1:8428 is read-only and rejecting writes"
  - name: a short vmagent backlog does not page
    interval: 1m
    input_series:
      - series: 'vmagent_remotewrite_pending_data_bytes{instance="agent1:8429",url="1:secret-url"}'
        values: '0 200e6 200e6 200e6 0 0'
    alert_rule_test:
      - eval_time: 3m
        groupname: vm-self
        alertname: VMAgentQueueBacklog
        exp_alerts: []
  - name: a failed reload alerts after 5m, a quick fix doesn't
    interval: 1m
    input_series:
      - series: 'vm_promscrape_config_last_reload_successful{instance="vm1:8428"}'
        values: '1 0 0 0 0 0 0 0'
      - series: 'vm_promscrape_config_last_reload_successful{instance="vm2:8428"}'
        values: '1 0 0 1 1 1 1 1'
    alert_rule_test:
      - eval_time: 3m
        groupname: vm-self
        alertname: VMScrapeConfigReloadFailed
        exp_alerts: []
      - eval_time: 7m
        groupname: vm-self
        alertname: VMScrapeConfigReloadFailed
        exp_alerts:
          - exp_labels:
              severity: warning
              instance: vm1:8428
            exp_annotations:
              summary: "Scrape config reload failed on vm1:8428; old config still active"
```

The `values` shorthand reads as one sample per `interval`: `'0 0 1 1 1 1'` with a 30s interval means 0 at 0s and 30s, then 1 from 60s on.

```bash
vmalert-tool-prod unittest --files rules_test.yml; echo "exit=$?"
```

```text
Unit Testing:  rules_test.yml
SUCCESS
exit=0
```

A green test only proves something if a broken rule turns it red. So break the rules on purpose and make sure each break is caught. This script does that, and it's what we'd put in CI:

```bash
cat > check-rules.sh <<'EOF'
#!/usr/bin/env bash
# Pass: the real rules pass their tests, and every deliberately broken copy fails them.
set -uo pipefail
TOOL=${TOOL:-vmalert-tool-prod}
fail=0

$TOOL unittest --files rules_test.yml >/dev/null 2>&1 \
  && echo "PASS  real rules" || { echo "FAIL  real rules"; fail=1; }

mutants=(
  's/        for: 1m/        for: 5m/'
  's/        for: 5m/        for: 1m/'
  's/        for: 15m/        for: 1m/'
  's/vm_storage_is_read_only == 1/vm_storage_is_read_only == 2/'
)
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
cp rules_test.yml "$work/"
for m in "${mutants[@]}"; do
  sed "$m" rules.yml > "$work/rules.yml"
  if cmp -s rules.yml "$work/rules.yml"; then
    echo "SKIP  mutant matched nothing: $m"; fail=1; continue
  fi
  if $TOOL unittest --files "$work/rules_test.yml" >/dev/null 2>&1; then
    echo "FAIL  mutant survived: $m"; fail=1
  else
    echo "PASS  mutant caught:   $m"
  fi
done
exit $fail
EOF
chmod +x check-rules.sh
./check-rules.sh; echo "exit=$?"
```

```text
PASS  real rules
PASS  mutant caught:   s/        for: 1m/        for: 5m/
PASS  mutant caught:   s/        for: 5m/        for: 1m/
PASS  mutant caught:   s/        for: 15m/        for: 1m/
PASS  mutant caught:   s/vm_storage_is_read_only == 1/vm_storage_is_read_only == 2/
exit=0
```

Each **mutant** is a copy of the rules with one realistic mistake. If a mutant passes the tests, the tests have a blind spot. The `SKIP` check exists because a mutant that no longer matches anything (after someone edits a rule) would otherwise "pass" forever without testing anything.

---

## How our own tests lied to us

Writing those tests, we got three wrong. Each looked fine until a mutant ran.

**1. A failure for the wrong reason.** Our first broken copy lived in a subfolder, and vmalert-tool said `FAILED`. Great, except the message was `found no rule group in [broken/broken/rules.yml]`. Paths in `rule_files` are resolved **relative to the test file**, not your shell. The rules never loaded. Always read *why* a test failed.

**2. Checking at the wrong moment.** The backlog test first checked at 5m. A broken rule with `for: 1m` passed, because by 5m the backlog was gone and nothing would fire under either rule. Moving the check to 3m, mid-backlog, caught it.

**3. Same mistake, different rule.** The reload test checked only at 7m, after `vm2` had recovered. A `for: 1m` rule passed again. Adding a 3m check, while both were failing, fixed it.

The pattern in all three: **a test written to pass will pass.** Write the "should not fire" check at the moment a broken rule *would* fire.

> [!NOTE]
> vmalert-tool evaluates every group at the file's `evaluation_interval` (default `1m`) and ignores each group's own `interval`. That's why the test file sets `evaluation_interval: 30s` to match the group. Leave them different and you're testing different timing than production runs.

---

## Run vmalert

Check the rules file the same way as the scrape file in part 2. A broken file exits 255; a good one exits 0:

```bash
vmalert-prod -rule=/etc/vmalert/rules.yml -dryRun; echo "exit=$?"
```

Then run it against the **monitoring** instance, the one that scrapes your main database from outside:

```bash
vmalert-prod \
  -rule=/etc/vmalert/rules.yml \
  -datasource.url=http://10.0.0.6:8428 \
  -remoteWrite.url=http://10.0.0.6:8428 \
  -notifier.url=http://10.0.0.6:9093 \
  -httpListenAddr=10.0.0.6:8880
```

`-datasource.url` is where rules are evaluated, `-remoteWrite.url` is where alert state is written back (as the `ALERTS` series), and `-notifier.url` is your Alertmanager.

In the lab we replaced `-notifier.url` with `-notifier.blackhole` (no Alertmanager there), pointed a monitoring instance at a deliberately read-only one, and waited:

```bash
curl -s http://127.0.0.1:8880/api/v1/alerts
```

```text
VMStorageReadOnly firing 127.0.0.1:8433 2026-11-11T12:50:00+02:00
```

The `ALERTS{alertname="VMStorageReadOnly", alertstate="firing"}` series showed up in the monitoring instance too. Delivery through Alertmanager wasn't tested.

---

## Back to the bug report

The ticket gets closed with three lines: the raw samples are identical in both databases (45 and 45), Prometheus extrapolates `increase()` to the edges of the window, and 15 is the real number of jobs. If the team wants Prometheus to agree, `increase(...[5m] anchored)` does that on 3.16, as long as that panel never has to run on VictoriaMetrics.

The bigger change is what doesn't become a ticket any more. Each story in this series now ends in an alert, and each alert has a test that has caught a broken copy of it:

| The story | What used to happen | What happens now |
| --- | --- | --- |
| [Part 2](/fields/devops/victoriametrics/single-node-in-ten-minutes.md): a typo in the scrape file | The old config ran silently and the new target never appeared | `VMScrapeConfigReloadFailed` after 5 minutes |
| [Part 3](/fields/devops/victoriametrics/vmagent-and-the-network-blip.md): storage unreachable | Nobody knew until someone looked at a dashboard | `VMAgentQueueBacklog` once the queue has been over 100 MB for 15 minutes |
| [Part 4](/fields/devops/victoriametrics/retention-disk-and-backups.md): disk full, `/health` green | A weekend of missing data | `VMStorageReadOnly` after 1 minute, from a separate instance |

The next time two dashboards disagree, compare samples before functions. The next time something breaks, it should page you, and you'll already have proof the page works.

**Takeaway:** compare raw samples before blaming a database, and trust an alert rule only after its tests have caught a deliberately broken copy of it.

**Next:** [Part 6, the cheatsheet](/fields/devops/victoriametrics/cheatsheet.md), has every step from the series as copy-paste commands.

**Series index:** [VictoriaMetrics](/fields/devops/victoriametrics/README.md). Natural next steps are Grafana on top, and the cluster version once one node isn't enough.

---

## References

- [MetricsQL](https://docs.victoriametrics.com/victoriametrics/metricsql/): intentional differences from PromQL, including `rate`/`increase` behaviour, `NaN` handling and kept metric names.
- [vmalert-tool](https://docs.victoriametrics.com/victoriametrics/vmalert-tool/): unit tests, the test file format, `metricsql_expr_test`, and the `evaluation_interval` limitation.
- [vmalert](https://docs.victoriametrics.com/victoriametrics/vmalert/): `-datasource.url`, `-remoteWrite.url`, `-notifier.url`, `-notifier.blackhole`, `-dryRun`.
- [Prometheus rule unit testing](https://prometheus.io/docs/prometheus/latest/configuration/unit_testing_rules/): the test format vmalert-tool is compatible with.
- [Prometheus changelog](https://github.com/prometheus/prometheus/blob/main/CHANGELOG.md): 3.7.0 adds experimental `anchored` and `smoothed`; 3.16.0 makes them stable and always on.
- [Prometheus feature flags (3.14)](https://prometheus.io/docs/prometheus/3.14/feature_flags/): what `anchored` and `smoothed` do.
- [promtool tsdb](https://prometheus.io/docs/prometheus/latest/storage/#backfilling-from-openmetrics-format): backfilling from OpenMetrics, used to load identical data.
- [VictoriaMetrics single-node docs, import](https://docs.victoriametrics.com/victoriametrics/single-server-victoriametrics/#how-to-import-data-in-prometheus-exposition-format): the import endpoint used for the same data.