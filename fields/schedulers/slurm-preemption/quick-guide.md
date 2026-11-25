
<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/fields/">Fields</a> / <a href="#/fields/schedulers/">Schedulers</a> / <a href="#/fields/schedulers/slurm-preemption/">Dying Politely: Preemption, Requeue and Signals</a></nav>

# Set Up QOS Preemption and Make Jobs Survive It

<!-- related-block -->
<div class="reading-time">Intermediate · Guide · 5 min read · Updated 23 Nov 2026</div>
<!-- related-block -->
<div class="tag-chips"><a class="chip" href="#/.docs/generated/explore/tags/hpc">hpc</a> <a class="chip" href="#/.docs/generated/explore/tags/quick">quick</a> <a class="chip" href="#/.docs/generated/explore/tags/slurm">slurm</a></div>


> **Quick guide for** the [Preemption and signals series](/fields/schedulers/slurm-preemption/README.md).
> Use it when a high-priority tier must evict a low one, or a long job must survive being evicted. You end with a proven eviction and a job that requeues.

## Before you start

- Accounting is on (`sacctmgr` works) and you can restart `slurmctld` in a quiet moment.
- One idle node for the drill.
- Roll out in this order: create QOSs, edit `slurm.conf`, run the drill, then tell users.

---

## Part 1: Switch preemption on

1. Create the tiers.

   ```bash
   sacctmgr -i add qos low Priority=10
   sacctmgr -i modify qos low set PreemptMode=requeue GraceTime=120 PreemptExemptTime=00:30:00
   sacctmgr -i add qos high_bio Priority=1000
   sacctmgr -i modify qos high_bio set Preempt=low
   ```

   **Expect:** `sacctmgr show qos format=Name%14,Priority,Preempt%14,PreemptMode,GraceTime,PreemptExemptTime` lists `low` with `requeue` and `high_bio` with `Preempt` `low`.
   **If not:** `Preempt=` goes on the preemptor, `GraceTime` on the victim.

2. Let the account use them.

   ```bash
   sacctmgr -i modify account name="bio" set qos+=low,"high_bio"
   ```

   **Expect:** `sacctmgr show assoc format=Account%12,User%12,DefaultQOS,QOS%30` lists both.
   **If not:** a submit fails with `Invalid qos specification`.

3. Set `slurm.conf`, restart `slurmctld` if `PreemptType` changed.

   ```text
   PreemptType=preempt/qos
   PreemptMode=REQUEUE
   AccountingStorageEnforce=associations,qos
   PreemptParameters=send_user_signal
   ```

   **Expect:** `scontrol show config | grep -E '^Preempt|^AccountingStorageEnforce|^JobRequeue|^KillWait'` shows them.
   **If not:** read the log.

4. Run the drill on one node.

   ```bash
   L=$(sbatch --parsable -A physics --qos=low -w node1 --exclusive --requeue \
         --open-mode=append -o low.out --wrap='sleep 600')
   H=$(sbatch --parsable -A physics --qos=high_physics -w node1 --exclusive --wrap='sleep 5')
   sacct -X -D -j $L,$H -o JobID,QOS%12,State%12 -P
   scontrol show job $L | grep -oE 'Requeue=[0-9]+ Restarts=[0-9]+'
   ```

   **Expect:** low `PREEMPTED` then `RUNNING` again, high `COMPLETED`, and `Requeue=1 Restarts=1`.
   **If not:** see the table below.

**Don't:** announce the `low` tier before the drill passes.
**Roll back:** `sacctmgr -i modify qos low set GraceTime=30 PreemptExemptTime=00:00:00` shortens the grace period.

---

## Part 2: Route jobs with a submit rule

1. Put `job_submit.lua` next to the `slurm.conf` the controller uses.
2. Add `JobSubmitPlugins=lua` to `slurm.conf` and run `scontrol reconfigure`.

   ```bash
   scontrol show config | grep JobSubmitPlugins
   grep job_submit /var/log/slurm/slurmctld.log | tail -3
   ```

   **Expect:** `JobSubmitPlugins = lua` and `job_submit.lua loaded`.
   **If not:** with the plugin on and no file, `slurmctld` refuses to start.
3. The rules the page gives:
   - No `--time`: refuse with `slurm.ESLURM_INVALID_TIME_LIMIT`.
   - No `--qos`: set `low` and `job_desc.requeue = 1`.
   - `--qos=high`: set `high_<account>`.
   - `--exclusive=user` (`job_desc.shared == 2`): change to `0`.

   **Expect:** `sbatch --wrap='sleep 1'` prints `Please set --time, jobs without one are not accepted`.
   **If not:** the script is not loaded.

**Don't:** restart `slurmctld` with a broken script. It fails with `fatal: failed to initialize job_submit plugin`.

---

## Part 3: Make a training job survive eviction

```bash
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --signal=B:USR1@300
```

1. Run the trainer in the background and `wait` for it, so the `trap` can run:

   ```bash
   trap on_usr1 USR1
   python train.py --resume-latest &
   child=$!
   wait "$child"
   ```

   **Expect:** on `USR1` the handler asks the trainer to checkpoint, then runs `scontrol requeue "$SLURM_JOB_ID"`.
   **If not:** the trap never fires when the trainer runs in the foreground.
2. Cap restarts with `SLURM_RESTART_COUNT` and require a minimum runtime before requeueing.
3. Prefer `srun python train.py`. The trainer is then a step and hears the early `SIGTERM` itself.

**Don't:** save a checkpoint inside the handler. Set a flag and save at a safe boundary. The handler must be idempotent.

---

## Who hears what

| Event | Batch shell | `srun` steps |
|---|---|---|
| Preemption, `GraceTime` > 0 | No | Yes, about 1 s later |
| End of grace, time limit, `scancel` | Yes | Yes |
| `--signal=B:USR1@N` | Yes | No |
| `scancel -s USR1 <job>` | No | Yes (`--batch` for the shell) |

Timings are ticks, not stopwatches: the end of grace was noticed 3 to 25 s late on 23.11.4.

## Tips and tricks

- Use a user-defined signal such as `USR1`. `srun` passes it through.
- Measure your own timings with `probe.sh` and your `GraceTime`. Do not guess.
- `PreemptExemptTime` gives a job a minimum runtime before it can be preempted.
- `--open-mode=append` keeps the first run's log when a requeue starts the second.
- Changing `PriorityTier` or `OverSubscribe` needs only `scontrol reconfig`. Changing preemption plugin settings needs a full restart.
- `GraceTime` is not used with `SUSPEND`. There is a separate `suspend_grace_time`.

## Warnings

> [!WARNING]
> A broken `job_submit.lua` stops a restarting `slurmctld`: users then see "Unable to contact slurm controller".

- A bash `trap` runs only after the foreground command ends, so background the trainer and `wait`.
- A job that exits early still counts as preempted, whatever the reason.
- One preemptor can evict more than it needed: backfill reserves whole nodes.
- Suspend does not free licenses. Use `REQUEUE` or `CANCEL` with `PreemptParameters=reclaim_licenses`.
- Requeue starts the script again. It does not resume it.

## If it fails

| What you see | Likely cause | Fix |
|---|---|---|
| The victim is gone, no second run | No `--requeue` and `JobRequeue=0` | `JobRequeue=1`, or the submit rule |
| Nothing is evicted | `Preempt=` missing, or on the wrong QOS | `sacctmgr show qos format=Name,Preempt` |
| Nothing is evicted for 30 minutes | `PreemptExemptTime` | Lower it on the victim QOS |
| A high job waits behind a low one | `--exclusive=user` or `--exclusive=mcs` | Rewrite them in the submit rule |
| The batch shell hears nothing early | No `send_user_signal` | Set `PreemptParameters=send_user_signal` |

**Why it works:** [preemption and signals](/fields/schedulers/slurm-preemption/slurm-preemption-requeue-signals.md), [QOS setup](/fields/schedulers/slurm-preemption/slurm-qos-preemption-setup.md), [submit plugin](/fields/schedulers/slurm-preemption/slurm-job-submit-lua.md), [signals cheat sheet](/fields/schedulers/slurm-preemption/slurm-signals-cheatsheet.md). Next: [pending jobs](/fields/schedulers/slurm-pending-jobs/README.md).

<!-- related-block -->
<div class="see-also">

**See also**

- [Dying Politely: Preemption, Requeue and the Signals Your Training Job Ignores](/fields/schedulers/slurm-preemption/slurm-preemption-requeue-signals.md) — How Slurm preemption modes differ, what GraceTime and --signal send and to whom, why a bash trap never fires while the trainer runs, and a requeue-safe checkpoint wrapper that cannot loop.
- [The Guest List: Setting Up QOS Preemption Without Starting a War](/fields/schedulers/slurm-preemption/slurm-qos-preemption-setup.md) — A step-by-step setup of QOS-based requeue preemption (slurm.conf, sacctmgr, who may use what), a drill that proves it works, and the quiet ways it goes wrong.
- [The Receptionist Who Rewrites Your Badge: job_submit.lua](/fields/schedulers/slurm-preemption/slurm-job-submit-lua.md) — What the Lua job_submit plugin is, where its script lives, what it can read and return, four tested recipes (QOS routing, time limits, requeue, exclusive), and how it fails.
- [Who Gets Told What: Every Signal Slurm Sends, and Who Actually Hears It](/fields/schedulers/slurm-preemption/slurm-signals-cheatsheet.md) — Which signals Slurm sends at preemption, GraceTime, --signal, time limits and scancel, whether the batch shell or the srun steps receive them, and how late they really arrive.

</div>
