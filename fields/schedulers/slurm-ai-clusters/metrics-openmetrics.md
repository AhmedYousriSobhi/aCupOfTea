---
id: slurm-openmetrics
title: "Slurm Metrics Without an Exporter: OpenMetrics into VictoriaMetrics"
sidebar_label: "5. Metrics into VictoriaMetrics"
order: 5
summary: Slurm 25.11+ serves OpenMetrics from slurmctld - scraping it into VictoriaMetrics, idle CPUs fixed by DefMemPerCPU, MiB in _bytes metrics until 26.11, open access, and a tested alert.
level: intermediate
type: [concept, guide]
domains: [systems-and-hpc]
tags: [slurm, hpc, monitoring, victoriametrics]
relations:
  prerequisites: [vm-single-node, vm-metricsql-vmalert]
  related: [slurm-gpu-health-checks, slurm-backfill-tuning]
---

# Slurm Metrics Without an Exporter: OpenMetrics into VictoriaMetrics

> **Part 5 of [Slurm for AI Clusters](/fields/schedulers/slurm-ai-clusters/README.md)** Since 25.11, `slurmctld` can serve its own metrics over HTTP. By the end you'll scrape them into VictoriaMetrics, read the two numbers that explained a half-empty cluster, and have a unit-tested alert that survives the metric change in 26.11.

- [Idle CPUs, pending jobs](#idle-cpus-pending-jobs)
- [Turning it on](#turning-it-on)
- [Scraping it](#scraping-it)
- [The two numbers that explained it](#the-two-numbers-that-explained-it)
- [_bytes that are MiB](#_bytes-that-are-mib)
- [An alert, and the bug its test caught](#an-alert-and-the-bug-its-test-caught)
- [Who can read it](#who-can-read-it)
- [Back to the half-empty cluster](#back-to-the-half-empty-cluster)
- [References](#references)

---

## Idle CPUs, pending jobs

The cluster dashboard shows a third of the CPUs idle. The queue has jobs pending with reason `Resources`. Users send screenshots of both side by side: "the cluster is half empty and my 1-CPU job can't start". The admin checks `sinfo`: every node is `mix`, nothing is down or drained. The scheduler isn't broken. Something else is full.

> [!NOTE]
> Lab: Slurm **26.05.6** built from source on `s26a`–`s26c` (2 CPUs and `RealMemory=1000` each). VictoriaMetrics **v1.156.0** single-node, and `vmalert-tool` from the same release, as set up in the [VictoriaMetrics series](/fields/devops/victoriametrics/README.md). 23.11 doesn't have these endpoints; for older Slurm you need an external exporter.

---

## Turning it on

One line in `slurm.conf`, then restart `slurmctld`:

```text
MetricsType=metrics/openmetrics
```

The metrics are served by `slurmctld` itself, on its normal port (default 6817). No exporter process, no extra port:

```text
$ curl -s http://s26a:6817/metrics
slurmctld index of metrics endpoints:
  '/metrics/jobs': get job metrics
  '/metrics/nodes': get node metrics
  '/metrics/partitions': get partition metrics
  '/metrics/jobs-users-accts': get user and account jobs metrics
  '/metrics/scheduler': get scheduler metrics
```

A sample from each:

```text
slurm_jobs_pending 1
slurm_node_cpus_idle{node="s26a"} 1
slurm_nodes_drain 0
slurm_partition_jobs{partition="all"} 0
slurm_bf_cycle_cnt 0
```

---

## Scraping it

`metrics_path` is one per scrape job, so one job per endpoint, all pointing at the controller:

```yaml
# scrape.yml for victoria-metrics -promscrape.config=scrape.yml
scrape_configs:
  - job_name: slurm-jobs
    metrics_path: /metrics/jobs
    static_configs:
      - targets: ['s26a:6817']
  - job_name: slurm-nodes
    metrics_path: /metrics/nodes
    static_configs:
      - targets: ['s26a:6817']
  - job_name: slurm-scheduler
    metrics_path: /metrics/scheduler
    static_configs:
      - targets: ['s26a:6817']
```

```text
up{job="slurm-jobs"} 1
up{job="slurm-nodes"} 1
up{job="slurm-scheduler"} 1
count({__name__=~"slurm_.*"}) 146
```

146 series for three nodes. We left out `/metrics/jobs-users-accts` on purpose: the Slurm docs warn that per-user and per-account endpoints are "unbounded entities" that can "dramatically increase the amount of data stored". Add it only with a plan for its cardinality. The same docs note that every scrape takes locks inside `slurmctld`, so don't scrape it every second; the default 30 s or slower is fine.

---

## The two numbers that explained it

We reproduced the dashboard: a 2-node job (1 CPU per node) and a 1-CPU job, then one more 1-CPU job. The last one pended with `Resources` while `slurm_node_cpus_idle` said each node had a free CPU. The node metrics, side by side:

```text
slurm_node_cpus_idle{node="s26a"} 1
slurm_node_cpus_idle{node="s26b"} 1
slurm_node_cpus_idle{node="s26c"} 1
slurm_node_memory_alloc_bytes{node="s26a"} 1000
slurm_node_memory_alloc_bytes{node="s26b"} 1000
slurm_node_memory_alloc_bytes{node="s26c"} 1000
slurm_node_memory_bytes{node="s26a"} 1000
```

CPUs free, memory **fully allocated**. Each 1-CPU job had been given all of its node's memory. That's the default: with memory as a consumable resource (`CR_Core_Memory`) and no `DefMemPerCPU`, `DefMemPerGPU` or `DefMemPerNode`, a job that doesn't ask for memory gets the whole node's. `slurm.conf(5)` says `DefMemPerNode`'s default is `0 (unlimited)`, and the lab showed it:

```text
$ scontrol show config | grep DefMemPer
DefMemPerNode           = UNLIMITED
```

The fix is a default per CPU:

```text
DefMemPerCPU=400
```

After `scontrol reconfigure`, resubmitting the same three jobs (jobs already running keep their old allocation):

```text
JOBID CPUS MIN_MEMORY STATE NODELIST(REASON)
12 2 400M RUNNING s26a,s26b
13 1 400M RUNNING s26a
14 1 400M RUNNING s26b
slurm_node_cpus_idle{node="s26a"} 0
slurm_node_memory_alloc_bytes{node="s26a"} 800
```

All three running, `s26c` left completely free for a bigger job. Pick the value from your nodes: `RealMemory` divided by CPUs (or by GPUs, for `DefMemPerGPU` on GPU partitions), minus some room for the OS.

---

## _bytes that are MiB

Look at that sample again: `slurm_node_memory_bytes 1000`, on a node configured with `RealMemory=1000`, which is in MiB. In 26.05 the node memory metrics carry a `_bytes` name and a MiB value. `slurm_node_memory_free_bytes` read `4911`, the container host's free memory in MiB.

The 26.11 release notes fix it: "Report node memory metrics in bytes in the openmetrics endpoint. They were in MiB." So on the upgrade from 26.05 to 26.11, every node memory series jumps by a factor of 1,048,576. A dashboard that shows them as "GB" by dividing by 1024 is wrong before the upgrade and wrong in a different way after. An alert like `slurm_node_memory_free_bytes < 1024` (meant as "less than 1 GiB free") fires on every node before 26.11 and never after.

Rule of thumb: **write rules as ratios of two memory metrics.** A ratio has no unit, so it's right on both versions. The alert below does that.

---

## An alert, and the bug its test caught

The pattern from the story, as a rule: idle CPUs on a node whose memory is fully allocated.

```yaml
# slurm-rules.yml
groups:
  - name: slurm-capacity
    rules:
      - alert: SlurmStrandedCPUs
        # Left side sets $value: idle CPUs on a node whose memory is fully allocated.
        expr: (slurm_node_cpus_idle > 0) and (slurm_node_memory_alloc_bytes >= slurm_node_memory_bytes)
        for: 15m
        labels: {severity: warning}
        annotations:
          summary: "{{ $labels.node }}: {{ $value }} CPUs idle, memory fully allocated"
```

And a unit test for `vmalert-tool`, with one node in the trap and one fixed:

```yaml
# slurm-rules.test.yml
rule_files: [slurm-rules.yml]
evaluation_interval: 1m
tests:
  - interval: 1m
    input_series:
      - series: 'slurm_node_memory_bytes{node="s26a"}'
        values: '1000x30'
      - series: 'slurm_node_memory_alloc_bytes{node="s26a"}'
        values: '1000x30'
      - series: 'slurm_node_cpus_idle{node="s26a"}'
        values: '1x30'
      - series: 'slurm_node_memory_bytes{node="s26b"}'
        values: '1000x30'
      - series: 'slurm_node_memory_alloc_bytes{node="s26b"}'
        values: '800x30'
      - series: 'slurm_node_cpus_idle{node="s26b"}'
        values: '0x30'
    alert_rule_test:
      - eval_time: 10m
        groupname: slurm-capacity
        alertname: SlurmStrandedCPUs
        exp_alerts: []
      - eval_time: 20m
        groupname: slurm-capacity
        alertname: SlurmStrandedCPUs
        exp_alerts:
          - exp_labels: {node: s26a, severity: warning}
            exp_annotations: {summary: "s26a: 1 CPUs idle, memory fully allocated"}
```

```bash
vmalert-tool unittest --files slurm-rules.test.yml
```

```text
Unit Testing:  slurm-rules.test.yml
SUCCESS
```

That's the second version of the rule. The first had the two sides of `and` the other way round, and the test failed:

```text
Annotations:{summary="s26a: 1000 CPUs idle, memory fully allocated"}
```

`and` returns the **left** side's samples, so `$value` was the memory, not the CPU count. Swapping the sides fixed it. To check the test can fail, we changed `for: 15m` to `for: 25m`: `got:[]` at 20 minutes, `FAILED`.

On the live data, the expression returned all three nodes at the minute of the trap, and nothing after the fix.

---

## Who can read it

In our lab, `curl` with no credentials got HTTP 200 from every endpoint. That's the default. From the Slurm metrics guide: "By default, metrics endpoints do not require authentication. They are either accessible to everyone or to no one (with the exceptions of SlurmUser and root), depending on whether PrivateData is set."

| Setting | Effect |
| --- | --- |
| Nothing | Open to anyone who can reach port 6817 |
| `PrivateData` set | Closed except to SlurmUser and root, unless `MetricsParameters=ignore_private_data` |
| `MetricsAuthUsers=<users>` | Only those users (plus SlurmUser and root), with a JWT; overrides the other two |

The guide also points out that the metrics reveal job patterns and user activity. Port 6817 has to be reachable by every node and every client anyway, so a firewall rule doesn't fix it; decide who may read the metrics, and set `MetricsAuthUsers` for the scraper's user if the answer isn't "everyone".

---

## Back to the half-empty cluster

With `slurm_node_cpus_idle` and `slurm_node_memory_alloc_bytes` on the same graph, the answer to the screenshots takes one look: the CPUs were free, the memory wasn't, because every job without `--mem` got a whole node's worth. `DefMemPerCPU` fixed the default, the queue drained, and the `SlurmStrandedCPUs` alert now catches the next time it happens, for example a partition someone adds without a memory default.

The cluster wasn't half empty. It was full of memory nobody was using.

**Takeaway:** Slurm 25.11+ serves its own OpenMetrics from `slurmctld`, open by default; scrape one job per endpoint, look at idle CPUs and allocated memory together, write memory rules as ratios because the units change in 26.11, and unit-test the rules.

**Next:** [Part 6, Lab Build Cheatsheet](/fields/schedulers/slurm-ai-clusters/lab-build-cheatsheet.md), has every command used to build the lab behind this series.

---

## References

- [Slurm Metrics Guide](https://slurm.schedmd.com/metrics.html): endpoints, `MetricsType`, `MetricsAuthUsers`, `MetricsParameters`, security and performance notes.
- [slurm.conf(5)](https://slurm.schedmd.com/slurm.conf.html#OPT_DefMemPerCPU): `DefMemPerCPU`, `DefMemPerNode` (default unlimited), `SelectTypeParameters`.
- [Slurm 26.11 release notes](https://github.com/SchedMD/slurm/blob/master/RELEASE_NOTES.md): node memory metrics change from MiB to bytes.
- [VictoriaMetrics: scrape configuration](https://docs.victoriametrics.com/victoriametrics/sd_configs/): `scrape_configs`, `metrics_path`.
- [vmalert-tool](https://docs.victoriametrics.com/victoriametrics/vmalert-tool/): `unittest` file format.
- [MetricsQL and vmalert](/fields/devops/victoriametrics/metricsql-and-vmalert.md): the rule-testing workflow used here.
