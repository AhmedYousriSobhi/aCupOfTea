# OSU Benchmarks, Explained Like You're Debugging Them at 2 AM

If you work in HPC long enough, someone eventually hands you a ticket that says "network seems slow, can you run OSU?" and walks away. This is the guide I wish someone had given me before I had to Google what `osu_bibw` even meant.

---

## The one-sentence version

**OSU Micro-Benchmarks measure how well MPI talks over your network — nothing more, nothing less.**

Not your GPU. Not your CPU. Not your storage. Just: *when Rank 0 sends a message to Rank 1, how long does it take, and how much data can flow per second?*

That's it. Everything else in this guide is detail.

---

## Where it came from

OSU stands for **Ohio State University** — specifically their Network-Based Computing Lab, the same group behind MVAPICH. Back in the day, people needed a way to answer a simple question: *"Is my slow app slow because of my code, or because of my network?"* So they built tiny, boring, single-purpose test programs that do nothing but send messages back and forth. Over the years the suite grew to cover MPI collectives, OpenSHMEM, UPC++, and eventually GPU buffers via CUDA.

Think of it as a stethoscope for your interconnect. It doesn't fix anything — it just tells you exactly where the problem lives.

---

## The three benchmarks that actually matter day-to-day

| Benchmark | What it's really asking | Analogy |
|---|---|---|
| `osu_latency` | "How long for one message to make a round trip?" | Texting a friend and timing their reply |
| `osu_bw` | "How much data can I shove through in one direction?" | Timing how fast you can move boxes onto a truck |
| `osu_bibw` | "What if both sides send at once?" | Two people moving boxes through the same doorway simultaneously |

Everything else (`osu_allreduce`, `osu_alltoall`, `osu_bcast`, etc.) is a variation on "how fast can a group of ranks coordinate," which matters a lot more once you're running real distributed training or CFD jobs.

---

## The math, minus the intimidation

**Latency** is just: send a message, get a reply, divide by two.

```
one_way_latency = round_trip_time / 2
```

**Bandwidth** is just: how much data, divided by how long it took.

```
bandwidth = (message_size × window_size) / elapsed_time
```

The one equation worth tattooing on your monitor:

```
T(S) = α + S/B
```

Where `α` is fixed overhead (latency) and `S/B` is size divided by bandwidth. This single formula explains almost every OSU curve you'll ever see:

- **Tiny messages** → `α` dominates → the curve is flat and latency-bound, no matter how fast your NIC is.
- **Huge messages** → `S/B` dominates → you finally see your real, sustained bandwidth.

That's why a 1-byte message and a 4 MB message tell you completely different stories about the same network.

---

## "Reference" doesn't mean what you think it means

This is the part people get wrong constantly: **there is no universal "correct" OSU number.** A 400 Gb/s link doesn't mean you should expect 50 GB/s out of `osu_bw`. You need to pick which kind of reference you're comparing against:

1. **Theoretical hardware limit** — divide your link speed by 8 to get GB/s, then treat that as a ceiling, not a target.
2. **Known-good baseline** — "this node used to get 48 GB/s, now it gets 45" is a regression, full stop, regardless of theory.
3. **Application requirement** — if your app needs Allreduce under 20 µs and you're getting 18 µs, you're fine. Nobody cares if that's "only" 90% of theoretical.

Pick one before you start comparing numbers, or you'll chase ghosts.

---

## RoCE, quickly

**RoCE = RDMA over Converged Ethernet.** It's a way to get InfiniBand-style low-latency, kernel-bypass communication (RDMA) but running over regular Ethernet instead of a dedicated IB fabric. Modern deployments almost always mean **RoCEv2**, which wraps RDMA traffic in UDP/IP so it can actually be routed like normal network traffic.

The important bit for benchmarking: **OSU doesn't care whether you're on InfiniBand or RoCE.** It talks to MPI, and MPI picks the transport underneath (UCX, libfabric, whatever). OSU just reports what came out the other end.

---

## "But OSU touches GPU memory — isn't that the same as NCCL or BabelStream?"

No, and this trips people up constantly. Same hardware, wildly different software paths:

| Tool | What it actually tests | Path |
|---|---|---|
| **BabelStream** | GPU's own memory bandwidth | GPU compute cores ↔ HBM (never leaves the GPU) |
| **NCCL tests** | NVIDIA's own GPU-to-GPU comms | GPU ↔ NVLink/PCIe/NIC via NCCL |
| **OSU (CPU buffers)** | Your MPI stack over the network | CPU ↔ MPI ↔ NIC ↔ network |
| **OSU (CUDA buffers)** | Your MPI stack's *GPU-aware* comm path | GPU ↔ MPI (GPU-aware) ↔ NIC ↔ network |

They're four completely different software stacks touching the same silicon. Running all four isn't redundant — it's how you triangulate a problem. For example:

- BabelStream ✅, NCCL ✅, but OSU (CPU) ❌ → your GPUs and NCCL are fine, your **MPI setup is broken**.
- BabelStream ✅, OSU (CPU) ✅, but NCCL ❌ and OSU (GPU) ❌ → the issue is likely **GPU↔NIC topology or GPUDirect RDMA**, not basic networking.

That's the whole point of running more than one — each tool isolates a different layer, and the layer that fails tells you exactly where to dig.

---

## Building it (the short version)

```bash
module load gcc openmpi
wget <osu-tarball>
tar xf osu-micro-benchmarks-<version>.tar.gz
cd osu-micro-benchmarks-<version>

./configure CC=mpicc CXX=mpicxx --prefix=$HOME/opt/omb
make -j && make install
export PATH=$HOME/opt/omb/bin:$PATH
```

For GPU (H200-relevant) builds, just add CUDA flags:

```bash
./configure CC=mpicc CXX=mpicxx \
  --enable-cuda \
  --with-cuda-include=/usr/local/cuda/include \
  --with-cuda-libpath=/usr/local/cuda/lib64
make -j && make install
```

**Golden rule:** build OSU against the exact MPI you actually intend to run in production. A benchmark built against the wrong MPI is measuring nothing useful.

---

## Running it

```bash
# Basic CPU latency between two ranks
mpirun -np 2 --host node01,node02 ./osu_latency

# Bandwidth
mpirun -np 2 --host node01,node02 ./osu_bw

# Collective (Allreduce across 8 ranks)
mpirun -np 8 ./osu_allreduce

# GPU-to-GPU (device buffers) — needs CUDA-enabled build + GPU-aware MPI
mpirun -np 2 ./osu_latency D D
```

Watch out: if both ranks land on the same node, you're accidentally benchmarking shared memory, not the network. Always pin ranks to separate nodes when you're testing the fabric.

---

## A sane diagnostic order when numbers look bad

Don't jump straight to "the network is broken." Work through it like a checklist:

```
1. Is this actually inter-node?
2. Right MPI, right version?
3. Right transport (UCX/OFI/TCP)?
4. Right NIC selected?
5. Rank placement sane?
6. CPU / NUMA affinity correct?
7. PCIe topology reasonable?
8. Link state / congestion?

If GPU involved, also check:
9. GPU-aware MPI actually enabled?
10. GPUDirect RDMA working?
11. GPU ↔ NIC topology favorable? (nvidia-smi topo -m)
```

Nine times out of ten it's #2 through #6, not the actual fabric.

---

## The one-paragraph takeaway

OSU is a stethoscope, not a scoreboard. It doesn't tell you if your network is "fast" — it tells you exactly how a *specific, precisely configured* communication path performs, one layer at a time. Run CPU-buffer OSU to validate MPI-over-network, GPU-buffer OSU to validate MPI's GPU-aware path, BabelStream to validate raw HBM bandwidth, and NCCL tests to validate NVIDIA's own GPU comm stack — separately, not as interchangeable "GPU benchmarks." Keep them apart, and when something's slow, you'll know which layer to blame instead of guessing.