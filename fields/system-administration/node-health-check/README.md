# Node Health Check - Overview

> A ten-part series on **LBNL Node Health Check (NHC)**, the small bash framework that big HPC clusters trust to decide whether a compute node deserves a job. Read it in order the first time; come back to the troubleshooting page and cheat sheet whenever a node misbehaves at 2 AM.

## Who this is for

Cluster admins and HPC/AI platform engineers who run Slurm (or PBS, or Grid Engine, or even Kubernetes) and are tired of one sick node quietly eating a queue full of jobs. You should be comfortable with a root shell and `slurm.conf`. Bash wizardry is helpful for part 6, not required before it.

## The route

| # | Page | You'll walk away with |
|---|------|-----------------------|
| 1 | [Why your cluster needs a bouncer](/fields/system-administration/node-health-check/why-node-health-check.md) | The black-hole-node problem, what NHC is, and how it decides who gets in |
| 2 | [Build and install](/fields/system-administration/node-health-check/build-and-install.md) | NHC on your nodes from an RPM, a tarball or the Git tree, tested |
| 3 | [Writing nhc.conf](/fields/system-administration/node-health-check/writing-nhc-conf.md) | A real config for CPU, GPU and login nodes, plus match strings and contexts |
| 4 | [Slurm integration](/fields/system-administration/node-health-check/slurm-integration.md) | The drain/resume handshake, `HealthCheckNodeState`, prolog/epilog and reboots |
| 5 | [Rolling out to a fleet](/fields/system-administration/node-health-check/rollout-at-scale.md) | A dry-run → canary → enforce plan that won't drain your whole cluster on day one |
| 6 | [Writing custom checks](/fields/system-administration/node-health-check/custom-checks.md) | Your own `.nhc` module, with GPU examples and NHC-style fast bash |
| 7 | [Auto-remediation](/fields/system-administration/node-health-check/auto-remediation.md) | A safe detect → drain → fix → verify → resume loop with guard rails |
| 8 | [Troubleshooting](/fields/system-administration/node-health-check/troubleshooting.md) | Symptom-first fixes for the classic NHC headaches |
| 9 | [Architecture-driven NHC](/fields/system-administration/node-health-check/architecture-driven-nhc.md) | NHC generated from one cluster definition, cross-checked with `slurm.conf` and tested with real NHC |
| 10 | [Cheat sheet](/fields/system-administration/node-health-check/cheat-sheet.md) | Every command and knob from the series on one page |

## Contents

| File | Description |
|------|-------------|
| [why-node-health-check](/fields/system-administration/node-health-check/why-node-health-check.md) | Black-hole nodes, what NHC is and how it works |
| [build-and-install](/fields/system-administration/node-health-check/build-and-install.md) | Installing NHC from RPM, tarball or Git |
| [writing-nhc-conf](/fields/system-administration/node-health-check/writing-nhc-conf.md) | Config syntax, match strings, contexts and starter configs |
| [slurm-integration](/fields/system-administration/node-health-check/slurm-integration.md) | Wiring NHC into Slurm, PBS and cron |
| [rollout-at-scale](/fields/system-administration/node-health-check/rollout-at-scale.md) | Deploying NHC safely across hundreds of nodes |
| [custom-checks](/fields/system-administration/node-health-check/custom-checks.md) | Writing your own checks, GPU examples included |
| [architecture-driven-nhc](/fields/system-administration/node-health-check/architecture-driven-nhc.md) | Generating NHC configs from an architecture definition |
| [auto-remediation](/fields/system-administration/node-health-check/auto-remediation.md) | Automating fixes without automating disasters |
| [troubleshooting](/fields/system-administration/node-health-check/troubleshooting.md) | Symptom-first troubleshooting guide |
| [cheat-sheet](/fields/system-administration/node-health-check/cheat-sheet.md) | Commands, options and variables at a glance |

Example files for part 9: [`cluster-example.yaml`](/fields/system-administration/node-health-check/cluster-example.yaml), [`nhc_gen.py`](/fields/system-administration/node-health-check/nhc_gen.py), [`acme_arch.nhc`](/fields/system-administration/node-health-check/acme_arch.nhc).

## Versions this series targets

Written against **NHC 1.5** (released October 2026, the first feature release since 1.4.3 in 2022) and current Slurm. Where 1.4.3 behaves differently, the page says so. Upstream lives at [github.com/mej/nhc](https://github.com/mej/nhc).

## Related reading in this repo

- [Rebooting a Slurm cluster without losing jobs](/fields/schedulers/slurm-reboot-order.md): NHC is on its pre-flight checklist for a reason.
- [Schedulers intro](/fields/schedulers/intro.md): where node health checking sits in the scheduler's world.
- [The cluster that passed every test except the one that mattered](/fields/devops/kubernetes/nvidia-cluster-readiness-engine.md): what's beyond single-node checks.
