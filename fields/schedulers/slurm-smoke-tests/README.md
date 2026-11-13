
# Slurm Smoke Tests: Does It Still Work?

A cluster can pass every glance and still be broken: `sinfo` shows a tidy table while the accounting daemon is down, a rule refuses every monitoring job, or a node reports `idle` with half its cores. A smoke test is the short list of things that must all work, run every time something changes.

Each page opens with a failure, then builds the check that would have caught it. Every script was run on a two-node test cluster (Slurm 23.11.4), against failures injected on purpose. SchedMD does not define a "smoke test", so the series synthesises what its admin, troubleshooting and upgrade guides say to verify, and adds what the tests turned up.

The pages stand alone. Read part 1 first if you are new to this; the rest each name what they build on.

---

## Contents

| File | Description |
|---|---|
| [1. The Cluster That Worked Perfectly and Remembered Nothing](/fields/schedulers/slurm-smoke-tests/slurm-smoke-control-plane.md) | A six-check, two-minute smoke test (MUNGE, controller, nodes, `srun`, `sbatch`, `sacct`) as one script with three outcomes, tested against four failures |
| [2. Measure Twice, Reconfigure Once](/fields/schedulers/slurm-smoke-tests/slurm-smoke-config-change.md) | What a bad `slurm.conf` does, and the dry runs that catch it: a snapshot diff, `sbatch --test-only`, a canary partition |
| [3. The Morning After the Upgrade](/fields/schedulers/slurm-smoke-tests/slurm-smoke-after-upgrade.md) | A backup you have restored, versions on every node, a snapshot comparison, and why you cannot undo an upgrade |
| [4. Does the Rulebook Still Work?](/fields/schedulers/slurm-smoke-tests/slurm-smoke-policy.md) | A two-stage policy test: routing and refusals with no resources, then a real preemption drill |
| [5. Back From the Repair Shop](/fields/schedulers/slurm-smoke-tests/slurm-smoke-node-readiness.md) | Why `idle` proves little, a hardware-versus-config check, and a reservation fence for a probe job |
| [6. When Smoke Becomes a Fire Drill](/fields/schedulers/slurm-smoke-tests/slurm-smoke-regression-suites.md) | SchedMD's test suite and ReFrame, and the baseline rule |

---

## Which check, when

| What just happened | Run |
|---|---|
| Any change at all | [Part 1](/fields/schedulers/slurm-smoke-tests/slurm-smoke-control-plane.md): the control-plane script, as an ordinary user |
| Editing `slurm.conf` | [Part 2](/fields/schedulers/slurm-smoke-tests/slurm-smoke-config-change.md): snapshot before and after, `--test-only`, canary partition |
| An upgrade | [Part 3](/fields/schedulers/slurm-smoke-tests/slurm-smoke-after-upgrade.md): proven backup first, then versions, part 1, snapshot diff |
| A change to QOS, limits, the submit script or preemption | [Part 4](/fields/schedulers/slurm-smoke-tests/slurm-smoke-policy.md): stage 1 always, stage 2 for preemption changes |
| A node returning from repair or reboot | [Part 5](/fields/schedulers/slurm-smoke-tests/slurm-smoke-node-readiness.md): hardware comparison, then a probe job inside a fence |
| A big change on a test cluster | [Part 6](/fields/schedulers/slurm-smoke-tests/slurm-smoke-regression-suites.md): a regression suite, compared with a baseline |

---

## What the tests turned up

The surprises are the reason the checks look the way they do:

- A dead `slurmd` is invisible to `sinfo` for a while, so only launching a task on every node finds it quickly.
- With `slurmdbd` stopped, jobs run perfectly and nothing is recorded.
- A drained node and a full cluster give `srun` the same "busy" message, and a dead node can look like a full cluster to `sbatch`, so a smoke test needs a third outcome: inconclusive.
- A typo in `slurm.conf` is caught by `scontrol` before the controller sees it, but a partition naming a missing node survives a reconfigure and stops the next restart from working.
- A submit rule that requires `--time` broke the first draft of the smoke test, and, most probably, 18 failures in SchedMD's suite.
- With `config_overrides`, a node with half its configured CPUs shows `idle`. Without it, Slurm marks the node `inval`.
- A drained node cannot run a job even inside a reservation, so a probe needs the reservation first and the resume second.

---

## What was not tested

No GPU commands were run (the test cluster has none). No upgrade between versions was performed. SchedMD's unit and expect suites were not run. NHC was not installed. Each page says so where it matters.

---

## Related pages

- [Why is my job still pending?](/fields/schedulers/slurm-pending-jobs/README.md): the reason codes behind a smoke test's `WAIT`.
- [Autopsy of a job: `sacct`](/fields/schedulers/slurm-sacct-job-forensics.md): reading what the accounting check recorded.
- [Dying Politely: preemption and signals](/fields/schedulers/slurm-preemption/README.md): the policy that part 4 tests.
- [Cluster operations](/fields/schedulers/slurm-cluster-operations/README.md): upgrade order, reboots and reservations around parts 3 and 5.
- [When a GPU falls off the bus](/fields/schedulers/slurm-ai-clusters/gpu-health-checks.md): the health-check program that part 5 points to.
