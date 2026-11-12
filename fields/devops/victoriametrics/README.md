---
summary: A five-page VictoriaMetrics series plus a cheatsheet - why it exists, a locked-down single node, vmagent buffering, retention and backups, and alerts tested before they page anyone.
sidebar_label: VictoriaMetrics
sidebar_group: VictoriaMetrics
---

# VictoriaMetrics, for People Whose Prometheus Keeps Running Out of Room

A short series on VictoriaMetrics, the Prometheus-compatible metrics database, written for people who run clusters and are comfortable with a root shell. Start at page 1 and work down. Every command was run on a throwaway lab, and each page says what the docs say, what the lab showed, and what we recommend, separately.

Written against **VictoriaMetrics v1.156.0** (released 2026-11-09), with Prometheus 3.16.0 and node_exporter 1.12.1 for comparison.

---

## Contents

| File | Description |
| --- | --- |
| [1. The Prometheus That Ate the Head Node](/fields/devops/victoriametrics/why-victoriametrics.md) | What VictoriaMetrics is, its components, single-node vs cluster, what's free and what isn't, and what it's not for |
| [2. A Single Node You Can Trust](/fields/devops/victoriametrics/single-node-in-ten-minutes.md) | Verified install, systemd unit, scrape config, safe reloads, and the delete endpoint that is open by default |
| [3. vmagent and the Network Blip](/fields/devops/victoriametrics/vmagent-and-the-network-blip.md) | Buffering through an outage, the URL edit that silently deletes the buffer, and how to size the queue |
| [4. Retention, Full Disks and Backups](/fields/devops/victoriametrics/retention-disk-and-backups.md) | What retention really deletes and when, read-only mode that `/health` won't report, and backups proven by a restore |
| [5. MetricsQL Surprises and Alerts You Can Test](/fields/devops/victoriametrics/metricsql-and-vmalert.md) | Why `increase()` disagrees with Prometheus, rules with unit tests that fail when they should, and alerting from outside |
| [6. Cheatsheet](/fields/devops/victoriametrics/cheatsheet.md) | Every step from the series in order, as copy-paste commands, with a quick-reference table |

---

## How the pages were tested

- **Where:** a throwaway Ubuntu 24.04.5 sandbox (Linux 6.18, systemd 255), destroyed afterwards. It was a container, not a VM, so systemd wasn't running: unit files were linted with `systemd-analyze verify` but never started. Each page marks what wasn't run.
- **Binaries:** official release tarballs, checked against the published SHA-256 sums before use.
- **Failure paths too:** every check on these pages was also run against a broken input to prove it fails. Two of our own tests passed when they shouldn't have, and page 5 shows how we caught it.

## Related pages

- [GPU Allocation vs Utilization](/fields/devops/kubernetes/gpu-allocation-vs-utilization.md): what the numbers you store actually mean.
- [Predicting GPU node failures](/fields/system-administration/gpu-failure-prediction/README.md): a use for the metrics once you keep them long enough.