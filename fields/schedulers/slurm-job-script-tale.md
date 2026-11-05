
# The Tale of a Slurm Job Script: Submission Is a Commitment, Not a Promise

<!-- related-block -->
<div class="reading-time">11 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [Schedulers: The Traffic Controller Nobody Thanks Until It Breaks](/fields/schedulers/slurm-intro.md)  ·  **See also:** [Backfill Tuning: The Planner That Can Only See One Day Ahead](/fields/schedulers/slurm-backfill-tuning.md), [SlurmdSpoolDir Is Full: The Drain That Is Not About the Spool Directory](/fields/schedulers/slurm-spool-dir-full.md), [slurmstepd: The Small Daemon That Actually Runs Your Job](/fields/schedulers/slurm-slurmstepd.md)

</div>


> **Part of the [schedulers](/fields/schedulers/slurm-intro.md) directory.** The story below is the original tale. The sections after it check its claims against the Slurm man pages, SchedMD support tickets and the slurm-users list, and add what the story leaves out. The commands were not run on a live cluster for this page, so try them with a short test job first. The sources date from 2019 to 2023, and the accounting flags in the last sections need Slurm 21.08 or newer.

## Table of Contents

- [The Tale of a Slurm Job Script: Submission Is a Commitment, Not a Promise](#the-tale-of-a-slurm-job-script-submission-is-a-commitment-not-a-promise)
  - [Table of Contents](#table-of-contents)
  - [The tale](#the-tale)
  - [Where the snapshot actually lives](#where-the-snapshot-actually-lives)
  - [Frozen in time? Only the script and its environment](#frozen-in-time-only-the-script-and-its-environment)
  - [How sbatch reads the script](#how-sbatch-reads-the-script)
  - [Peeking at the frozen copy](#peeking-at-the-frozen-copy)
  - [Changing your mind without starting over](#changing-your-mind-without-starting-over)
  - [Best practice](#best-practice)
  - [Making runs traceable](#making-runs-traceable)
  - [The afterlife of a script](#the-afterlife-of-a-script)
  - [Cheat sheet](#cheat-sheet)
  - [References](#references)

* * *

## The tale

You fixed the bug in `job.sh` at 18:02. Job 2 was still pending, so you assumed it would pick up the fix. At 03:00 it started, ran the old script, and burned the night on the bug you'd already fixed. Here's why.

When you run `sbatch job.sh`, Slurm doesn't keep a live link to your file. Instead, at the moment of submission, it reads the script, copies its contents into the job record (spooled internally, typically under `StateSaveLocation`), and hands it a JobID. From that instant on, the job is frozen in time — it carries its own private copy of the script.

So here's what's happening in your case:

- **Job 1 (running)** — using the snapshot taken when you submitted it. Editing `job.sh` now does nothing to it. It's already off living its own life.
- **Job 2 (pending)** — same story. Even though it hasn't started yet, Slurm already took its snapshot at submission time, not at start time. It's sitting in the queue holding onto the old version of the script, waiting for resources — not waiting to "check" the file again.

**When does your edit matter?**

Only for the next `sbatch job.sh` you run. Any submission after your edit will pick up the new snapshot. That's it.

> [!NOTE]
> The core of the tale checks out. The sections below make the picture more exact in four places: where the copy lives, what "frozen" covers, which options exist besides cancelling, and what the versioning advice can and cannot do.

* * *

## Where the snapshot actually lives

"Typically under `StateSaveLocation`" is right, and it can be made precise. Three sources agree:

- **The layout.** A SchedMD commit message describes a `hash.#` subdirectory based on the last digit of the job ID, added so file systems with limited files per directory can cope with many jobs. A support ticket then shows the path in full, `<StateSaveLocation>/hash.6/job.25596/script`, and a log from another ticket shows the same pattern with `hash.4/job.33767454/script`.
- **There are two files, not one.** Tools that archive jobs read both `script` and `environment` from that job directory, and the ticket about a controller that would not start mentions the script file and the environment file both being empty.
- **The controller does the keeping, not your file system.** A slurm-users reply explains the flow: `sbatch` submits the script over the network to `slurmctld`, which stores it in `StateSaveLocation` and sends it to `slurmd` at dispatch time. The node then stores it under its own `SlurmdSpoolDir`. So the controller host never needs to see your home directory.

```
sbatch ──(network)──> slurmctld ──> <StateSaveLocation>/hash.N/job.<id>/{script,environment}
                          │
                          └─(at dispatch)──> slurmd ──> <SlurmdSpoolDir>/job<id>/slurm_script
```

Two consequences worth knowing:

- **A damaged state directory can be fatal for a job.** In a SchedMD ticket, a zero-length `script` file made `slurmctld` log that it could not find the batch script and stop with "Check file system serving StateSaveLocation as that directory may be missing or corrupted". That is why the [upgrade page](/fields/schedulers/slurm-upgrade-order.md) backs this directory up before anything else.
- **Arrays share one copy.** A SchedMD talk on cluster field notes points out that array jobs cost far less than many individual jobs, because only one job script and environment file is kept for the whole array.

On the node side, the [spool directory page](/fields/schedulers/slurm-spool-dir-full.md) explains why a full disk there drains the node: `slurmd` cannot write the script it is about to run.

* * *

## Frozen in time? Only the script and its environment

"Frozen in time" is accurate for the script text. It is too strong for everything the script touches. Slurm freezes a small set of things and leaves the rest of your world alive:

| What | Frozen at submit? | Notes |
|---|---|---|
| The script text | **Yes** | The `script` file above |
| Your `#SBATCH` options | **Yes** | Resolved into the job record |
| Your environment variables | **Yes** | The `environment` file. This includes loaded modules, because they live in variables |
| Your working directory | **Yes** | The job starts where you ran `sbatch`, unless `--chdir` says otherwise |
| `train.py`, helper scripts, configs, data | **No** | Read at run time, from whatever is on disk then |

The `sbatch` man page is explicit about the last row: other than the batch script itself, Slurm does no movement of user files. A cluster guide from VSC spells out the environment row: by default `sbatch` copies the environment it sees, so every module loaded when you submitted is loaded in the job.

Now go back to your two jobs, and suppose `job.sh` contains `python train.py`:

| You edit | Job 1 (running) | Job 2 (pending) |
|---|---|---|
| `job.sh` | Unchanged | Unchanged |
| `train.py`, before the job reaches it | **Sees the new code** | **Sees the new code** |
| Your shell's loaded modules | Unchanged | Unchanged |

That is the trap behind "the old script with the new code". A pending job that holds the old `--lr 1.0` and runs a freshly fixed `train.py` is a combination nobody tested. Even a running job can pick up a change, if the script later runs `source config.sh` or the Python process imports a module it has not loaded yet.

* * *

## How sbatch reads the script

Three rules from the man page explain surprises at submission time:

- **Directives stop at the first command.** After the first non-comment, non-whitespace line, `sbatch` processes no more `#SBATCH` lines. A directive below a command is ignored as an ordinary comment.
- **Directives are literal text.** They are read by Slurm, not the shell, so `#SBATCH --output=$HOME/out.txt` does not expand `$HOME`. Filename patterns such as `%j` are Slurm's own and do work.
- **Precedence.** The man page says `SBATCH_*` environment variables override options in the script, and command-line options override those variables. A leftover `SBATCH_PARTITION` in a `.bashrc` can quietly outvote the script.

```bash
#!/bin/bash
#SBATCH --job-name=train      # read
module load python/3.11       # first command: directive block ends here
#SBATCH --time=12:00:00       # IGNORED
```

If a job came out with the wrong limit or partition, check `scontrol show job <id>` first, then `env | grep ^SBATCH_`.

* * *

## Peeking at the frozen copy

You can ask Slurm for the exact script it holds:

```bash
scontrol write batch_script <jobid>            # writes slurm-<jobid>.sh
scontrol write batch_script <jobid> held.sh    # or a name you choose
scontrol write batch_script <jobid> -          # to stdout
diff job.sh held.sh                            # what did Slurm freeze?
```

From a SchedMD ticket: the file defaults to `slurm-<job_id>.sh`, `-` writes to stdout, and only an admin, an operator or the job's owner can retrieve it. It works while the controller still holds the job. A finished job's record is purged after `MinJobAge` seconds, which the `sbatch` man page mentions when it explains dependencies on finished jobs.

Admins have a second route, the same ticket notes: copy `<StateSaveLocation>/hash.N/job.<id>/script` directly.

* * *

## Changing your mind without starting over

Cancel and resubmit is the only way to change the **script**. For some other changes, though, it is not the only option, and it costs you your place in the queue (the job's age restarts, which is my inference from how the age factor works rather than a documented statement).

| You want to change | While pending? | How |
|---|---|---|
| Time limit, partition, QOS, account, dependency, name | Often | `scontrol update JobId=<id> ...`. The `sbatch` man page notes, for instance, that the account can be changed after submission. Which fields a regular user may change is site policy |
| Pause a job without losing it | Yes | `scontrol hold <id>`, then `scontrol release <id>` |
| The script text | **No** | Cancel, edit, resubmit |
| The captured environment | **No** | Resubmit from the right environment |

Two related cases:

- **Requeue.** A requeued job returns to pending and runs again. Since the controller holds the script, I would expect the original text to run even if you have edited the file since, but I found no source that says so. Test it with a short job. The [preemption page](/fields/schedulers/slurm-preemption-requeue-signals.md) covers writing scripts that survive requeue.
- **Dependent jobs.** If `job2` was submitted with `--dependency=afterok:<job1>`, it carries its own snapshot taken when *it* was submitted. Fixing `job.sh` and resubmitting job 1 does not update job 2.

* * *

## Best practice

If you want to change what's running or queued:

**Cancel and resubmit:** `scancel` then `sbatch job.sh` — cleanest option.

**Version your scripts:** `job_v1.sh`, `job_v2.sh`, or better, tag by commit hash / date, so `squeue` output and your script history stay traceable to what actually ran.

**Never edit-in-place while jobs are pending if you're debugging** — you'll convince yourself the fix "should" apply and burn time confused when it doesn't.

Slurm treats submission as a commitment, not a promise to check back later.

* * *

## Making runs traceable

The versioning advice is right, with one catch: `squeue` shows the job **name**, not the script file. A file called `job_v2.sh` does not show up anywhere unless you carry the version into something Slurm records.

| Where | Shows the version? |
|---|---|
| `squeue`, `sacct` job name | Yes, if you pass it: `sbatch --job-name=train-a1b2c3d job.sh` |
| `--comment` | Yes, but `sacct` only keeps it if `AccountingStoreFlags` includes `job_comment` (the configuration tool lists `job_comment` among the flags) |
| `scontrol show job` → `Command=` | Only the **path** of the script, not its content. After an edit, it points at a file that no longer matches what ran, which is the complaint in a 2021 slurm-users thread |

A pattern that pins both the script and the code to a commit:

```bash
REV=$(git rev-parse --short HEAD)
sbatch --job-name="train-$REV" --comment="commit $REV" job.sh
```

And a self-documenting habit, adapted from the same slurm-users thread, which describes capturing the original script with each run. Put this at the top of the script body so every run keeps its own record (the filenames are my own):

```bash
OUT=runs/$SLURM_JOB_ID
mkdir -p "$OUT"
scontrol write batch_script "$SLURM_JOB_ID" "$OUT/script.sh"
env | sort > "$OUT/env.txt"          # check for secrets before sharing
git rev-parse HEAD > "$OUT/commit.txt" 2>/dev/null
module list > "$OUT/modules.txt" 2>&1
```

* * *

## The afterlife of a script

After the job ends and the controller purges its record, can you still get the script back?

- **By default, no.** A 2021 slurm-users reply says the accounting database stores neither the job's `Command` nor the script.
- **Since 21.08, optionally yes.** The release notes add `AccountingStoreFlags=job_script` to store the batch script and `job_env` to store the environment variables.

With the flags on:

```bash
sacct -j <jobid> --batch-script      # or -B
sacct -j <jobid> --env-vars          # needs job_env; -j is required
```

The man page says `-B` prints `NONE` when the job had no script. SchedMD's SC21 slides show the idea with a wrapped `sleep` job whose generated `#!/bin/sh` script comes back through `sacct --batch-script`.

Two cautions that are my own, not from the docs.

> [!WARNING]
> Don't switch on `job_env` cluster-wide first. Scripts and environments can hold secrets, so think about who can read the accounting database before enabling `job_env`. And storing them grows the database, which makes dumps and schema conversions slower. Safe path: enable `job_script` alone first, check database size after a week of normal load, then decide on `job_env`. Rollback is removing the flag from `AccountingStoreFlags` and reconfiguring. Rows already stored probably stay in the database (my inference, untested).

* * *

## Cheat sheet

```
sbatch freezes   script text + options + environment (two files in StateSaveLocation) + cwd
sbatch ignores   code, configs, data: read live at run time, by running AND pending jobs
read it back     scontrol write batch_script <id> [file|-]    (owner or admin, while the record exists)
change it        scontrol update (some fields) | hold/release | script change = cancel + resubmit
precedence       command line > SBATCH_* env vars > #SBATCH lines (which stop at the first command)
trace it         --job-name / --comment (job_comment flag) with a commit hash; Command= is only a path
afterwards       AccountingStoreFlags=job_script,job_env (21.08+) then sacct -B / --env-vars -j <id>
```

**Takeaway:** Submission freezes the letter and its envelope (script, options, environment). Everything the letter points to is still out in the world.

**Next:** [slurmstepd: The Small Daemon That Actually Runs Your Job](/fields/schedulers/slurm-slurmstepd.md)

* * *

## References

- [Slurm: sbatch man page](https://man.archlinux.org/man/sbatch.1.en.txt) (directive parsing, exit after transfer, no movement of user files, account changes)
- [Slurm: sbatch man page, Ubuntu copy (MinJobAge and dependencies)](https://manpages.ubuntu.com/manpages/noble/man1/sbatch.1.html)
- [VSC documentation: submission of job scripts (environment copied by default)](https://docs.vscentrum.be/compute/jobs/job_submission.html)
- [SchedMD ticket 7609: storing job scripts in the database (`scontrol write batch_script`, StateSaveLocation path)](https://support.schedmd.com/show_bug.cgi?id=7609)
- [SchedMD ticket 7757: slurmctld will not start (zero-length script and environment files)](https://support.schedmd.com/show_bug.cgi?id=7757)
- [SchedMD commit: "Add subdirectory for job script/env files" (hash.# layout)](https://earth.bsc.es/gitlab/mgimenez/ces_slurm_simulator/-/commit/d4156ab5572dcab8b805ed37c26b8bde784a2ad9)
- [slurm-users: sbatch submits scripts to slurmctld, which stores them in StateSaveLocation (2022)](https://lists.schedmd.com/pipermail/slurm-users/2022-February/008417.html)
- [SchedMD SLUG 2023: Field Notes 7 (array jobs store one script and environment)](https://Slurm.schedmd.com/SLUG23/Field-Notes-7.pdf)
- [slurm-users: Get original script of a job (2021)](https://groups.google.com/g/slurm-users/c/lmg6_5Lq9UY)
- [Slurm 21.08 release notes (job_script and job_env flags)](https://github.com/SchedMD/slurm/blob/slurm-21-08-8-2/RELEASE_NOTES)
- [Slurm: sacct man page (`--batch-script`, `--env-vars`)](https://manpages.ubuntu.com/manpages/kinetic/man1/sacct.1.html)
- [Slurm: configuration tool (AccountingStoreFlags options)](https://slurm.schedmd.com/configurator.html)
- [SchedMD SC21 BoF slides: storing batch scripts in SlurmDBD](https://Slurm.schedmd.com/SC21/BoF.pdf)
