
# Dying Politely: Preemption, Requeue and Signals


A high-priority job arrives and a running job has to make room. Whether it dies cleanly, loses a day of training, or restarts by itself depends on settings most clusters never test. This series goes from the theory to a working setup to a signal reference.

Read parts 1 to 3 in order. Part 4 is the reference you come back to.

---

## Contents

| File | Description |
| --- | --- |
| [1. Dying Politely](/fields/schedulers/slurm-preemption/slurm-preemption-requeue-signals.md) | Preemption modes, `GraceTime`, signals your training job ignores, and a requeue-safe wrapper |
| [2. The Guest List](/fields/schedulers/slurm-preemption/slurm-qos-preemption-setup.md) | Setting up QOS preemption with requeue, step by step, with a drill that proves it works |
| [3. job_submit.lua](/fields/schedulers/slurm-preemption/slurm-job-submit-lua.md) | Routing jobs to the right QOS, requiring time limits, and how the plugin fails |
| [4. Who Gets Told What](/fields/schedulers/slurm-preemption/slurm-signals-cheatsheet.md) | Every signal Slurm sends, whether the batch shell or the `srun` steps hear it, and how late it arrives |
| [Quick guide: Set Up QOS Preemption and Make Jobs Survive It](/fields/schedulers/slurm-preemption/quick-guide.md) | Steps to switch on QOS preemption, prove it, add a submit rule and make a job requeue |

---

## Related pages

- [Multi-tenancy: who stores the rules](/fields/schedulers/slurm-accounting-multi-tenancy.md): QOS, associations and fairshare, the prerequisite for part 2.
- [Autopsy of a job: `sacct`](/fields/schedulers/slurm-sacct-job-forensics.md): reading how a preempted or requeued job ended.
- [Inside a Slurm job](/fields/schedulers/slurm-inside-a-job/README.md): the daemon and cgroups that deliver the signals.
- [What changed between Slurm 23.11 and 26.05](/fields/schedulers/slurm-cluster-operations/slurm-version-changes.md): version differences for preemption, Lua and signals.

<!-- related-block -->
<div class="mentioned-in">

**Mentioned in**

- [Check That Slurm Still Works After a Change](/fields/schedulers/slurm-smoke-tests/quick-guide.md) — Which check to run after a change, an upgrade, a policy edit or a repair, with the command and the output that means pass.
- [Set Up QOS Preemption and Make Jobs Survive It](/fields/schedulers/slurm-preemption/quick-guide.md) — Steps to switch on QOS preemption, prove it with a drill, add a submit rule, and make a training job catch its warning and requeue.

</div>
