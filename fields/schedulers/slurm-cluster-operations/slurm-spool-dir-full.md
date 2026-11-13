
# SlurmdSpoolDir Is Full: The Drain That Is Not About the Spool Directory

<!-- related-block -->
<div class="reading-time">10 min read</div>
<!-- related-block -->
<div class="related-strip">

**See also:** [Calling Dibs on Nodes: Reservations, Maintenance Windows and the Job That Fit](/fields/schedulers/slurm-cluster-operations/slurm-reservations-and-maintenance.md), [Kill Task Failed: A Murder Mystery With No Body (and One Drained Node)](/fields/schedulers/slurm-cluster-operations/slurm-kill-task-failed.md), [Rebooting a Slurm Cluster Without Losing Your Job (Or Anyone Else's)](/fields/schedulers/slurm-cluster-operations/slurm-reboot-order.md), [slurmstepd: The Small Daemon That Actually Runs Your Job](/fields/schedulers/slurm-inside-a-job/slurm-slurmstepd.md), [The Tale of a Slurm Job Script: Submission Is a Commitment, Not a Promise](/fields/schedulers/slurm-inside-a-job/slurm-job-script-tale.md), [When a GPU Falls Off the Bus: Health Checks That Drain the Node](/fields/schedulers/slurm-ai-clusters/gpu-health-checks.md)

</div>


> **Part of the [schedulers](/fields/schedulers/slurm-intro.md) directory.** The reason string, the recovery steps and the contents of the directory come from site documentation, mailing-list threads, a vendor support article and the `slurmd` man page. Nothing was run on a live cluster for this page, and the invented scenario is just that.

## Table of Contents

- [SlurmdSpoolDir Is Full: The Drain That Is Not About the Spool Directory](#slurmdspooldir-is-full-the-drain-that-is-not-about-the-spool-directory)
  - [Table of Contents](#table-of-contents)
  - [The drain with the wrong name](#the-drain-with-the-wrong-name)
  - [The directory is innocent, the filesystem is not](#the-directory-is-innocent-the-filesystem-is-not)
  - [What slurmd actually keeps in there](#what-slurmd-actually-keeps-in-there)
  - [The evidence that leaves the scene](#the-evidence-that-leaves-the-scene)
  - [A triage runbook](#a-triage-runbook)
  - [Bringing the node back](#bringing-the-node-back)
  - [Prevention: give temp files somewhere else to live](#prevention-give-temp-files-somewhere-else-to-live)
  - [Two spool directories, two different jobs](#two-spool-directories-two-different-jobs)
  - [Cheat sheet](#cheat-sheet)
  - [References](#references)

* * *

## The drain with the wrong name

Picture a GPU node that has been training for six days. Nothing in the job fails. Then `sinfo -R` shows a node drained with this reason:

```
SlurmdSpoolDir is full
```

The reaction is natural: go look at `/var/spool/slurmd`. It holds a few megabytes. Everyone's spool directory holds a few megabytes. The name of the error is a little misleading, and the rest of this page is about why.

The behavior itself is old. A commit from the early days of the project, by Moe Jette, carries a one-line message: "Slurmd will drain a compute node when the SlurmdSpoolDir is full." A vendor guide for GPU clouds describes it as a safety measure: when the filesystem holding the spool directory runs out of space, `slurmd` can no longer write its own state, so it drains the node.

* * *

## The directory is innocent, the filesystem is not

A user on the slurm-users list reported the error on a few nodes of a 242-node run, even though the spool directory had roughly 38 GB of free space and nothing was intentionally written there. Three replies explain the pattern:

- **"It is the partition that is full, not the directory itself."** The cause could be log files in `/var/log` just as easily as anything in `/var/spool`, because `/var` or `/var/spool` may sit on a partition shared with other things.
- **"This is basically always somebody filling up `/tmp`,"** when `/tmp` resides on the same filesystem as the spool directory. The reply is blunt, and it matches the vendor guide's own example: a node running long training jobs accumulates over a hundred gigabytes of temporary files in `/tmp` over several days and fills its root disk entirely.
- **One site's troubleshooting notes** list the symptom from the user's side: no `slurm-*.out` files appear, or jobs fail, when `/tmp`, `/var/tmp` or `/var/spool` fills, and they point out that `/var/spool` and `/var/tmp` typically share the same underlying storage, so filling one affects the other.

So the diagnosis is rarely "something wrote a lot into the spool directory". It is "something wrote a lot onto the same disk, and `slurmd` was the first thing polite enough to notice".

* * *

## What slurmd actually keeps in there

The administrator documentation is thin on this, and the person who started the 2023 thread said so. The answers from the list and from site documentation add up to this inventory:

| Item | What it is | Where I saw it |
|---|---|---|
| `jobNNNNN/slurm_script` | The batch script of each job on this node. One reply on the list describes finding "job scripts and various cached data" and typically a few megabytes in total | A permissions-error thread quoting `.../job00136/slurm_script`; the 2023 thread |
| `cred_state` (and `.old`, `.new`) | Credential state that `slurmd` rewrites; a `cred_state.new` write is the file in the failure message below | A permissions thread listing the directory; a site troubleshooting page |
| `hwloc_topo_whole.xml` | A cached topology file | The same permissions thread |
| `conf-cache/` | Configuration files fetched by `slurmd` in configless mode, with `/run/slurm/conf` pointing at it | Niflheim site documentation |
| `<nodename>_<jobid>.<stepid>` | Unix sockets for running steps, described on the [slurmstepd page](/fields/schedulers/slurm-inside-a-job/slurm-slurmstepd.md) | Slurm source |
| A core file, if `slurmd` crashes | The man page says a core file goes to `SlurmdSpoolDir`, or `/var/tmp/` as a last resort, unless `slurmd` runs with `-D` | `slurmd` man page |

Batch scripts are bounded: `max_script_size` in `SchedulerParameters` defaults to 4 MB. To fill a disk with scripts you would need an extraordinary number of jobs, which is why the list's first reaction was "can your job scripts contain large amounts of data?" and its second was "is the spool directory on shared storage?".

That second question matters. The Slurm configuration tool says the directory for `slurmd` state **must be unique on each compute server, on local disk**. A spool directory on shared storage is a different problem with a different smell.

Site documentation adds one more rule: the directory is not created by the RPM packages. You create it and set the owner yourself.

The failure itself, when it happens, looks like this in the logs (this exact message was posted by a site that hit it):

```
error: write /var/spool/slurmd/cred_state.new error No space left on device
```

* * *

## The evidence that leaves the scene

The 2023 thread contains a detail that every admin who has chased a full disk will recognize. When the author finally looked, `df -h` showed about 38 GB free. Large files that existed during the failure had been removed by the time anyone checked. The disk had been full, and then it was not, and the node was still drained.

There are two common ways for the evidence to disappear:

- A job ended and its temporary files were cleaned up (or the user deleted them) after `slurmd` had already drained the node.
- A process holds a **deleted file open**. Space is not returned while the file is still open, so `df` shows the disk full while `du` finds nothing to explain it. The vendor guide's answer is `lsof +L1`, which lists open files that have been unlinked.

Either way, look for the explanation in the logs from the time of the event as well as in the current state of the disk. The reason timestamp from `scontrol show node` tells you where to start.

* * *

## A triage runbook

```bash
# 1. Confirm the reason and when it happened
sinfo -R
scontrol show node <node> | grep -iE 'reason|state'

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

Notes on reading the results:

| Finding | What it suggests |
|---|---|
| `/tmp` is huge and on the root filesystem | Jobs writing scratch data to the default temp location |
| `/var/log` is huge | Logs not rotated, or debug logging left on |
| `df` is full, `du` finds little | A deleted-but-open file, so check `lsof +L1` |
| `df -h` fine, `df -i` full | Inode exhaustion from millions of small files |
| A core file in the spool directory | A `slurmd` crash. Check the logs before restarting anything |

> [!WARNING]
> Be careful with `rm` inside `SlurmdSpoolDir` itself. It holds the batch scripts and step sockets of jobs that may still be running, and an older SchedMD ticket describes the directory as part of how job state is restored. Clean up the *temporary files* that filled the disk, not the spool directory's own contents, unless you have drained the node and confirmed nothing is running on it. That advice is my reading of the design, so verify it on a test node.

* * *

## Bringing the node back

Once there is real free space, tell Slurm the node may take jobs again:

```bash
df -h /var/spool/slurmd          # confirm the headroom first
scontrol update NodeName=<node> State=RESUME
sinfo -n <node>
```

The drain does not clear itself when the disk recovers, so this step is manual. A good sign afterward is a job that starts and finishes cleanly, which proves `slurmd` can write its state again. If the node drains again within the hour, something is still filling the disk, and the cleanup treated a symptom.

* * *

## Prevention: give temp files somewhere else to live

The documentation point that explains the whole story is in Niflheim's notes: jobs store temporary files in `/tmp`, `/scratch` and `/dev/shm`, and **no cleanup is done after the job exits**. Add a large, shared, default temp directory and a long-running job, and the full disk becomes a matter of time.

**Options, from most to least integrated:**

| Approach | How it works | Notes |
|---|---|---|
| Namespace/tmpfs plugin | Gives each job private `/tmp`, `/var/tmp` and `/dev/shm` mounts backed by a base path, removed when the job ends | Needs `PrologFlags=Contain` and a `job_container.conf`. Renamed in 25.11 from `job_container/tmpfs` to `namespace/tmpfs`, configured with `NamespaceType=` instead of `JobContainerType=` |
| `auto_tmpdir` (SPANK plugin) | Creates and cleans a per-job temp directory | Third-party. A new Slurm major version needs a rebuild on a test node |
| `spank-private-tmp` | Private temp dirs | Does not clean up, so you must add cleanup |
| Cron cleanup | Removes old files from scratch | Crude, but it works. The site example removes files older than seven days under `/scratch` |

A configuration sketch from the Niflheim documentation:

```
# slurm.conf
NamespaceType=namespace/tmpfs        # before 25.11: JobContainerType=job_container/tmpfs
PrologFlags=Contain

# job_container.conf
AutoBasePath=true
BasePath=/scratch Dirs=/tmp,/var/tmp,/dev/shm Shared=true
```

The `Shared=true` option, from Slurm 23.02, is the one they flag as important when home directories are automounted, because older versions had trouble with NFS automounts under the tmpfs plugin. One suggestion of my own, not from the documentation: choose a `BasePath` on a filesystem **other than** the one holding `SlurmdSpoolDir` and the OS logs, so that a runaway job fills its own scratch space rather than the disk `slurmd` depends on.

**Other habits that pay off:**

- **Separate filesystems.** Put `/tmp`, `/scratch` and `/var/log` on different filesystems from the spool directory and the root disk, or at least apply quotas.
- **Know your `TmpFS`.** `TmpDisk` for a node is defined as the size of its `TmpFS` filesystem (default `/tmp`), and jobs can request space with `--tmp`. Set `TmpFS=/scratch` if that is where jobs really write.
- **Alert early.** A node health check that looks at free space on local filesystems (Niflheim's NHC notes show `DF_FLAGS` set to list only local filesystems) turns a surprise drain into a warning, and it can run on a schedule through `HealthCheckProgram`.
- **Rotate logs and keep debug off.** The `slurmd` log is on the same disk, and `SlurmdDebug=debug2` is not a long-term setting.

* * *

## Two spool directories, two different jobs

It is common to mix up the two directories that Slurm needs. They live on different machines and fail in different ways.

| Setting | Lives on | Holds | Remember |
|---|---|---|---|
| `SlurmdSpoolDir` | Every compute node, local disk | Per-node job scripts, credential state, config cache, step sockets | Fills up with the node's disk. Full means the node drains |
| `StateSaveLocation` | The controller (and shared for HA) | The controller's state: jobs, nodes, reservations | Back it up before upgrades, as in the [upgrade page](/fields/schedulers/slurm-cluster-operations/slurm-upgrade-order.md) |

An old SchedMD reply sums up the division in one line: the controller keeps its state in `StateSaveLocation` and the job information in `SlurmdSpoolDir`, so with both directories intact you have what you need to restore state after a restart.

* * *

## Cheat sheet

```
Reason "SlurmdSpoolDir is full" = slurmd cannot write its own state (cred_state.new ... ENOSPC)
Usual cause:   the FILESYSTEM is full, not the directory (often /tmp or /var/log on the same disk)
Check:         df -h, df -i, du per directory, lsof +L1 (deleted-but-open files)
Do not:        rm inside the spool dir while jobs may be running
Recover:       free space, then  scontrol update NodeName=<node> State=RESUME
Prevent:       private per-job temp dirs (namespace/tmpfs), separate filesystems, health checks
```

A node that drains itself over disk space is not being dramatic. It is the one daemon on the box that refuses to run jobs it cannot keep track of.

* * *

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