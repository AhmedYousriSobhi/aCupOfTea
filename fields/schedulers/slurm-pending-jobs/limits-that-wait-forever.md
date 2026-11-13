
# Limits That Wait Forever: QOS and Account Limits in Practice

<!-- related-block -->
<div class="reading-time">7 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [Reading the Reason Column: Why Is My Slurm Job Pending?](/fields/schedulers/slurm-pending-jobs/why-is-my-job-pending.md), [Slurm Multi-Tenancy: Who Stores the Rules, Who Enforces Them](/fields/schedulers/slurm-accounting-multi-tenancy.md)  ·  **See also:** [The Guest List: Setting Up QOS Preemption Without Starting a War](/fields/schedulers/slurm-preemption/slurm-qos-preemption-setup.md), [Who Goes First: Slurm's Priority Number, Taken Apart](/fields/schedulers/slurm-pending-jobs/who-goes-first.md)

</div>


> **Part 3 of [Why Is My Job Still Pending?](/fields/schedulers/slurm-pending-jobs/README.md)** [Part 2](/fields/schedulers/slurm-pending-jobs/who-goes-first.md) decided the order of the queue. Limits decide whether a job may start at all, whatever its priority. By the end you'll set a per-user GPU cap that actually holds, reject jobs that could never run, and read how close anyone is to a limit.

- [The cap that didn't hold](#the-cap-that-didnt-hold)
- [Two places a limit can live](#two-places-a-limit-can-live)
- [The lab's limits](#the-labs-limits)
- [A limit that clears by itself](#a-limit-that-clears-by-itself)
- [A job that can never run](#a-job-that-can-never-run)
- [The second QOS](#the-second-qos)
- [Closing it with a partition QOS](#closing-it-with-a-partition-qos)
- [Who is using what, right now](#who-is-using-what-right-now)
- [Rolling out a new limit](#rolling-out-a-new-limit)
- [Back to the cap](#back-to-the-cap)
- [References](#references)

---

## The cap that didn't hold

The GPU partition keeps filling up with one group's jobs. The admins agree on a rule: at most two GPUs per user at a time. One `sacctmgr` command puts the cap on the GPU QOS, and the announcement goes out.

Two things happen in the next week. A new user submits a 4-GPU job, which shows `QOSMaxGRESPerUser` and sits in the queue for six days before anyone notices it can never start. And the same heavy user from before is somehow running three GPUs. Nobody broke anything. Both are exactly how the limit was written.

> [!NOTE]
> Lab: Slurm **23.11.4**, slurmdbd, `AccountingStorageEnforce=associations,limits,qos,safe`. One GPU node with four GPUs (fake device files, enough for scheduling). If limits seem to do nothing on your cluster at all, check `AccountingStorageEnforce` first: [Slurm multi-tenancy](/fields/schedulers/slurm-accounting-multi-tenancy.md) covers that trap.

---

## Two places a limit can live

| Where | Set with | Applies to | Reason names start with |
| --- | --- | --- | --- |
| An **association** (an account, or a user in an account) | `sacctmgr modify account/user ... set ...` | Every job charged to that account or user | `Assoc` |
| A **QOS** | `sacctmgr modify qos ... set ...` | Only jobs **running under that QOS** | `QOS` |

And each limit is one of two kinds:

| Kind | Example | Means |
| --- | --- | --- |
| `Grp...` | `GrpTRES=gres/gpu=3` | Shared total for everyone under it |
| `Max...` | `MaxTRESPerUser=gres/gpu=2` | Per user (or per job), each on their own |

The second row of the first table is the one that bites: a QOS limit only applies to jobs in that QOS.

---

## The lab's limits

```bash
sacctmgr -i add qos gpu-normal MaxTRESPerUser=gres/gpu=2
sacctmgr -i modify user alice,bob,carol,admin set qos+=gpu-normal
sacctmgr -i modify account physics set GrpTRES=gres/gpu=3
```

So: each user may hold two GPUs under `gpu-normal`, and the `physics` account (alice, bob, admin) may hold three in total. Every user can also still use the default `normal` QOS. That's the usual setup, and it's the source of the hole below.

---

## A limit that clears by itself

Alice runs a 2-GPU job, then asks for one more GPU:

```text
JOBID   USER     NAME        QOS TRES_PER_NOD    STATE                 REASON
   23  alice  a-1more gpu-normal   gres/gpu:1  PENDING      QOSMaxGRESPerUser
   22  alice   a-2gpu gpu-normal   gres/gpu:2  RUNNING                   None
```

That's the cap doing its job. When job 22 ends, job 23 starts. This kind of `QOS...` or `Assoc...` reason clears by itself: the job is fine on its own, it just has to wait for the user's (or account's) other jobs.

---

## A job that can never run

Carol asks for four GPUs at once, under a QOS that allows two per user:

```text
JOBID   USER     NAME        QOS TRES_PER_NOD    STATE                 REASON
   25  carol   c-4gpu gpu-normal   gres/gpu:4  PENDING      QOSMaxGRESPerUser
```

Same reason as alice's job, but a completely different situation: even with the whole cluster empty, this job breaks the limit by itself. It will wait forever, and by default Slurm accepts it and lets it.

The QOS flag **`DenyOnLimit`** makes Slurm reject such jobs at submission instead:

```bash
sacctmgr -i modify qos gpu-normal set flags=DenyOnLimit
```

Carol's same submission, after:

```text
sbatch: error: QOSMaxGRESPerUser
sbatch: error: Batch job submission failed: Job violates accounting/QOS policy (job submit limit, user's size and/or time limits)
```

Immediate and specific. `DenyOnLimit` judges each job **on its own**: a job that only goes over the limit because of the user's *other* running jobs is still accepted and waits, as alice's did above. The QOS documentation spells this out. So it removes the waiting-forever case without turning every busy moment into an error.

---

## The second QOS

Now the hole. With alice's two GPUs running, bob submitted a 1-GPU job without asking for any QOS, so it ran under `normal`:

```text
JOBID   USER     NAME        QOS TRES_PER_NOD    STATE                 REASON
   24    bob   b-2gpu gpu-normal   gres/gpu:2  PENDING           AssocGrpGRES
   26    bob  b-noqos     normal   gres/gpu:1  RUNNING                   None
   22  alice   a-2gpu gpu-normal   gres/gpu:2  RUNNING                   None
```

Job 26 **ran**. The per-user cap lives on `gpu-normal`, and job 26 isn't in `gpu-normal`. The only thing that stopped bob from taking even more was the account limit: physics was now at 3 GPUs, so his next job waited on `AssocGrpGRES`. A user in an account without a `GrpTRES` limit could have filled the node through `normal`.

This is the week-one surprise from the story: the heavy user's third GPU came in through a different QOS.

---

## Closing it with a partition QOS

A QOS can be attached to a **partition**. Then its limits apply to every job in that partition, whatever QOS the job asked for. In `slurm.conf`:

```text
PartitionName=gpu Nodes=gpu001 MaxTime=2-00:00:00 QOS=gpu-normal State=UP
```

After `scontrol reconfigure` (we redeployed and restarted), `scontrol show partition gpu` showed `QoS=gpu-normal`. Then bob ran a 2-GPU job and tried to sneak one more in under `normal`:

```text
JOBID   USER     NAME      QOS TRES_PER_NOD    STATE                 REASON
   32    bob  b-sneak   normal   gres/gpu:1  PENDING      QOSMaxGRESPerUser
   31    bob      b-2   normal   gres/gpu:2  RUNNING                   None
```

Both jobs are under `normal`, and the cap held anyway: the partition QOS counted them. The docs say the partition QOS overrides the job's QOS. The exception is a job QOS with the `OverPartQOS` flag, which reverses the order. Give that flag only to a QOS you'd let skip the partition's rules.

Rule of thumb: **a limit on a resource belongs on the partition that has the resource.** A QOS that users choose is for priority and special cases, not for the main cap.

---

## Who is using what, right now

`sacctmgr` shows limits. To see a limit next to current usage, ask the controller:

```bash
scontrol show assoc_mgr flags=qos qos=gpu-normal
scontrol show assoc_mgr flags=assoc accounts=physics
```

Trimmed, with alice running two GPUs:

```text
QOS=gpu-normal(3)
    User Limits
      alice(2001)
        MaxTRESPU=cpu=N(1),mem=N(200),...,gres/gpu=2(2)
      bob(2002)
        MaxTRESPU=cpu=N(0),mem=N(0),...,gres/gpu=2(0)
...
    GrpTRES=cpu=N(1),mem=N(200),node=N(1),billing=N(1),gres/gpu=3(2),
```

Each value reads **limit(in use)**: `gres/gpu=2(2)` means a limit of 2 with 2 in use, so alice's next GPU job waits. `N` means no limit. The `GrpTRES` line is the physics account: 2 of its 3 GPUs in use. This is the command to run when a user asks "which limit is holding me?".

---

## Rolling out a new limit

A new limit changes what runs tomorrow, so treat it as a change, not a command:

1. **Dry run:** count who would be over it today. `scontrol show assoc_mgr` with the new values in mind, or `squeue -o "%u %b" -t R` for current GPU use per user.
2. **Announce** the limit and the date, with the `whypending` script from [part 1](/fields/schedulers/slurm-pending-jobs/why-is-my-job-pending.md) so users can see why they're waiting.
3. **Enforce** on the partition QOS, with `DenyOnLimit`. Running jobs aren't killed when a limit is added; with the `safe` enforcement option, the docs say a running job isn't killed even if limits change under it.
4. **Rollback** is one `sacctmgr modify ... set MaxTRESPerUser=gres/gpu=-1` (`-1` clears a limit), and takes effect for the next scheduling pass.

---

## Back to the cap

Same rule, written properly this time. The 2-GPU cap goes on a QOS attached to the GPU partition, with `DenyOnLimit`. The new user's 4-GPU job is rejected the moment they submit it, with a message that names the limit, so they resubmit as two 2-GPU jobs or ask for an exception. The heavy user's third GPU waits on `QOSMaxGRESPerUser` whichever QOS they pick. And when someone asks why they're waiting, `scontrol show assoc_mgr` shows the limit and the usage side by side.

Nothing in the queue can wait forever any more. Every pending job is either first in line, behind someone with a better claim, or waiting for its own user's jobs to finish.

**Takeaway:** a QOS limit only binds jobs in that QOS, so put caps on a partition QOS; add `DenyOnLimit` so jobs that could never run are rejected, and read live usage with `scontrol show assoc_mgr`.

**Series index:** [Why Is My Job Still Pending?](/fields/schedulers/slurm-pending-jobs/README.md). For the scheduler that fits small jobs into gaps around all of this, see [backfill tuning](/fields/schedulers/slurm-backfill-tuning.md).

---

## References

- [Slurm QOS](https://slurm.schedmd.com/qos.html): QOS limits, partition QOS, `OverPartQOS`, `DenyOnLimit`.
- [Slurm: Resource Limits](https://slurm.schedmd.com/resource_limits.html): association limits, `Grp` vs `Max`, `AccountingStorageEnforce` options including `safe`.
- [sacctmgr(1)](https://slurm.schedmd.com/sacctmgr.html): setting and clearing limits (`-1`).
- [scontrol(1): show assoc_mgr](https://slurm.schedmd.com/scontrol.html#OPT_assoc_mgr): live limits and usage.
- [squeue(1): JOB REASON CODES](https://slurm.schedmd.com/squeue.html#SECTION_JOB-REASON-CODES): `QOSMaxGRESPerUser`, `AssocGrpGRES` and the rest.
- [Slurm multi-tenancy](/fields/schedulers/slurm-accounting-multi-tenancy.md): associations, enforcement, and the limit that silently does nothing.
