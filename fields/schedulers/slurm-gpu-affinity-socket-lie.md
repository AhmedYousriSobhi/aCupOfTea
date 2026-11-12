---
id: slurm-gpu-affinity-socket-lie
title: "Your GPU Has Core Affinity. Slurm Has Socket Affinity. They Are Not Speaking."
order: 5
sidebar_label: GPU affinity and the socket lie
summary: gres.conf Cores= schedules per socket, not core. Fix topology via l3cache_as_socket or numa_node_as_socket. Also covers four 1-GPU schemes and how MIG, MPS, and sharding isolate workloads.
level: advanced
type: concept
domains:
  - systems-and-hpc
tags:
  - slurm
  - hpc
  - gpu
relations:
  related:
    - slurm-cgroups-in-practice
    - slurm-kill-task-failed
---

# Your GPU Has Core Affinity. Slurm Has Socket Affinity. They Are Not Speaking.

> **Part of the [schedulers](/fields/schedulers/slurm-intro.md) directory**, and the missing neighbor of the [mixed-GPU series](/fields/schedulers/slurm-mixed-gpus/README.md): that series is about *which* GPUs a job gets, this page is about *where* they sit. Everything below comes from SchedMD's GRES documentation for Slurm 26.05 and the `gres.conf` man page. None of it was run on a live cluster for this page.

## Table of Contents

- [Your GPU Has Core Affinity. Slurm Has Socket Affinity. They Are Not Speaking.](#your-gpu-has-core-affinity-slurm-has-socket-affinity-they-are-not-speaking)
  - [Table of Contents](#table-of-contents)
  - [The comforting misconception](#the-comforting-misconception)
  - [What the docs actually say](#what-the-docs-actually-say)
  - [Making Slurm's sockets match the hardware](#making-slurms-sockets-match-the-hardware)
  - [One GPU, four names](#one-gpu-four-names)
  - [AutoDetect: nvml, nvidia, and what each can see](#autodetect-nvml-nvidia-and-what-each-can-see)
  - [The library that will not let go](#the-library-that-will-not-let-go)
  - [Sharing a GPU: MIG, MPS, shards](#sharing-a-gpu-mig-mps-shards)
  - [Steps want all your GPUs by default](#steps-want-all-your-gpus-by-default)
  - [A debugging routine for a bad GPU node](#a-debugging-routine-for-a-bad-gpu-node)
  - [References](#references)

* * *

## The comforting misconception

An admin writes this in `gres.conf`:

```
Name=gpu File=/dev/nvidia0 Cores=0-15
Name=gpu File=/dev/nvidia1 Cores=16-31
```

It reads like a promise: GPU 0 gets cores 0 to 15, GPU 1 gets cores 16 to 31, and Slurm will keep jobs on matching pairs. It is a lovely picture of NUMA-aware scheduling.

SchedMD's GRES documentation has a polite name for what happens next. It calls it a **common misconception**.

* * *

## What the docs actually say

The GRES guide puts it plainly: Slurm handles GRES affinity on a **socket** basis internally. The `Cores` field in `gres.conf` creates the impression that core-level affinity is respected during scheduling, "which it does not and never has". The `gres.conf` man page says the same thing from the other side: Slurm can track resources at the CPU or thread level, but the scheduling algorithms that co-allocate GRES with CPUs operate at socket level.

The practical trouble shows up with **job steps**. Jobs are placed by socket, steps look at cores, and the two views can disagree. To stop admins from writing affinity that Slurm cannot honor, Slurm now checks that any `Cores` value lines up with socket boundaries, and it complains if it does not:

```
error: _check_core_range_matches_sock: gres/gpu GRES autodetected core affinity 0-7
on node node0 doesn't match socket boundaries. (Socket 0 is cores 0-1)
```

That message turns up on modern CPUs with many cache domains. The GPU driver reports an affinity based on the real hardware topology, Slurm believes the node has two big sockets, and the two descriptions do not nest.

What `--gres-flags` changes, per the man page:

| Flag on the job | Effect |
|---|---|
| *(none)* | The cores listed for a GPU are **preferred**, not required |
| `--gres-flags=enforce-binding` | Only the listed cores may be allocated with that GPU. Better performance, possibly longer queue time |
| `--gres-flags=disable-binding` | Any core may be used. Faster scheduling, possibly worse application performance. Needed if a job wants more CPUs than are bound to a GPU |

So the setting is real, but it operates inside Slurm's socket-shaped view of the node, not on the physical layout you drew on the whiteboard.

* * *

## Making Slurm's sockets match the hardware

The documented fix is to change what Slurm believes a "socket" is, so that it matches the GPU affinity boundaries. Two topology parameters do this: `l3cache_as_socket` and `numa_node_as_socket`. Test first, change second:

```bash
# what does the hardware look like to Slurm right now?
slurmd -C

# what would it look like with a different socket definition?
slurmd -C --parameters=l3cache_as_socket

# which grouping matches the GPUs? compare with the driver's view
nvidia-smi topo -m
```

If one of the options lines the socket count and cores per socket up with the GPU affinity you see in `nvidia-smi topo -m`, make it permanent. Per node is the recommended form when only some nodes need it:

```
# slurm.conf, per node
NodeName=node0 CPUs=32 Boards=1 SocketsPerBoard=8 CoresPerSocket=2 ThreadsPerCore=2 Parameters=l3cache_as_socket Gres=gpu:a100:2

# or globally
SlurmdParameters=l3cache_as_socket
```

Then let `AutoDetect=nvml` in `gres.conf` pick up the affinity. The socket count may now differ from the number of physical sockets on the board. That is expected and not a bug.

The manual alternative is to turn AutoDetect off for that node and write `Cores=` yourself, still aligned to socket boundaries or it gets rejected:

```
NodeName=node0 Autodetect=off Name=gpu Type=a100 File=/dev/nvidia0 Cores=0-15
NodeName=node0 Autodetect=off Name=gpu Type=a100 File=/dev/nvidia1 Cores=16-31
```

> [!WARNING]
> `Cores` in `gres.conf` uses Slurm's **logical** core index, not the physical one. A mismatch between the two is a quiet way to build a topology that validates and is still wrong.

* * *

## One GPU, four names

The GRES guide spends a surprising number of lines on numbering, and for good reason. The same physical GPU can be known by four different numbers.

| Where | How it is numbered |
|---|---|
| `nvidia-smi` (NVML) | By PCI bus ID, lowest to highest |
| CUDA | Not necessarily the same, unless `CUDA_DEVICE_ORDER=PCI_BUS_ID` is set |
| `/dev/nvidiaN` | By Linux minor number. The mapping to NVML numbers is, in the docs' words, nondeterministic and system dependent, and can change between boots after hardware or OS changes |
| Inside a job with device cgroups | Renumbered from 0, whatever the physical device was |

That last row has a consequence that trips up site scripts. If a job is allocated `/dev/nvidia1` and devices are constrained by cgroup (see the [cgroups page](/fields/schedulers/slurm-cgroups-in-practice.md)), the job sees `CUDA_VISIBLE_DEVICES=0`. The Prolog and Epilog, which run **outside** any cgroup, see `CUDA_VISIBLE_DEVICES=1`. An epilog that cleans up "the GPU the job used" by reading its own environment has to translate between the two.

Two housekeeping rules from the docs: list `File=` entries in increasing numeric order, and do an after-boot check that each device file still belongs to the GPU you think it does. The docs describe the assignment as "fairly stable", which is a phrase worth remembering at 3 a.m.

* * *

## AutoDetect: nvml, nvidia, and what each can see

| Setting | Needs the NVML library? | Detects MIG and NVLink? |
|---|---|---|
| `AutoDetect=nvml` | Yes | Yes |
| `AutoDetect=nvidia` (added in 24.11) | No | **No** |

Other values exist for AMD (`rsmi`), Intel (`oneapi`) and `nrt`. With AutoDetect on, you still need the `Gres=` line in `slurm.conf` so `slurmctld` knows how many to expect. And counts are enforced: a node that finds **fewer** resources than configured is drained, and a node whose detected GPUs are not all covered by the config is drained too.

`Type` matching has a charming quirk. It must equal, or be a substring of, the name the hardware reports with spaces turned into underscores. So `geforce_rtx_2060` can be written as `geforce`, `rtx`, `2060` or the whole thing. Two commands show you what Slurm sees:

```bash
slurmd -C    # detected hardware and Gres line
slurmd -G    # the gres setup as configured, including autodetected devices being ignored
```

If `gres.conf` specifies `Type` and `File` that match a real GPU, any `Cores` or `Links` you added become a **sanity check** against the detected values. A GPU that disagrees with its configuration is omitted from the node with an error. That is useful, because it turns a silent hardware change into a loud one.

* * *

## The library that will not let go

Here is an interaction that few people see until it bites. With `AutoDetect=nvml` or `rsmi`, `slurmstepd` loads the management library and **holds it open** to account for GPU use in any step that asked for a GPU. `slurmd` does the same if `AcctGatherEnergyType=acct_gather_energy/gpu` is set. The docs state the consequence directly: while a process holds the library open, no other process can configure the GPU.

That matters if your Prolog tries to change GPU settings (persistence mode, clocks and similar). The documented escape hatches:

- Do not set `AcctGatherEnergyType=acct_gather_energy/gpu` if a Prolog needs to configure GPUs.
- If jobs share GPUs on the node, you may also need `JobAcctGatherParams=DisableGPUAcct`.

The library is also held when a job requests `--gpu-freq`.

On the plus side, with `AccountingStorageTRES=gres/gpu` and `AutoDetect=nvml`, Slurm gathers `gres/gpumem` and `gres/gpuutil` per step, and `sacct` shows them in the `TRESUsageIn*` fields. For once the accounting has a view of GPU *utilization*, not just allocation. MIG devices are the exception, because NVML does not provide utilization metrics for them.

* * *

## Sharing a GPU: MIG, MPS, shards

Three ways to put more than one job on a GPU, with very different guarantees.

| Mechanism | What it gives you | The catch, per the docs |
|---|---|---|
| **MIG** | Hardware-isolated GPU instances (up to seven on an A100), each treated as a GPU with cgroup isolation and task binding | Partitions must already exist, because Slurm does not do dynamic MIG partitioning. No `gpumem`/`gpuutil` accounting for MIG |
| **MPS** | Several jobs sharing a GPU, each given a percentage | A request must fit on one GPU. A job cannot request both `gpu` and `mps`. Only one user can have an active MPS server on a system, so different users are **time-sliced**, not truly concurrent |
| **Shards** | A generic way to let several jobs share a GPU | Does **not** fence the processes on the GPU. Works best with homogeneous workloads |

A few notes that save debugging time:

- A MIG `Type` must be a substring of the "MIG Profile" string in the `slurmd` log at `debug2` level, for example `nvidia_a100_3g.20gb`.
- MPS needs a Prolog to start and stop the MPS servers. A sample ships in `etc/prolog.example` in the Slurm distribution.
- `Count` for MPS is translated to a percentage, so it is normally a multiple of 100.
- The same GPU can be allocated as `gpu` or as `mps`/`shard`, never both at once.
- Shards and MPS both require the `select/cons_tres` plugin.

* * *

## Steps want all your GPUs by default

A job allocation is one thing and a job step is another. By default a step is given **all** the GRES the job requested, except those implicitly requested by an exclusive job. SchedMD's explanation is that granting less by default would force steps that need no GPU to say so explicitly.

The consequence shows up when you launch parallel steps inside one allocation. The docs' own example is a batch script that starts several `srun` steps in the background, each asking for its own count:

```bash
#SBATCH --gres=gpu:4 -n4 -N1-1
srun --gres=gpu:2 -n2 --exclusive show_device.sh &
srun --gres=gpu:1 -n1 --exclusive show_device.sh &
srun --gres=gpu:1 -n1 --exclusive show_device.sh &
wait
```

Leave the `--gres` off and each step claims everything. Also note the typing rule: a job requested as `gpu:2` cannot start a step requesting `gpu:tesla:2`, and the reverse holds too. Typed and untyped requests must be consistent within a job.

* * *

## A debugging routine for a bad GPU node

```bash
# 1. What does Slurm think the node is?
slurmd -C
slurmd -G

# 2. What does the hardware say about affinity and links?
nvidia-smi topo -m

# 3. Would a different socket definition line them up?
slurmd -C --parameters=l3cache_as_socket     # or numa_node_as_socket

# 4. Why is the node drained?
sinfo -R
scontrol show node <node> | grep -i reason

# 5. Inside a job: which GPU numbers does it actually see?
srun --gres=gpu:1 bash -c 'echo $CUDA_VISIBLE_DEVICES; nvidia-smi -L'
```

Remember step 5 gives numbers from inside the job's own view, which may not match what an epilog or monitoring agent sees.

| Symptom | First suspect |
|---|---|
| `doesn't match socket boundaries` error at start | Autodetected GPU affinity does not nest in Slurm's socket layout |
| Node drained with fewer GRES than configured | A GPU fell off the bus, or `Gres=` in `slurm.conf` says more than the node has |
| Prolog cannot change GPU settings | A process (often `slurmstepd` or `slurmd`) holds the management library open |
| Two parallel `srun` steps fight over the same GPUs | Steps default to all the job's GRES |
| Scripts disagree about which GPU is "1" | Four numbering schemes; check `CUDA_DEVICE_ORDER` and cgroup renumbering |

* * *

## References

- [Slurm: Generic Resource (GRES) Scheduling](https://slurm.schedmd.com/gres.html)
- [Slurm: gres.conf man page](https://slurm.schedmd.com/gres.conf.html)
- [Slurm: Prolog and Epilog Guide](https://slurm.schedmd.com/prolog_epilog.html)
- [NVIDIA: MIG User Guide](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/index.html)
- [NVIDIA: MPS documentation](https://docs.nvidia.com/deploy/mps/index.html)