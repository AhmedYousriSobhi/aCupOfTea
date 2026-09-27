## The Tale of job.sh and the Snapshot

## Table of Contents
- [The Tale of job.sh and the Snapshot](#the-tale-of-jobsh-and-the-snapshot)
- [Table of Contents](#table-of-contents)
- [Once Upon A Time](#once-upon-a-time)
- [When does your edit matter?](#when-does-your-edit-matter)
- [Best practice](#best-practice)

## Once Upon A Time
When you run sbatch job.sh, Slurm doesn't keep a live link to your file. Instead, at the moment of submission, it reads the script, copies its contents into the job record (spooled internally, typically under StateSaveLocation), and hands it a JobID. From that instant on, the job is frozen in time — it carries its own private copy of the script.

So here's what's happening in your case:

- Job 1 (running) — using the snapshot taken when you submitted it. Editing job.sh now does nothing to it. It's already off living its own life.
- Job 2 (pending) — same story. Even though it hasn't started yet, Slurm already took its snapshot at submission time, not at start time. It's sitting in the queue holding onto the old version of the script, waiting for resources — not waiting to "check" the file again.

## When does your edit matter?

Only for the next sbatch job.sh you run. Any submission after your edit will pick up the new snapshot. That's it.

## Best practice

If you want to change what's running or queued:

Cancel and resubmit: scancel <jobid> then sbatch job.sh — cleanest option.
Version your scripts: job_v1.sh, job_v2.sh, or better, tag by commit hash / date, so squeue output and your script history stay traceable to what actually ran.
Never edit-in-place while jobs are pending if you're debugging — you'll convince yourself the fix "should" apply and burn time confused when it doesn't.

Slurm treats submission as a commitment, not a promise to check back later.