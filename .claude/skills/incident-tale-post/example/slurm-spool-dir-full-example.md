---
id: slurm-spool-dir-full
title: "SlurmdSpoolDir Is Full: The Drain That Is Not About the Spool Directory"
order: 7
sidebar_label: SlurmdSpoolDir is full
summary: Why slurmd drains node with reason "SlurmdSpoolDir is full", why culprit is filesystem underneath, what slurmd keeps in spool directory, a triage runbook, how to stop jobs from filling the disk.
level: intermediate
type: guide
domains:
  - systems-and-hpc
tags:
  - slurm
  - hpc
relations:
  related:
    - slurm-slurmstepd
    - slurm-kill-task-failed
    - slurm-reboot-order
---

# SlurmdSpoolDir Is Full: The Drain That Is Not About the Spool Directory

> **Part of the [schedulers](/fields/schedulers/slurm-intro.md) directory.** The reason string, the recovery steps and the contents of the directory come from site documentation, mailing-list threads, a vendor support article and the `slurmd` man page. Nothing was run on a live cluster for this page, and the invented scenario is just that.

Around 03:20, Dana will type one `rm -rf` that would have cost six days of training and the rest of her second week. She'll have a perfectly reasonable explanation for it. It will be completely wrong.

**By the end of this page you will be able to:**

- Explain why a node drains with "SlurmdSpoolDir is full" when that directory is only a few megabytes.
- Find what really filled the disk, including space that `du` can't see.
- Clean up and resume the node without touching what live jobs depend on.
- Stop it happening again, with an early warning and a safer disk layout.

---

## A directory gets the blame

It's 02:14. `gpu-node-07` has been training for six days, and nothing in the job has failed.

Dana is on call, in her second week on a cluster she inherited on Monday, when the alert lands in `#cluster-alerts`:

> **slurm-bot:** gpu-node-07 DRAINED. Reason: SlurmdSpoolDir is full

She runs `sinfo -R` to be sure, and sees the reason word for word:

```
SlurmdSpoolDir is full
```

The reason names a directory, so Dana goes and looks at the directory.

---

## Three attempts, all aimed at the directory

**Attempt 1: believe it.** The directory holds a few megabytes. Everyone's does. Dana decides the error is a false alarm and resumes the node:

```bash
scontrol update NodeName=gpu-node-07 State=RESUME
```

She goes back to bed.

> **slurm-bot, 03:10:** gpu-node-07 DRAINED. Reason: SlurmdSpoolDir is full

![Timeline: drained at 02:14, resumed, drained again at 03:10.](images/drain-again.svg)

*Resuming changes the label. Only free space changes the node.*

**Attempt 2: blame the folders.** If the directory is the problem, something inside it must be stale. It holds `job00136/` and a handful of other job folders that look old. Dana types:

```bash
rm -rf /var/spool/slurmd/job*
```

**Attempt 3: be careful.** Dana narrows the glob:

```bash
rm -rf /var/spool/slurmd/job001*
```

It is the same mistake, only more precisely aimed. Her finger is on Enter when a message lands:

> **Omar (training team):** Dana, is that gpu-node-07? Our six days of training are on it. Please tell me none of that is live.

She isn't sure. She takes her hand off the keyboard.

Three attempts, and the error sent her wrong each time:

- First it made her trust a directory that was fine.
- Then it made her attack that directory.
- Then her carefulness made the attack more precise, not less wrong.

The question was never about the directory. It was about the disk underneath. Who else lives on that disk?

---

## What the node knows that the alert doesn't

### The error, decoded

`slurmd` drains a node when the filesystem holding `SlurmdSpoolDir` runs out of space.

- **The history:** an early commit by Moe Jette says it in one line: "Slurmd will drain a compute node when the SlurmdSpoolDir is full."
- **The reason:** a vendor guide for GPU clouds calls it a safety measure. `slurmd` can no longer write its own state, so it drains the node.

The failure looks like this in the log (posted by a site that hit it):

```
error: write /var/spool/slurmd/cred_state.new error No space left on device
```

Not drama: `slurmd` is the one daemon on the box that refuses to run jobs it cannot keep track of.

### Who shares the disk

A user reported the error on a few nodes of a 242-node run, with roughly 38 GB free in the spool directory and nothing intentionally written there. The replies and a site's notes explain the pattern:

- *"It is the partition that is full, not the directory itself."* Log files in `/var/log` can be the cause as easily as anything in `/var/spool`, because `/var` or `/var/spool` may sit on a partition shared with other things.
- *"This is basically always somebody filling up `/tmp`,"* when `/tmp` is on the same filesystem as the spool directory.
- **The vendor guide's example:** a node running long training jobs accumulates over a hundred gigabytes of temporary files in `/tmp` over several days and fills its root disk.
- **A site's notes (Pasteur, not a reply on that thread):** no `slurm-*.out` files appear, or jobs fail, when `/tmp`, `/var/tmp` or `/var/spool` fills. `/var/spool` and `/var/tmp` typically share the same underlying storage, so filling one affects the other.

So the diagnosis is rarely "something wrote a lot into the spool directory". It is "something wrote a lot onto the same disk, and `slurmd` was the first thing polite enough to notice".

![One disk shared by the spool directory, the logs and /tmp. /tmp grows until the disk is full and the node drains.](images/shared-disk.svg)

*Three things share one filesystem. Whichever grows, the node drains.*

### Triage, in order

```bash
# 1. Confirm the reason and when it happened
sinfo -R
scontrol show node <node> | grep -iE 'reason|state'
#    The reason timestamp marks where to look in the logs.

# 2. Which filesystem holds the spool directory, and how full is it?
scontrol show config | grep -i SlurmdSpoolDir
df -h /var/spool/slurmd /tmp /var/tmp /var/log
df -i /var/spool/slurmd          # out of inodes also says "No space left on device"

# 3. Find the culprit one directory at a time
#    (du over everything can hang on a disk that is completely full)
du -sh /tmp /var/tmp /var/log /home 2>/dev/null

# 4. Space that du cannot see: deleted files still held open
lsof +L1

# 5. Who is using it? (job IDs often appear in the path)
ls -lt /tmp | head
```

How to read the results:

| Finding | What it suggests |
|---|---|
| `/tmp` huge, on the root filesystem | Jobs writing scratch data to the default temp location |
| `/var/log` huge | Logs not rotated, or debug logging left on |
| `df` full, `du` finds little | A deleted-but-open file: check `lsof +L1` |
| `df -h` fine, `df -i` full | Inode exhaustion from millions of small files |
| A core file in the spool directory | A `slurmd` crash: check the logs before restarting anything |

![df says 100 percent, du finds a little. A deleted file still held open by a process explains the gap.](images/deleted-open.svg)

*Space held by a deleted file is not returned until the process closes it. `lsof +L1` lists open files that have been unlinked (the vendor guide's answer).*

### When the evidence is gone

A detail from the 2023 thread that every admin who has chased a full disk will recognise:

- `df -h` showed about 38 GB free when the author finally looked.
- The large files that existed during the failure had been removed by then.
- The disk had been full, then it was not, and the node was still drained.

Two common ways the evidence disappears:

- A job ended and its temporary files were cleaned up (or the user deleted them) after `slurmd` had already drained the node.
- A process holds a deleted file open (see the sketch above).

Either way, read the logs from the time of the event as well as the current state of the disk. The reason timestamp from `scontrol show node` is the starting point.

### What is inside the directory

The administrator documentation is thin on this, and the author of a 2023 slurm-users thread said so. Each line below names its source, and the listing is assembled, not captured from a live node.

```
$ ls -l /var/spool/slurmd
job00136/                      # one folder per job; holds slurm_script, the batch script (2022 thread)
                               #   "job scripts and various cached data", a few MB in total (2023 thread)
cred_state  (.old, .new)       # credential state that slurmd rewrites; cred_state.new is the file in the error (2022 thread, a site troubleshooting page)
hwloc_topo_whole.xml           # a cached topology file (2022 thread)
conf-cache/                    # configless-mode configs; /run/slurm/conf points here (Niflheim)
<nodename>_<jobid>.<stepid>    # unix sockets of running steps (Slurm source, slurmstepd page)
a core file                    # only if slurmd crashes; lands here, or in /var/tmp/ as a last
                               #   resort, unless slurmd runs with -D (slurmd man page)
```

The sockets are described on the [slurmstepd page](/fields/schedulers/slurm-inside-a-job/slurm-slurmstepd.md).

Three facts rule out the directory itself as the culprit:

- **Scripts can't fill it.** `max_script_size` in `SchedulerParameters` defaults to 4 MB, so filling a disk with scripts takes an extraordinary number of jobs.
- **The list asked the right questions.** The first reaction was "can your job scripts contain large amounts of data?", and the second was "is the spool directory on shared storage?".
- **It must be local, and it is created by the admin.** It must be **unique on each compute server, on local disk** (the Slurm configuration tool). The RPM packages do not create it: the admin creates it and sets the owner (site documentation). A spool directory on shared storage is a different problem with a different smell.

### Clean up, then resume

> [!WARNING]
> Don't `rm` inside `SlurmdSpoolDir` while jobs may be running. It looks like clutter. It is a filing cabinet that `slurmd` expects to find in order.

- It holds the batch scripts and step sockets of jobs that may still be running.
- An older SchedMD ticket describes the directory as part of how job state is restored.
- Clean up the *temporary files* that filled the disk, not the directory's own contents, unless the node is drained and nothing is running on it.
- That advice is the page author's reading of the design: verify it on a test node.

Resume only once there is real free space:

```bash
df -h /var/spool/slurmd          # confirm the headroom first
scontrol update NodeName=<node> State=RESUME
sinfo -n <node>
```

- The drain does not clear itself when the disk recovers, so resuming is manual.
- A good sign afterwards: a job that starts and finishes cleanly, which proves `slurmd` can write its state again.
- If the node drains again within the hour, something is still filling the disk and the cleanup treated a symptom.

### Two spool directories, two jobs

Slurm needs two directories, on different machines, and they fail differently.

| Setting | Lives on | Holds | Remember |
|---|---|---|---|
| `SlurmdSpoolDir` | Every compute node, local disk | Per-node job scripts, credential state, config cache, step sockets | Fills up with the node's disk. Full means the node drains |
| `StateSaveLocation` | The controller (shared for HA) | The controller's state: jobs, nodes, reservations | Back it up before upgrades, as on the [upgrade page](/fields/schedulers/slurm-cluster-operations/slurm-upgrade-order.md) |

An old SchedMD reply sums it up in one line: the controller keeps its state in `StateSaveLocation` and the job information in `SlurmdSpoolDir`, so with both directories intact you have what you need to restore state after a restart.

![SlurmdSpoolDir on every compute node versus StateSaveLocation on the controller.](images/two-spool-dirs.svg)

*One drains a node when it fills. The other holds the controller's state.*

---

## The spool directory, cleared of all charges

Back on `gpu-node-07`, at 03:30, Dana reads her triage output:

```
df -h:   /  100%   (spool directory, /tmp and /var/log all on it)
du:      /tmp is most of what it can see
ls -lt:  scratch folders from jobs that finished days ago
lsof:    nothing held open worth chasing
```

The culprit was never the spool directory:

- Earlier jobs had written scratch data to `/tmp`, the default location.
- Nothing cleans `/tmp` after a job exits.
- Over several days it ate the disk that `slurmd` lives on.

The spool directory, meanwhile, was blamed twice in one night. It is taking it well.

Dana deletes the leftover temporary files and not a single file inside `/var/spool/slurmd`. She checks the headroom with `df -h`, then resumes the node.

> **Omar:** and our six days?
> **Dana:** untouched. I was one Enter key from deleting the live job's folders.

By the end of the shift a job has started and finished cleanly on `gpu-node-07`, the sign that `slurmd` can write its state again.

The error named a directory. The disk was the culprit.

---

## So it can't happen on Monday

Niflheim's notes name the cause: jobs store temporary files in `/tmp`, `/scratch` and `/dev/shm`, and **no cleanup is done after the job exits**. `/tmp` never complains about this; it just fills. Add a large, shared, default temp directory and a long-running job, and the full disk becomes a matter of time.

![Four ways to keep job temp files off the disk slurmd needs, from most to least integrated.](images/fix-ladder.svg)

*Four options, from most to least integrated.*

| Approach | How it works | Notes |
|---|---|---|
| `namespace/tmpfs` plugin | Private `/tmp`, `/var/tmp` and `/dev/shm` per job, backed by a base path and removed when the job ends | Needs `PrologFlags=Contain` and a `job_container.conf`. Renamed in 25.11 from `job_container/tmpfs`, configured with `NamespaceType=` instead of `JobContainerType=` |
| `auto_tmpdir` (SPANK plugin) | Creates and cleans a per-job temp directory | Third party: a new Slurm major version needs a rebuild on a test node |
| `spank-private-tmp` | Private temp directories | Does not clean up, so you must add cleanup |
| Cron cleanup | Removes old files from scratch | Crude, but it works. The site example removes files older than seven days under `/scratch` |

The most integrated option, from the Niflheim documentation:

```
# slurm.conf
NamespaceType=namespace/tmpfs        # before 25.11: JobContainerType=job_container/tmpfs
PrologFlags=Contain

# job_container.conf
AutoBasePath=true
BasePath=/scratch Dirs=/tmp,/var/tmp,/dev/shm Shared=true
```

- **`Shared=true`** (from Slurm 23.02) is the option they flag as important when home directories are automounted: older versions had trouble with NFS automounts under the tmpfs plugin.
- **The page author's suggestion, not from the documentation:** put `BasePath` on a filesystem **other than** the one holding `SlurmdSpoolDir` and the OS logs, so a runaway job fills its own scratch space rather than the disk `slurmd` depends on.

Other habits that pay off:

- **Separate filesystems.** Put `/tmp`, `/scratch` and `/var/log` on different filesystems from the spool directory and the root disk, or at least apply quotas.
- **Know your `TmpFS`.** `TmpDisk` for a node is the size of its `TmpFS` filesystem (default `/tmp`), and jobs can request space with `--tmp`. Set `TmpFS=/scratch` if that is where jobs really write.
- **Alert early.** A node health check on free space on local filesystems turns a surprise drain into a warning.
  - Niflheim's NHC notes set `DF_FLAGS` to list only local filesystems.
  - It can run on a schedule through `HealthCheckProgram`.
- **Rotate logs and keep debug off.** The `slurmd` log is on the same disk, and `SlurmdDebug=debug2` is not a long-term setting.

**Next:** the controller's state lives in `StateSaveLocation`. What should you back up before an upgrade, and in what order? See [the upgrade-order page](/fields/schedulers/slurm-cluster-operations/slurm-upgrade-order.md).

---

## 📜 The Scroll (keep this)

```
Reason "SlurmdSpoolDir is full" = slurmd cannot write its own state (cred_state.new ... ENOSPC)
Usual cause:   the FILESYSTEM is full, not the directory (often /tmp or /var/log on the same disk)
Check:         df -h, df -i, du per directory, lsof +L1 (deleted-but-open files)
Do not:        rm inside the spool dir while jobs may be running
Recover:       free space, then  scontrol update NodeName=<node> State=RESUME
Prevent:       private per-job temp dirs (namespace/tmpfs), separate filesystems, health checks
```

## References

- [slurm-users: SlurmdSpoolDir full (December 2023)](https://lists.schedmd.com/pipermail/slurm-users/2023-December/010748.html), with replies [here](https://lists.schedmd.com/pipermail/slurm-users/2023-December/010751.html) and [here](https://lists.schedmd.com/pipermail/slurm-users/2023-December/010754.html)
- [Crusoe: How to recover a Slurm node drained due to full root disk](https://support.crusoecloud.com/hc/en-us/articles/52235931715611-How-To-Recover-a-Slurm-Node-Drained-Due-to-Full-Root-Disk)
- [Slurm source history: "Slurmd will drain a compute node when the SlurmdSpoolDir is full"](https://earth.bsc.es/gitlab/mgimenez/ces_slurm_simulator/-/commit/c233f9dd2232287cda00da3679b961450273129c)
- [Pasteur troubleshooting notes: full /tmp or /var/tmp](https://docs-7e7aab.pages.pasteur.fr/troubleshooting/)
- [slurm-users: SlurmdSpoolDir permissions and directory contents (2022)](https://lists.schedmd.com/pipermail/slurm-users/2022-August/009058.html)
- [Niflheim: Slurm configuration (spool directories, temporary job directories, configless cache)](https://niflheim-system.readthedocs.io/en/latest/Slurm_configuration.html)
- [Slurm: configuration tool (easy version)](https://slurm.schedmd.com/configurator.easy.html)
- [Slurm: slurmd man page (core file location)](https://manpages.opensuse.org/Leap-15.6/slurm-node/slurmd.8.en.html)
- [SchedMD ticket 689: advice for running in production](https://support.schedmd.com/show_bug.cgi?id=689)
