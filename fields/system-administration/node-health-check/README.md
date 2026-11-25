# Node Health Check - Overview


> A thirteen-part series on **LBNL Node Health Check (NHC)**, the small bash framework that big HPC clusters trust to decide whether a compute node deserves a job. Read it in order the first time; parts 12 and 13 share one quick guide with just the steps; come back to the troubleshooting page and cheat sheet whenever a node misbehaves at 2 AM.

## Who this is for

Cluster admins and HPC/AI platform engineers who run Slurm (or PBS, or Grid Engine, or even Kubernetes) and are tired of one sick node quietly eating a queue full of jobs. You should be comfortable with a root shell and `slurm.conf`. Bash wizardry is helpful for part 6, not required before it.

## The route

| # | Page | You'll walk away with |
|---|------|-----------------------|
| 1 | [Why your cluster needs a bouncer](/fields/system-administration/node-health-check/getting-started/why-node-health-check.md) | The black-hole-node problem, what NHC is, and how it decides who gets in |
| 2 | [Build and install](/fields/system-administration/node-health-check/getting-started/build-and-install.md) | NHC on your nodes from an RPM, a tarball or the Git tree, tested |
| 3 | [Writing nhc.conf](/fields/system-administration/node-health-check/getting-started/writing-nhc-conf.md) | A real config for CPU, GPU and login nodes, plus match strings and contexts |
| 4 | [Slurm integration](/fields/system-administration/node-health-check/getting-started/slurm-integration.md) | The drain/resume handshake, `HealthCheckNodeState`, prolog/epilog and reboots |
| 5 | [Rolling out to a fleet](/fields/system-administration/node-health-check/getting-started/rollout-at-scale.md) | A dry-run → canary → enforce plan that won't drain your whole cluster on day one |
| 6 | [Writing custom checks](/fields/system-administration/node-health-check/checks-and-remediation/custom-checks.md) | Your own `.nhc` module, with GPU examples and NHC-style fast bash |
| 7 | [Auto-remediation](/fields/system-administration/node-health-check/checks-and-remediation/auto-remediation.md) | A safe detect → drain → fix → verify → resume loop with guard rails |
| 8 | [Troubleshooting](/fields/system-administration/node-health-check/checks-and-remediation/troubleshooting.md) | Symptom-first fixes for the classic NHC headaches |
| 9 | [Architecture-driven NHC](/fields/system-administration/node-health-check/architecture-and-case-study/architecture-driven-nhc.md) | NHC generated from one cluster definition, cross-checked with `slurm.conf` and tested with real NHC |
| 10 | [Case study: build us an NHC](/fields/system-administration/node-health-check/architecture-and-case-study/case-study-build-me-an-nhc.md) | A client engagement on DGX H100 + AMD EPYC hardware: discovery questions, proposal, validation, final answer |
| 11 | [Cheat sheet](/fields/system-administration/node-health-check/cheat-sheet.md) | Every command and knob from the series on one page |
| 12 | [GPU heat: the ceiling](/fields/system-administration/node-health-check/gpu-temperature/gpu-temperature-ceiling.md) | One `dcgmi` call, a ceiling rule that drains without killing jobs, and a check that never drains on a failed read |
| 13 | [GPU heat: the idle timer](/fields/system-administration/node-health-check/gpu-temperature/gpu-temperature-idle-timer.md) | A warn-then-drain timer for GPUs that stay warm while idle, gated on node state and GPU memory |

## Contents

| File | Description |
|------|-------------|
| [cheat-sheet](/fields/system-administration/node-health-check/cheat-sheet.md) | Part 11: commands, options and variables at a glance |

| Directory | Description |
|-----------|-------------|
| [getting-started](/fields/system-administration/node-health-check/getting-started/README.md) | Parts 1-5: what NHC is, install, config, Slurm integration, rollout |
| [checks-and-remediation](/fields/system-administration/node-health-check/checks-and-remediation/README.md) | Parts 6-8: custom checks, auto-remediation, troubleshooting |
| [architecture-and-case-study](/fields/system-administration/node-health-check/architecture-and-case-study/README.md) | Parts 9-10: configs generated from one definition, and a client case study, with their tools |
| [gpu-temperature](/fields/system-administration/node-health-check/gpu-temperature/README.md) | Parts 12-13 and a quick guide: GPU over-temperature detection |

## Versions this series targets

Written against **NHC 1.5** (released October 2026, the first feature release since 1.4.3 in 2022) and current Slurm. Where 1.4.3 behaves differently, the page says so. Upstream lives at [github.com/mej/nhc](https://github.com/mej/nhc).

## Related reading in this repo

- [Rebooting a Slurm cluster without losing jobs](/fields/schedulers/slurm-cluster-operations/slurm-reboot-order.md): NHC is on its pre-flight checklist for a reason.
- [Schedulers intro](/fields/schedulers/slurm-intro.md): where node health checking sits in the scheduler's world.
- [The cluster that passed every test except the one that mattered](/fields/devops/kubernetes/nvidia-cluster-readiness-engine.md): what's beyond single-node checks.

<!-- related-block -->
<div class="mentioned-in">

**Mentioned in**

- [Architecture-Driven NHC: Generate Health Checks from Your Cluster's Definition](/fields/system-administration/node-health-check/architecture-and-case-study/architecture-driven-nhc.md) — Describe your cluster's architecture once in YAML, generate every NHC config from it, cross-check it against slurm.conf, and prove the result with real NHC before it ships.
- [Auto-Remediation: From Detected to Fixed, Safely](/fields/system-administration/node-health-check/checks-and-remediation/auto-remediation.md) — Turn NHC drains into automatic fixes with an escalation ladder, built-in fix actions, a node-doctor loop on the controller, and guard rails against reboot storms.
- [Build and Install NHC](/fields/system-administration/node-health-check/getting-started/build-and-install.md) — Get NHC onto your nodes from a release RPM, the release tarball or the Git tree, run its unit tests and know where every file lands.
- [Case Study: "Build Us an NHC", From a Vague Ask to a Validated Proposal](/fields/system-administration/node-health-check/architecture-and-case-study/case-study-build-me-an-nhc.md) — A client asks for an NHC for their DGX H100 and AMD EPYC Slurm cluster; the discovery questions, first proposal, validation against vendor specs, and the final answer.
- [Glossary](/references/glossary.md) — Short definitions of the acronyms used across the pages (GPU, MPI, NUMA, RDMA, QoS and more), each with a pointer to the page that explains it properly.
- [GPU Temperature in a Health Check: The Ceiling Rule](/fields/system-administration/node-health-check/gpu-temperature/gpu-temperature-ceiling.md) — Add a GPU over-temperature ceiling to a health-check script: read temperature with one dcgmi call, drain without killing jobs, fail safe when the sensor can't be read, and pick the number.
- [GPU Temperature in a Health Check: The Idle Timer](/fields/system-administration/node-health-check/gpu-temperature/gpu-temperature-idle-timer.md) — Catch GPUs that run warm while doing nothing: a warn-then-drain timer, why 0% utilization alone is not idle, using the Slurm node state, and a read-only fleet scan before you enforce.
- [Is the Prediction Any Good?](/fields/system-administration/gpu-failure-prediction/scoring-and-backtesting.md) — How to judge GPU failure predictions - base rates, precision, recall, lead time, horizons, label quality, leakage and drift - and when a learned model is worth it.
- and 11 more

</div>
