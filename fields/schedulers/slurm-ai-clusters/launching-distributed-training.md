---
id: slurm-distributed-training
title: "Launching Distributed Training on Slurm: srun, torchrun, and the Rank Contract"
sidebar_label: "2. Launching distributed training"
order: 2
summary: Why a 2-node training job can run on one node, the environment PyTorch needs from Slurm, launching with srun or torchrun, and the double-launch trap - tested with PyTorch 2.15 on Slurm 23.11.
level: intermediate
type: [concept, guide]
domains: [systems-and-hpc, deep-learning]
tags: [slurm, hpc, distributed-training, pytorch]
relations:
  prerequisites: [slurm-topology-placement]
  related: [slurm-containers-pyxis, slurm-job-script-tale]
---

# Launching Distributed Training on Slurm: srun, torchrun, and the Rank Contract

> **Part 2 of [Slurm for AI Clusters](/fields/schedulers/slurm-ai-clusters/README.md)** [Part 1](/fields/schedulers/slurm-ai-clusters/topology-aware-placement.md) got the job good nodes. This page gets a process started on each of them with the right rank. By the end you'll have two working launch scripts, and you'll recognise the three ways they usually break.

- [Sixteen GPUs, eight busy](#sixteen-gpus-eight-busy)
- [The batch script runs on one node](#the-batch-script-runs-on-one-node)
- [What PyTorch needs from Slurm](#what-pytorch-needs-from-slurm)
- [Way 1: srun starts every rank](#way-1-srun-starts-every-rank)
- [Way 2: srun starts torchrun, torchrun starts the ranks](#way-2-srun-starts-torchrun-torchrun-starts-the-ranks)
- [Three ways it breaks](#three-ways-it-breaks)
- [On real GPUs](#on-real-gpus)
- [Back to the eight idle GPUs](#back-to-the-eight-idle-gpus)
- [References](#references)

---

## Sixteen GPUs, eight busy

A researcher moves a training script from one 8-GPU node to two. The job asks for `-N 2 --gpus-per-node=8`, Slurm allocates both nodes, the job runs, and it's exactly as fast as before. Monitoring shows the second node's GPUs at 0% for the whole run. Nobody gets an error. The job finishes, and they paid for two nodes and used one.

The batch script was:

```bash
#SBATCH -N 2 --gpus-per-node=8
python train.py
```

> [!NOTE]
> Lab: Slurm **23.11.4**, CPU nodes `cn001`–`cn004` (2 CPUs each), PyTorch **2.15.0** from PyPI in a venv at `/opt/torchenv` on every node, the **Gloo** backend on CPUs. No GPUs: the launch mechanics are what's tested here, and they don't depend on the device. Every output below is from the lab.

---

## The batch script runs on one node

A Slurm allocation is a set of nodes. The batch script itself is a single shell process, and it runs on the **first** node of the allocation. To run anything on the other nodes, you start a **job step** with `srun`. Two nodes, one test:

```bash
sbatch -p cpu -N2 --wrap 'hostname; srun hostname'
```

```text
cn001
cn001
cn002
```

`hostname` alone ran once, on `cn001`. `srun hostname` ran once per task, on both nodes. The researcher's `python train.py` is the first line: one process, one node, sixteen GPUs allocated.

So every multi-node training job needs `srun` somewhere. The only question is what `srun` starts.

---

## What PyTorch needs from Slurm

`torch.distributed.init_process_group()` with the default `env://` method reads four environment variables. Slurm sets its own versions of them for each task:

| PyTorch reads | Means | Slurm sets |
| --- | --- | --- |
| `RANK` | This process's global number, 0..N-1 | `SLURM_PROCID` |
| `WORLD_SIZE` | Total number of processes | `SLURM_NTASKS` |
| `LOCAL_RANK` | Number on this node, picks the GPU | `SLURM_LOCALID` |
| `MASTER_ADDR`, `MASTER_PORT` | Where rank 0 listens | Nothing. You choose: usually the first node, `scontrol show hostnames "$SLURM_JOB_NODELIST" \| head -n 1` |

The test program: every rank adds its rank + 1, so with 4 ranks every rank must print `sum=10`.

```python
# allreduce.py - every rank adds its number; all ranks should print the same sum.
import os, socket, torch, torch.distributed as dist
dist.init_process_group("gloo")   # reads RANK, WORLD_SIZE, MASTER_ADDR, MASTER_PORT
rank, world = dist.get_rank(), dist.get_world_size()
t = torch.tensor([float(rank + 1)])
dist.all_reduce(t)
print(f"rank {rank}/{world} on {socket.gethostname()} local_rank={os.environ.get('LOCAL_RANK')} sum={t.item():.0f}", flush=True)
dist.destroy_process_group()
```

---

## Way 1: srun starts every rank

One Slurm task per process. Slurm starts them all; a one-line wrapper renames Slurm's variables to PyTorch's:

```bash
#!/bin/bash
#SBATCH -J ddp-srun -p cpu -N 2 --ntasks-per-node=2 -t 00:05:00
export MASTER_ADDR=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
export MASTER_PORT=29500
srun bash -c 'RANK=$SLURM_PROCID WORLD_SIZE=$SLURM_NTASKS LOCAL_RANK=$SLURM_LOCALID \
  exec /opt/torchenv/bin/python -W ignore /usr/local/share/allreduce.py'
```

```text
rank 0/4 on cn001 local_rank=0 sum=10
rank 1/4 on cn001 local_rank=1 sum=10
rank 2/4 on cn002 local_rank=0 sum=10
rank 3/4 on cn002 local_rank=1 sum=10
```

The single quotes matter: the variables must expand inside each task, not once in the batch script. On GPUs, `--ntasks-per-node` equals the GPUs per node, and each rank uses GPU `LOCAL_RANK`.

The output also had a few lines like this, which are harmless in a container without IPv6:

```text
[c10d] The client socket cannot be initialized to connect to [cn001]:29500 (errno: 97 - Address family not supported by protocol).
```

**Good for:** Slurm accounts for every rank as a task, `scancel` and time limits hit every process directly, and `sacct` shows one step with N tasks.

---

## Way 2: srun starts torchrun, torchrun starts the ranks

One Slurm task **per node**. Each runs `torchrun`, which starts the per-node processes itself and sets `RANK`, `LOCAL_RANK` and `WORLD_SIZE` for them:

```bash
#!/bin/bash
#SBATCH -J ddp-torchrun -p cpu -N 2 --ntasks-per-node=1 --cpus-per-task=2 -t 00:05:00
head=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
srun /opt/torchenv/bin/torchrun \
  --nnodes="$SLURM_NNODES" --nproc-per-node=2 \
  --rdzv-backend=c10d --rdzv-endpoint="$head:29500" --rdzv-id="$SLURM_JOB_ID" \
  /usr/local/share/allreduce.py
```

```text
rank 0/4 on cn001 local_rank=0 sum=10
rank 1/4 on cn001 local_rank=1 sum=10
rank 3/4 on cn002 local_rank=1 sum=10
rank 2/4 on cn002 local_rank=0 sum=10
```

Same answer, 6 seconds of wall time. `torchrun` also printed a warning that it set `OMP_NUM_THREADS=1` for each process; set it yourself if your data loading needs more threads. Note `--cpus-per-task=2`: the one Slurm task must own all the CPUs (and on GPU nodes, all the GPUs) its child processes will use.

**Good for:** scripts already written for `torchrun`, and `torchrun`'s elastic features (restarting workers on failure, `--max-restarts`).

| | Way 1: `srun` per rank | Way 2: `srun` + `torchrun` |
| --- | --- | --- |
| Slurm tasks | One per process | One per node |
| Who sets `RANK` | Your wrapper, from `SLURM_PROCID` | `torchrun` |
| `--ntasks-per-node` | = processes per node | **1** |
| Rendezvous | `MASTER_ADDR:MASTER_PORT` | `--rdzv-endpoint` (c10d) |

---

## Three ways it breaks

| Mistake | What we saw |
| --- | --- |
| No `srun` at all | Runs once, on the first node (the story above). No error |
| `srun python` without setting `RANK` | `ValueError: Error initializing torch.distributed using env:// rendezvous: environment variable RANK expected, but not set`, every task exits 1, job `FAILED` |
| `torchrun` with `--ntasks-per-node=2` (copied from Way 1) | Four `torchrun` agents for a 2-node rendezvous. Two formed the group and the 4 ranks printed `sum=10`; the other two crashed with `RendezvousConnectionError: The connection to the C10d store has failed`. Job state `FAILED` |

The third one is the nasty one: the training ran, then the job reported failure, with a long traceback that never says "you started torchrun twice per node". In our run the two winning agents happened to be on different nodes. If both had been on the same node, all four ranks would have run there, on that node's GPUs only.

Rule of thumb: **count the processes.** `nodes × ntasks-per-node × nproc-per-node` must equal the world size you meant.

---

## On real GPUs

The same two scripts, with these changes. These are from the PyTorch and Slurm docs, not tested in this lab:

- Backend `nccl` instead of `gloo`, and `torch.cuda.set_device(int(os.environ["LOCAL_RANK"]))` before creating the process group.
- Ask for GPUs per node: `--gpus-per-node=8`. With Way 1, `--ntasks-per-node=8`; with Way 2, `--ntasks-per-node=1` and `--nproc-per-node=8`.
- NCCL picks a network interface on its own and can pick the wrong one on multi-homed nodes. `NCCL_DEBUG=INFO` prints which interface and transport it chose; `NCCL_SOCKET_IFNAME` forces one.
- If you use containers, [part 3](/fields/schedulers/slurm-ai-clusters/containers-with-pyxis.md) shows an Enroot hook that sets `RANK`, `WORLD_SIZE`, `MASTER_ADDR` and friends for you, tested in the lab.

---

## Back to the eight idle GPUs

The researcher's script becomes Way 2, because `train.py` was already written for `torchrun`:

```bash
#SBATCH -N 2 --ntasks-per-node=1 --gpus-per-node=8 --cpus-per-task=64
head=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
srun torchrun --nnodes=2 --nproc-per-node=8 \
  --rdzv-backend=c10d --rdzv-endpoint="$head:29500" --rdzv-id="$SLURM_JOB_ID" train.py
```

The first log line now says `world_size=16`, both nodes' GPUs show load, and the epoch time drops. The fix was one `srun`, because the batch script only ever ran on the first node.

**Takeaway:** the batch script runs on the first node only; start ranks with `srun`, either one task per rank with `RANK=$SLURM_PROCID`, or one task per node running `torchrun`, and make sure nodes × tasks × processes equals the world size.

**Next:** [Part 3, Containers with Pyxis and Enroot](/fields/schedulers/slurm-ai-clusters/containers-with-pyxis.md), runs the same ranks inside a container.

---

## References

- [sbatch(1)](https://slurm.schedmd.com/sbatch.html): the batch script runs on the first allocated node; `SLURM_*` output environment variables.
- [srun(1)](https://slurm.schedmd.com/srun.html): `SLURM_PROCID`, `SLURM_LOCALID`, `SLURM_NTASKS`.
- [PyTorch: torchrun (Elastic Launch)](https://docs.pytorch.org/docs/stable/elastic/run.html): `--nnodes`, `--nproc-per-node`, c10d rendezvous, the environment it sets.
- [PyTorch: torch.distributed](https://docs.pytorch.org/docs/stable/distributed.html): `init_process_group`, `env://` initialization, backends.
- [NCCL environment variables](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html): `NCCL_DEBUG`, `NCCL_SOCKET_IFNAME`.
- [The job script tale](/fields/schedulers/slurm-job-script-tale.md): what Slurm does with the batch script.
