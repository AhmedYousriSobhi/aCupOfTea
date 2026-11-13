
# Containers on Slurm with Pyxis and Enroot

<!-- related-block -->
<div class="reading-time">8 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [Launching Distributed Training on Slurm: srun, torchrun, and the Rank Contract](/fields/schedulers/slurm-ai-clusters/launching-distributed-training.md)  ·  **See also:** [Lab Build Cheatsheet: A Slurm AI Cluster in Containers](/fields/schedulers/slurm-ai-clusters/lab-build-cheatsheet.md), [When a GPU Falls Off the Bus: Health Checks That Drain the Node](/fields/schedulers/slurm-ai-clusters/gpu-health-checks.md)

</div>


> **Part 3 of [Slurm for AI Clusters](/fields/schedulers/slurm-ai-clusters/README.md)** [Part 2](/fields/schedulers/slurm-ai-clusters/launching-distributed-training.md) started the ranks. Now they run inside a container image, so every node has the same CUDA, the same PyTorch, the same everything. By the end you'll run a multi-node step in a container with one `srun` flag, and you'll know the settings that make it work for every user, not just the admin who tested it.

- [Two ranks from a different universe](#two-ranks-from-a-different-universe)
- [What Pyxis and Enroot are](#what-pyxis-and-enroot-are)
- [Installing, and the dependencies nobody lists](#installing-and-the-dependencies-nobody-lists)
- [The first container step](#the-first-container-step)
- [It works as admin, fails as a user](#it-works-as-admin-fails-as-a-user)
- [Read-only by default, and mounts](#read-only-by-default-and-mounts)
- [Named containers outlive the job](#named-containers-outlive-the-job)
- [The PyTorch hook](#the-pytorch-hook)
- [Images from a registry](#images-from-a-registry)
- [Back to the two odd ranks](#back-to-the-two-odd-ranks)
- [References](#references)

---

## Two ranks from a different universe

A 4-node job in a container crashes with a mismatch nobody can explain: ranks 0–5 report one PyTorch version, ranks 6 and 7 another. Same `srun`, same `--container-image`. The two odd ranks were on a node added to the cluster last week, and their "container" was the node's own operating system. The new node was built without the Pyxis plugin, and `srun` didn't complain.

We reproduced it. `cn003` has no Pyxis; the image's `/etc/os-release` says `acot lab image 1.0`:

```bash
srun -p cpu -w cn003 --container-image=/srv/labimg.sqsh grep PRETTY /etc/os-release
```

```text
PRETTY_NAME="Ubuntu 24.04 LTS"
exit=0
```

Exit 0, and it ran on the host. `srun` on the login node knew the `--container-image` option because Pyxis was loaded *there*. The node that ran the task had never heard of it.

> [!NOTE]
> Lab: Slurm **23.11.4**. Enroot built from the **v4.2.1** tag (it reports `4.2.0`), Pyxis **v0.24.0**, both from source. `head01`, `cn001` and `cn002` have them; `cn003` doesn't, on purpose. The lab can't reach a container registry, so the images are small squashfs files we built (busybox plus an `os-release`). Pulling from a registry is docs-only below.

---

## What Pyxis and Enroot are

| Piece | What it is | Runs where |
| --- | --- | --- |
| **Enroot** | NVIDIA's tool that turns a container image into an unprivileged sandbox: a root filesystem plus user namespaces, no daemon | Every compute node |
| **Pyxis** | A Slurm **SPANK** plugin that adds `--container-*` options to `srun` and calls Enroot for each job step | Every node that runs `srun`, and every compute node |

SPANK plugins are listed in `plugstack.conf` and loaded by `srun`, `salloc`, `sbatch` and `slurmstepd`. That's the trap from the story: the option is parsed where you type it, and acted on (or not) where the task runs.

---

## Installing, and the dependencies nobody lists

Both build from their GitHub repositories. Enroot needs its git submodules, one of which (musl) is fetched from `git.musl-libc.org`; Pyxis needs the Slurm headers (`libslurm-dev` on Ubuntu, matching your Slurm version). The full commands are in the [lab cheatsheet](/fields/schedulers/slurm-ai-clusters/lab-build-cheatsheet.md#8-containers-enroot-and-pyxis).

Enroot is mostly shell scripts, and it fails at run time, not install time, when a tool is missing. Each of these produced an error inside a Slurm job in our lab:

| Missing | When it showed up | Error in the job output |
| --- | --- | --- |
| `curl` | Importing from a registry | `[ERROR] Command not found: curl` |
| `column` (`bsdextrautils` on Ubuntu) | Any **named** container | `[ERROR] Command not found: column` / `couldn't get list of existing container filesystems` |
| `unsquashfs` (`squashfs-tools`) | Creating a container from a `.sqsh` file | (installed before testing) |

`enroot check` lists what the kernel and host need. Run it on one node of each hardware type before rolling out.

One more from our own build: we built with the default `sysconfdir`, then installed with `sysconfdir=/etc`. The `enroot` script kept looking in `/usr/local/etc/enroot`, so none of the hooks in `/etc/enroot/hooks.d` ran. If the hooks seem to do nothing, check:

```bash
grep ENROOT_SYSCONF_PATH "$(command -v enroot)"
```

Then on every node, `/etc/slurm/plugstack.conf`:

```text
required /usr/local/lib/slurm/spank_pyxis.so
```

and restart `slurmd`. `required` means a node that can't load the plugin fails the step, instead of running it without.

---

## The first container step

```bash
srun -p cpu -N2 --container-image=/srv/labimg.sqsh sh -c "hostname; grep PRETTY /etc/os-release"
```

```text
cn002
cn001
PRETTY_NAME="acot lab image 1.0"
PRETTY_NAME="acot lab image 1.0"
```

A path to a squashfs file is the simplest image source: no registry, no import, the same file on every node. In production it lives on a shared filesystem; in the lab we copied it to each node.

Slurm's per-task variables reach the container unchanged:

```text
0 0 cn001 acot lab image
1 1 cn001 acot lab image
2 0 cn002 acot lab image
3 1 cn002 acot lab image
```

(`SLURM_PROCID`, `SLURM_LOCALID`, hostname, image name, from `srun -n4 ... sh -c 'echo $SLURM_PROCID $SLURM_LOCALID ...'`.) So both launch styles from [part 2](/fields/schedulers/slurm-ai-clusters/launching-distributed-training.md) work unchanged inside a container.

---

## It works as admin, fails as a user

The first multi-node test as user alice worked on `cn001` and failed on `cn002`:

```text
slurmstepd-cn002: error: pyxis: failed to create container filesystem for image: /srv/labimg.sqsh
slurmstepd-cn002: error: pyxis: printing enroot log file:
slurmstepd-cn002: error: pyxis:     mkdir: cannot create directory '/run/user/2001': Permission denied
```

Enroot's defaults put its runtime, cache and data under the XDG directories, like `${XDG_RUNTIME_DIR}/enroot`. `/run/user/2001` only exists while alice has a login session on that node. She'd logged into `cn001` earlier; she'd never logged into `cn002`. Batch jobs don't create a login session.

Set node-local paths for everyone, in `/etc/enroot/enroot.conf.d/10-paths.conf` on every node:

```text
ENROOT_RUNTIME_PATH /run/enroot/user-$(id -u)
ENROOT_CACHE_PATH   /var/lib/enroot/cache/user-$(id -u)
ENROOT_DATA_PATH    /var/lib/enroot/data/user-$(id -u)
```

```bash
mkdir -p /run/enroot /var/lib/enroot/cache /var/lib/enroot/data
chmod 1777 /run/enroot /var/lib/enroot/cache /var/lib/enroot/data
echo "d /run/enroot 1777 root root -" > /etc/tmpfiles.d/enroot.conf   # /run is a tmpfs: recreate at boot
```

After that, the same step worked on both nodes for alice. `ENROOT_DATA_PATH` holds unpacked container filesystems, so put it on a local disk with room for them.

---

## Read-only by default, and mounts

| Test | Result |
| --- | --- |
| `touch /x` in the container | `touch: /x: Read-only file system` |
| Same, with `--container-writable` | `wrote` |
| `--container-mounts=/srv:/data:ro`, then `ls /data` | `labimg.sqsh` |
| `touch /data/y` on that mount | `Read-only file system` |
| `--container-remap-root`, then `id` | `uid=0 gid=0 groups=0` (Pyxis's help: "Does not grant elevated system permissions, despite appearances") |

Read-only is the right default: a training job shouldn't write into its image. Datasets and checkpoints come in through `--container-mounts`; give each mount `:ro` unless the job writes to it. In our lab the user's home directory was mounted by Enroot's home hook without asking; whether that happens on your cluster depends on `ENROOT_MOUNT_HOME` and the hooks installed, so check before users rely on it.

---

## Named containers outlive the job

Unpacking a big image takes time. `--container-name` keeps the unpacked filesystem so the next step skips it:

```bash
#!/bin/bash
#SBATCH -p cpu -w cn001 -t 5
srun --container-image=/srv/labimg.sqsh --container-name=work --container-writable sh -c "echo step1 > /marker"
srun --container-name=work cat /marker
srun --container-image=/srv/labimg.sqsh sh -c "cat /marker 2>&1"
```

```text
step1
cat: can't open '/marker': No such file or directory
```

The second step reused the named container and found the file; the third, unnamed, got a fresh one. Then, after the job ended:

| Plugstack setting | `enroot list` on `cn001` after the job |
| --- | --- |
| Default (`container_scope=global`, per Pyxis's `config.c`) | `pyxis_work` |
| `container_scope=job` | (empty) |

With the default, every named container stays on the node's disk until someone removes it. That's a feature for a user who runs the same image all week, and a disk-full drain waiting to happen on a shared cluster. To clean up at the end of each job:

```text
required /usr/local/lib/slurm/spank_pyxis.so container_scope=job
```

---

## The PyTorch hook

Enroot ships optional hooks in `/usr/local/share/enroot/hooks.d/`. One, `50-slurm-pytorch.sh`, sets PyTorch's variables from Slurm's. It only acts when the image's environment defines `PYTORCH_VERSION`, which NVIDIA's PyTorch images do. We enabled it on the nodes and built a test image with that variable:

```bash
cp /usr/local/share/enroot/hooks.d/50-slurm-pytorch.sh /etc/enroot/hooks.d/
srun -p cpu -w cn[001-002] -n4 --container-image=/srv/ptimg.sqsh \
  sh -c 'echo $(hostname) RANK=$RANK LOCAL_RANK=$LOCAL_RANK WORLD_SIZE=$WORLD_SIZE MASTER_ADDR=$MASTER_ADDR MASTER_PORT=$MASTER_PORT OMP_NUM_THREADS=$OMP_NUM_THREADS'
```

```text
cn001 RANK=0 LOCAL_RANK=0 WORLD_SIZE=4 MASTER_ADDR=cn001 MASTER_PORT=61128 OMP_NUM_THREADS=1
cn001 RANK=1 LOCAL_RANK=1 WORLD_SIZE=4 MASTER_ADDR=cn001 MASTER_PORT=61128 OMP_NUM_THREADS=1
cn002 RANK=2 LOCAL_RANK=0 WORLD_SIZE=4 MASTER_ADDR=cn001 MASTER_PORT=61128 OMP_NUM_THREADS=1
cn002 RANK=3 LOCAL_RANK=1 WORLD_SIZE=4 MASTER_ADDR=cn001 MASTER_PORT=61128 OMP_NUM_THREADS=1
```

Everything Way 1 of [part 2](/fields/schedulers/slurm-ai-clusters/launching-distributed-training.md#way-1-srun-starts-every-rank) needed a wrapper for. The port is `SLURM_JOB_ID % 4536 + 61000` (job 128 here), so two jobs sharing a node don't collide. The same `srun` with the plain image left `RANK` empty. The hook doesn't overwrite a variable the image already sets.

---

## Images from a registry

Docs-only: the lab couldn't reach a registry. Pyxis also accepts registry images, as Enroot URIs:

```bash
srun --container-image=nvcr.io#nvidia/pytorch:<tag> python train.py
```

Pyxis imports a registry image on each node where the step runs (its README shows the `pyxis: importing docker image` line per step), so a 64-node job pulls from the registry 64 times at once. Our recommendation, not tested here: import once to a squashfs file on shared storage with `enroot import -o`, then point jobs at the file:

```bash
enroot import -o /shared/images/pytorch.sqsh docker://nvcr.io#nvidia/pytorch:<tag>
srun --container-image=/shared/images/pytorch.sqsh python train.py
```

Registry credentials go in `$ENROOT_CONFIG_PATH/.credentials`, in netrc format, per Enroot's `import` docs. Without `curl` on the node, the import fails as shown in the dependency table.

---

## Back to the two odd ranks

The new node gets `/etc/slurm/plugstack.conf` from the same Ansible role as the others, with `required`, so a node without Pyxis now fails container steps loudly instead of running them on the host. Enroot's paths point at node-local directories, so it works for users who never logged in. `container_scope=job` keeps named containers from filling the disks. And for a quick check that a node is ready, the [GPU health check in part 4](/fields/schedulers/slurm-ai-clusters/gpu-health-checks.md) can test for the plugin file too:

```bash
[ -e /usr/local/lib/slurm/spank_pyxis.so ] || scontrol update nodename="$(hostname -s)" state=drain reason="pyxis missing"
```

The odd ranks weren't a PyTorch bug. They ran outside the container, because nothing on that node knew there was one.

**Takeaway:** Pyxis must be loaded on every compute node, not just where you type `srun`, so mark it `required`; set node-local Enroot paths, mount data read-only into read-only images, and scope named containers to the job.

**Next:** [Part 4, GPU Health Checks](/fields/schedulers/slurm-ai-clusters/gpu-health-checks.md), keeps jobs off nodes whose GPUs aren't all there.

---

## References

- [Pyxis README](https://github.com/NVIDIA/pyxis) and [wiki: Setup](https://github.com/NVIDIA/pyxis/wiki/Setup): `--container-*` options, plugstack arguments such as `container_scope`, installation.
- [Enroot documentation](https://github.com/NVIDIA/enroot/tree/master/doc): `enroot.conf` paths, `import`/`create`/`start`, hooks, `.credentials`.
- [Enroot `50-slurm-pytorch.sh` hook](https://github.com/NVIDIA/enroot/blob/master/conf/hooks/extra/50-slurm-pytorch.sh): the variables it sets and when.
- [Slurm: SPANK](https://slurm.schedmd.com/spank.html): `plugstack.conf`, `required` vs `optional`, where plugins are loaded.
- [Slurm: Containers Guide](https://slurm.schedmd.com/containers.html): Slurm's own OCI container support, the alternative to Pyxis.
