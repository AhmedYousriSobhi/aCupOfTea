
# Case Study: "Build Us an NHC", From a Vague Ask to a Validated Proposal

<!-- related-block -->
<div class="reading-time">17 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [Architecture-Driven NHC: Generate Health Checks from Your Cluster's Definition](/fields/system-administration/node-health-check/architecture-driven-nhc.md)

</div>


> **Part 10 of the [Node Health Check series](/fields/system-administration/node-health-check/README.md).** The final exam. Everything from parts 1-9, applied to one realistic engagement: a vague request, ten minutes of thinking, a discovery call, a first proposal, a coffee, a validation pass that changes the proposal, and the answer that goes back.

> [!NOTE]
> **What's real here.** The client and their names are invented. The hardware is not: every spec comes from NVIDIA's and AMD's published documentation (linked in [References](#references)). Every command output on this page was produced by running the series' tools ([`nhc_gen.py`](/fields/system-administration/node-health-check/nhc_gen.py), [`nhc_test_harness.sh`](/fields/system-administration/node-health-check/nhc_test_harness.sh)) against this cluster's definition with real NHC 1.5. The inputs are in [`case-study-delta-cluster.yaml`](/fields/system-administration/node-health-check/case-study-delta-cluster.yaml) and [`case-study-delta-expected.txt`](/fields/system-administration/node-health-check/case-study-delta-expected.txt).

## Table of Contents
- [The ask](#the-ask)
- [The ten minutes before you reply](#the-ten-minutes-before-you-reply)
- [Discovery: the questions, and why each one matters](#discovery-the-questions-and-why-each-one-matters)
- [What discovery told us](#what-discovery-told-us)
- [The first proposal](#the-first-proposal)
- [☕ Coffee, then validation](#-coffee-then-validation)
- [The answer back to the client](#the-answer-back-to-the-client)
- [The reusable checklist](#the-reusable-checklist)
- [References](#references)

---

## The ask

Tuesday, 09:12. An email from the head of research computing at a university we'll call **Delta**:

> *"Hi, we keep losing GPU jobs. Researchers say training runs hang at startup on some nodes, mostly after maintenance, and every few weeks a batch of CPU jobs dies with I/O errors. A colleague told us we need 'NHC'. Can you build us an NHC for our cluster? We run Slurm. How fast can you do it?"*

It's tempting to reply with a link to [part 3](/fields/system-administration/node-health-check/writing-nhc-conf.md) and a sample config. Don't. "Build us an NHC" is a solution the client picked. Our job is to find the problem first.

---

## The ten minutes before you reply

Before typing a word, think through what you know and what you don't. Here's what those ten minutes look like on paper.

**1. Read the symptoms like a detective.**

| Symptom from the email | Plausible causes | What would detect it |
|---|---|---|
| GPU jobs "hang at startup" on some nodes | NVSwitch fabric not initialized (a known cause of CUDA error 802 on DGX/HGX), a GPU missing, an IB rail down so NCCL stalls | GPU count, fabric state, per-HCA link checks |
| "Mostly after maintenance" | Services not started after reboot, nodes returning to the pool before they're ready | Boot-time checks; NHC keeping rebooted nodes drained until checks pass ([part 4](/fields/system-administration/node-health-check/slurm-integration.md#boot-and-reboot-the-sneaky-part)) |
| CPU jobs die with I/O errors, in batches | Lustre client evictions or a dropped mount on a subset of nodes: the classic black hole ([part 1](/fields/system-administration/node-health-check/why-node-health-check.md)) | Mount checks with type and source |
| "Some nodes" | Heterogeneous hardware, or drift between identical nodes | Per-class expectations ([part 9](/fields/system-administration/node-health-check/architecture-driven-nhc.md)) |

**2. List what you don't know but must.** Hardware classes and counts. Slurm version and current health-check settings. Who drains nodes today, and how. What tools already exist (NVSM, DCGM, monitoring). Operating systems. How they deploy config. How much automatic draining they'll tolerate. Who gets paged.

**3. Name the risks of getting it wrong.** A bad config drains the whole cluster ([part 5](/fields/system-administration/node-health-check/rollout-at-scale.md)). Two tools both draining nodes fight each other. Expensive checks on GPU nodes slow training. Auto-fixes that hide hardware faults void the evidence the vendor will ask for.

**4. Decide what to send back now.** Not a solution: a short reply that shows you understood, sets expectations, and asks for a discovery call plus a small data bundle.

The reply, sent at 09:25:

> *"Thanks. What you're describing (hangs after maintenance, batches of I/O failures) is exactly what node health checking is good at, so NHC is a reasonable direction. Before proposing anything, I'd like a 45-minute call and a few command outputs from one node of each type (list attached). That lets me propose checks that match your hardware instead of a generic template. Expect a written proposal within two working days of the call."*

---

## Discovery: the questions, and why each one matters

A question you can't connect to a decision is a question you shouldn't ask. Each one below states the decision it drives.

**Problem and expectations**

| Question | Why it matters |
|---|---|
| What fails, how often, and since when? Any ticket numbers or job IDs? | Gives a baseline, so we can later prove the fix worked |
| What does "done" look like for you? | Becomes the acceptance criteria |
| How many false drains per week would be acceptable? | Sets how strict thresholds can be |

**Scheduler and node state**

| Question | Why it matters |
|---|---|
| Slurm version? Current `HealthCheck*` settings? | Which `HealthCheckNodeState` values exist; whether anything runs today |
| Who drains nodes today, and do they always set a reason? | The `NHC:` ownership contract ([part 1](/fields/system-administration/node-health-check/why-node-health-check.md#the-nhc-handshake)) only works if humans use reasons |
| Do you reboot nodes with `scontrol reboot`? `ASAP`? | Decides whether NHC 1.5's reboot handling matters, and how remediation must call it ([part 7](/fields/system-administration/node-health-check/auto-remediation.md#rungs-1-2-the-node-doctor)) |
| Existing Prolog/Epilog scripts? | Job-boundary checks must fit around them |

**Hardware and OS**

| Question | Why it matters |
|---|---|
| Every node type: model, CPUs, RAM, GPUs, HCAs, local disks | One class per distinct build |
| BIOS settings that matter: SMT, NUMA per socket (NPS) | Thread and NUMA checks must expect the configured values, not the maximum |
| OS and version per node type | Packaging (RPM vs source), sysconfig path, helper paths |
| Any nodes out for repair right now? | Exclude them from classes instead of drowning the first rollout in known failures |

**Fabric and storage**

| Question | Why it matters |
|---|---|
| Which HCAs carry compute traffic vs storage, and at what rate? | IB checks per compute HCA; don't IB-check Ethernet ports |
| Shared filesystems: mount points, types, servers | Mount checks with type and source; avoid `df` on network mounts |
| Local scratch on nodes? | Its own mount check |

**GPUs**

| Question | Why it matters |
|---|---|
| NVSwitch systems (DGX/HGX)? How is Fabric Manager run? | Fabric checks become mandatory |
| Driver and DCGM versions | Check commands and output formats |
| Which Xid errors have you seen? | Calibrates the drain list against real history |

**Existing tooling and operations**

| Question | Why it matters |
|---|---|
| What else monitors or acts on node health (NVSM, BCM, DCGM exporter, custom scripts)? | Avoids two tools fighting over node state |
| How is config deployed (Ansible, xCAT, image)? Is it in Git? | Delivery path and rollback |
| Is there a test node or partition we can use? | Canary rollout ([part 5](/fields/system-administration/node-health-check/rollout-at-scale.md#phase-3-canary-enforcing-on-a-few-nodes)) |
| Who acts on a drained node, and how fast? | Decides how much auto-remediation is worth building |
| Change windows, approvals? | Timeline |

**The data bundle we asked for** (one node of each type, run as root):

```bash
sinfo -R; scontrol show config | grep -i healthcheck; grep -i '^NodeName' /etc/slurm/slurm.conf
lscpu | grep -E 'Socket|Core|Thread|NUMA node\(s\)'; free -g
ibdev2netdev; ibstat | grep -E 'CA |Rate|State|Link layer'
findmnt -t nfs,nfs4,lustre,ext4,xfs
nvidia-smi -L; nvidia-smi --query-gpu=fabric.state,fabric.status --format=csv,noheader
systemctl is-active nvidia-fabricmanager nvsm munge slurmd
dmesg -T | grep -i 'NVRM: Xid' | tail -20
```

---

## What discovery told us

The call and the data bundle gave us this picture of **Delta**:

| Item | Value | Source |
|---|---|---|
| GPU nodes | 16 × **NVIDIA DGX H100** (`dgx[01-16]`) | Client |
| ... per node | 8 × H100 80 GB, 4 × NVSwitch; 2 × Xeon Platinum 8480C (56 cores each, 112 total); 2 TB RAM | [NVIDIA DGX H100 User Guide](https://docs.nvidia.com/dgx/dgxh100-user-guide/introduction-to-dgxh100.html) |
| ... threads | 224 (HT enabled) | Client's `lscpu` |
| ... compute fabric | 8 × single-port ConnectX-7, NDR 400 Gb/s IB, on 4 OSFP ports: RDMA devices `mlx5_0,3,4,5,6,9,10,11` | DGX H100 User Guide, Tables 5-6 |
| ... storage/in-band | 2 × dual-port ConnectX-7 (`mlx5_1,2,7,8`), **Ethernet by default** | DGX H100 User Guide, Table 1 and 5 |
| ... local storage | 8 × 3.84 TB NVMe U.2 in RAID 0 as data cache | DGX H100 User Guide |
| ... cache mount | `/raid`, ext4 on `/dev/md*` | Client's `findmnt` on `dgx01` |
| ... OS | DGX OS (Ubuntu-based), ships **NVSM** and **DCGM** | DGX H100 User Guide, "DGX OS Software" |
| CPU nodes | 120 × dual **AMD EPYC 9654** (`cpu[001-120]`): 96 cores / 192 threads each, 12 DDR5 channels per socket | [AMD EPYC 9654 product page](https://www.amd.com/en/support/downloads/drivers.html/processors/epyc/epyc-9004-series/amd-epyc-9654.html) |
| ... per node | 768 GB (24 × 32 GB, one DIMM per channel), BIOS default **NPS1** = 2 NUMA nodes per node; HDR 200 IB (`mlx5_0`); Rocky Linux 9 | Client; NPS options per [SPEC CPU2017 Genoa platform flags](https://spec.cs.miami.edu/cpu2017/flags/Fujitsu-Platform-Settings-V1.0-Genoa-RevC.html) |
| Login nodes | 2 (`login[01-02]`), not Slurm compute nodes | Client |
| Storage | NFS `/home` from `nfs01`; Lustre `/lustre/scratch` over o2ib | Client |
| Scheduler | Slurm 24.11, **no health check configured**; `scontrol reboot` used during maintenance | Client |
| Config management | xCAT images + Ansible, config in Git | Client |
| Operations | 2 admins, business hours; nobody watches drains at night | Client |
| Historical Xids | 79 (twice), 94, 13 and 31 (many) | Client's `dmesg` |
| Drains today | Manual, often without a reason | `sinfo -R` showed 5 nodes drained with empty reasons |

Two things in the bundle jumped out immediately:

1. `nvidia-smi --query-gpu=fabric.state,fabric.status` on one DGX returned `In Progress, N/A` for every GPU, while `systemctl is-active nvidia-fabricmanager` said `active`. **That node was the hang**: CUDA can't initialize until the NVSwitch fabric is formed, even though the Fabric Manager process is up. NVIDIA's troubleshooting docs list fabric state as the thing to check for CUDA error 802 on NVSwitch systems.
2. Five nodes drained with **empty reasons**. Nobody remembered why. NHC will leave those alone, and someone needs to triage them before rollout.

---

## The first proposal

Drafted right after the call (call it version 0.1):

- **NHC 1.5** on all nodes, run by `slurmd` every 300 s, `HealthCheckNodeState=ANY,CYCLE`.
- **Configs generated** from one architecture definition ([part 9](/fields/system-administration/node-health-check/architecture-driven-nhc.md)), with three contexts: periodic, epilog, deep.
- **Per class:** mounts, CPU/NUMA/memory, IB per HCA, services, rogue-process logging; on DGX also GPU count, GPU model, Xid scan, DCGM level 2 in the deep context only.
- **Rollout:** dry run, canary on 2 DGX + 8 CPU nodes, enforce behind a circuit breaker ([part 5](/fields/system-administration/node-health-check/rollout-at-scale.md)).
- **Remediation (phase 2):** node doctor reboots for a short list of failures, max 2 per day per node ([part 7](/fields/system-administration/node-health-check/auto-remediation.md)).

It looks complete. It isn't.

---

## ☕ Coffee, then validation

Coffee isn't a joke step. Stepping away is how you stop reviewing your own draft as its author. Back at the desk, the rule is: **every claim in the proposal gets checked against a primary source or a test run.** Here's what that pass found.

| # | Draft assumption | What validation showed | Change |
|---|---|---|---|
| 1 | DGX compute HCAs are `mlx5_0`…`mlx5_7` | NVIDIA's port table: compute ports are `mlx5_0,3,4,5,6,9,10,11`; `1,2,7,8` are the storage cards, Ethernet by default | IB checks on the 8 real compute HCAs only. A naive config would fail on every DGX, every run |
| 2 | "Fabric Manager running" = GPUs usable | The client's own data showed FM `active` with fabric `In Progress`. Process liveness isn't fabric health | New check `check_arch_gpu_fabric`: every GPU must report `Completed, Success`. FM service check kept, with `-S` to restart it |
| 3 | Drain on Xid 48, 79, 94, 95, 119 | NVIDIA's GPU debug guidelines: **94** (contained ECC) needs only the affected application restarted; **92** is informational; **64** and **95** need a reboot. Google Cloud's GPU troubleshooting guide: stop workloads and reset GPUs on **74** (NVLink) and **119** (GSP timeout) | Drain list becomes 48, 64, 74, 79, 95, 119, 120. Xid 94 goes to monitoring, not drains. (The client's Xid 13/31 history is application-side and correctly ignored) |
| 4 | `slurm.conf` matches hardware | The generator's cross-check failed on the first run (output below): `slurm.conf` says 1 thread per core on EPYC nodes; the hardware has SMT on | Question for the client: intended or not? Must be resolved before rollout |
| 5 | One package for everyone | DGX OS is Ubuntu-based; CPU nodes are Rocky 9 | RPM for Rocky; build from the release tarball for DGX OS, with `/etc/default/nhc` as its sysconfig path ([part 2](/fields/system-administration/node-health-check/build-and-install.md)) |
| 6 | DCGM level 2 in the deep context is fine anywhere | Level 2 runs about two minutes and loads the GPUs; Slurm kills the health check at 60 s | Confirmed: deep context only, never periodic, with its own `TIMEOUT=900` |
| 7 | NHC is the only health tool | DGX OS ships NVSM, which does its own health monitoring and alerting | Ownership rule: NVSM and DCGM *alert*, only NHC *drains*. Written into the runbook |
| 8 | Login nodes are like compute nodes | They're not Slurm nodes, so the cross-check would flag them as missing from `slurm.conf` | Marked `in_slurm: false`; no hygiene checks on login nodes |
| 9 | `/raid` is ext4 on `/dev/md*` | That's what the client's `findmnt` showed on `dgx01` | Kept, but verified on all 16 DGX during the dry run before enforcing |

Findings 2 and 8 needed new capabilities in the series' tools: a `service_map` and `extra_services` in the YAML for Fabric Manager, the `check_arch_gpu_fabric` module check, `in_slurm: false`, and a harness that accepts a client's expectations. They're now part of [`nhc_gen.py`](/fields/system-administration/node-health-check/nhc_gen.py), [`acme_arch.nhc`](/fields/system-administration/node-health-check/acme_arch.nhc) and [`nhc_test_harness.sh`](/fields/system-administration/node-health-check/nhc_test_harness.sh).

**Finding 4, as the generator reported it.** The node lines from the client's `slurm.conf`:

```ini
NodeName=cpu[001-120] Sockets=2 CoresPerSocket=96 ThreadsPerCore=1 RealMemory=750000
NodeName=dgx[01-16] Sockets=2 CoresPerSocket=56 ThreadsPerCore=2 RealMemory=2000000 Gres=gpu:h100:8
```

The cross-check:

```text
$ python3 nhc_gen.py case-study-delta-cluster.yaml --out build --slurm-conf client-slurm.conf --strict
ERROR:   class 'cpu-genoa' vs slurm.conf (cpu001 and others): slurm says 2/192/192 sockets/cores/threads, architecture says 2/192/384
Nothing written.
```

The client checked `lscpu` on `cpu001`: 2 threads per core. They chose to fix `slurm.conf` (`ThreadsPerCore=2`, saved as `client-slurm-fixed.conf`) and use `--hint=nomultithread` where jobs need full cores. After that:

```text
$ python3 nhc_gen.py case-study-delta-cluster.yaml --out build --slurm-conf client-slurm-fixed.conf --strict
OK: 138 nodes in 3 classes -> nhc.conf, nhc-epilog.conf, nhc-deep.conf in build/
```

**The generated DGX block** (periodic context, target `{dgx[01-16]}` omitted):

```bash
check_fs_mount_rw -t nfs -s 'nfs01:/export/home' -f /home
check_fs_mount_rw -t lustre -s '*@o2ib*:/scratch' -f /lustre/scratch
check_fs_mount_rw -t ext4 -s '/dev/md*' -f /raid
check_arch_gpu_count 8
check_arch_gpu_fabric
check_cmd_dmesg -m '!/NVRM: Xid [(]PCI:[^)]*[)]: (48|64|74|79|95|119|120),/' -M 'Fatal GPU Xid in kernel log'
check_ps_service -u root -d sshd -S sshd
check_ps_service -u munge -d munged -S munge
check_ps_service -u root -d nv-fabricmanager -S nvidia-fabricmanager
check_hw_cpuinfo 2 112 224
check_arch_numa_nodes 2
check_hw_physmem 2TB 2TB 3%
check_hw_ib 400 mlx5_0
check_hw_ib 400 mlx5_3
check_hw_ib 400 mlx5_4
check_hw_ib 400 mlx5_5
check_hw_ib 400 mlx5_6
check_hw_ib 400 mlx5_9
check_hw_ib 400 mlx5_10
check_hw_ib 400 mlx5_11
check_arch_gpu_model 'H100'
check_ps_unauth_users log syslog
check_ps_userproc_lineage log syslog
```

**The test run**, real NHC 1.5 with fake GPUs and kernel logs ([part 9](/fields/system-administration/node-health-check/architecture-driven-nhc.md#step-4-prove-it-with-real-nhc-before-it-ships)):

```text
$ CI=true EXPECTED_FILE=case-study-delta-expected.txt GPU_HOST=dgx05 ./nhc_test_harness.sh build
ok   - cpu007 nhc: 14 checks
ok   - dgx05 nhc: 27 checks
ok   - login01 nhc: 11 checks
ok   - mgmt01 nhc: 4 checks
ok   - dgx05 nhc-epilog: 9 checks
ok   - cpu007 nhc-epilog: 5 checks
ok   - dgx05 nhc-deep: 28 checks
ok   - GPU count passes with 8 GPUs
ok   - GPU count fails with one GPU missing
ok   - Xid check fails on fatal Xid 79
ok   - Xid check passes on benign Xid 13
ok   - fabric check passes when every GPU is Completed, Success
ok   - fabric check fails while Fabric Manager is not done
# 13 passed, 0 failed
```

The fabric test reproduces the client's hang: with every GPU at `In Progress, N/A`, NHC reports `check_arch_gpu_fabric: GPU 0 fabric is 'In Progress, N/A' (Fabric Manager not ready or fabric degraded)`, which in production becomes the node's `NHC:` drain reason. That's the symptom from the original email, caught before a job lands.

---

## The answer back to the client

Thursday, 16:40, two working days after the call as promised. The proposal, as sent:

> ### Delta Research Computing: Node Health Check proposal (v1.0)
>
> **Summary.** Your GPU job hangs match a known NVSwitch failure mode: on at least one DGX, the GPU fabric wasn't initialized although Fabric Manager was running, and CUDA can't start in that state. Your batches of CPU I/O failures match nodes that keep accepting jobs after losing a filesystem. We propose LBNL NHC 1.5, configured from a single description of your cluster, to take such nodes out of service automatically with a readable reason, and to return them once healthy.
>
> **What gets checked**
>
> | Node type | Every 5 minutes (staggered) | After every job | On demand / after repairs |
> |---|---|---|---|
> | DGX H100 ×16 | Mounts (`/home`, `/lustre/scratch`, `/raid`), 8 GPUs present, NVSwitch fabric ready, fatal GPU errors, Fabric Manager/munge/sshd running (auto-restart), CPU, NUMA, memory, 8 × NDR links at 400 Gb/s, GPU model | Mounts, GPUs, fabric, fatal GPU errors | Everything, plus DCGM diagnostics level 2 |
> | EPYC ×120 | Mounts, services, CPU (SMT on), NUMA (NPS1), memory, HDR link | Mounts | Everything |
> | Login ×2 | Mounts, services, CPU, memory, HDR link (alerts only) | — | — |
>
> **What changes in Slurm.** Three `slurm.conf` lines (`HealthCheckProgram`, `HealthCheckInterval=300`, `HealthCheckNodeState=ANY,CYCLE`), a short epilog, and `ThreadsPerCore=2` for the EPYC nodes (already agreed).
>
> **How we roll it out** (no node is drained by NHC until week 3)
>
> | Week | Step | Exit criterion |
> |---|---|---|
> | 1 | Install, dry run on all nodes, triage every finding with you | Every failure explained: config fixed or node fixed |
> | 2 | Canary: NHC may drain only `dgx[01-02]` and `cpu[001-008]` | 5 working days, zero false drains |
> | 3 | Enforce everywhere, with an alert if more than 5% of nodes are NHC-drained | You sign off |
> | 4-5 | Optional phase 2: automatic reboot for a short list of GPU and service failures, max 2 per node per day, then escalation to you | Agreed list, dry-run log reviewed |
>
> **How you'll know it worked.** Baseline from your last 60 days: GPU jobs failing in the first 5 minutes, CPU jobs failing on I/O, hours that drained nodes sit unexplained. We report the same numbers 30 days after week 3.
>
> **New rules for your team** (one-page runbook included): always drain with a reason; reasons starting with `NHC:` belong to NHC; NVSM and DCGM alert, only NHC drains; change node expectations only through the cluster description in Git, which is tested automatically before deployment.
>
> **What we need from you.** Root access to one node per type and to the Slurm controller; a 30-minute slot to apply `slurm.conf` changes; a decision on the 5 nodes currently drained without a reason.
>
> **Deliverables.** Cluster description, generated configs, check module, test harness and CI pipeline, all in your Git repository; packages for Rocky 9 and DGX OS; runbook; a handover session.
>
> **Out of scope.** Multi-node performance validation (NCCL/MPI benchmarks across nodes), which we recommend as a follow-up: a node can pass every check and still slow a 16-node job.
>
> **Open questions.** (1) Confirm `/raid` is ext4 on all 16 DGX (verified on `dgx01` only). (2) Who should be emailed for escalations in phase 2?

Notice what the answer does *not* contain: NHC syntax, bash, or the word "match string". The client asked for an outcome. The technical depth lives in the deliverables and the runbook.

---

## The reusable checklist

For the next "build us an NHC" email:

1. **Before replying:** map each symptom to plausible causes and to what would detect it. Reply with understanding, a discovery call and a data bundle, not a config.
2. **Discovery:** problem and success criteria; scheduler version, drain habits, reboot habits; every hardware class, with BIOS settings; OS per class; compute vs storage HCAs; mounts; GPU platform (NVSwitch?), driver, Xid history; other health tools; deployment method; test nodes; who acts on drains.
3. **Ask for data, not descriptions:** `sinfo -R`, `slurm.conf` node lines, `lscpu`, `ibdev2netdev`, `findmnt`, `nvidia-smi` fabric state, `dmesg` Xids. Clients describe the cluster they designed; commands show the cluster they have.
4. **First proposal:** classes and contexts, Slurm settings, rollout phases, remediation as a separate phase.
5. **Validate every assumption** against vendor documentation and a real test run: device names, service names, what "healthy" looks like, error policies, timeouts, OS differences, overlapping tools. Expect the proposal to change. Ours changed in 9 places.
6. **Answer in the client's language:** what was wrong, what gets checked, what changes, how it rolls out, how success is measured, what you need from them, what's out of scope.

> **Takeaway:** "build us an NHC" is the client's chosen solution, not their problem. Ten minutes of thinking turns it into the right questions; data beats descriptions; and a coffee-separated validation pass, against vendor docs and real test runs, is what turns a plausible proposal into one that works on their hardware.

---

## References

**Hardware**
- [NVIDIA DGX H100/H200 User Guide: Introduction (components, network port mapping, DGX OS software)](https://docs.nvidia.com/dgx/dgxh100-user-guide/introduction-to-dgxh100.html)
- [AMD EPYC 9654 product specifications](https://www.amd.com/en/support/downloads/drivers.html/processors/epyc/epyc-9004-series/amd-epyc-9654.html)
- [SPEC CPU2017 platform settings for AMD Genoa: NUMA nodes per socket (NPS) options](https://spec.cs.miami.edu/cpu2017/flags/Fujitsu-Platform-Settings-V1.0-Genoa-RevC.html)

**GPU health**
- [NVIDIA GPU Debug Guidelines: common Xid errors and recommended actions](https://docs.nvidia.com/deploy/gpu-debug-guidelines/index.html)
- [Google Cloud: troubleshooting GPU VMs, Xid actions](https://docs.cloud.google.com/compute/docs/troubleshooting/troubleshooting-gpus)
- [NVIDIA Xid Errors catalogue (PDF)](https://docs.nvidia.com/deploy/pdf/XID_Errors.pdf)
- [NVIDIA NIM troubleshooting: CUDA error 802 and Fabric Manager](https://docs.nvidia.com/nim/large-language-models/latest/troubleshooting/cuda-driver.html)
- [NVIDIA NVSentinel issue #883: `fabric.state` / `fabric.status` query fields and degraded-fabric examples](https://github.com/NVIDIA/NVSentinel/issues/883)
- [DigitalOcean: diagnosing "system not yet initialized" via fabric state](https://docs.digitalocean.com/support/how-do-i-fix-a-system-not-initialized-error-on-multi-gpu-droplets/)
- [NVIDIA DCGM diagnostics: run levels and durations](https://docs.nvidia.com/datacenter/dcgm/latest/user-guide/dcgm-diagnostics.html)

**Scheduler and NHC**
- [`slurm.conf`: HealthCheckProgram, HealthCheckNodeState, node configuration](https://slurm.schedmd.com/slurm.conf.html)
- [LBNL NHC on GitHub](https://github.com/mej/nhc) and [1.5 release notes](https://github.com/mej/nhc/releases/tag/1.5)
