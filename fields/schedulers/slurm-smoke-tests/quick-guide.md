
<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/fields/">Fields</a> / <a href="#/fields/schedulers/">Schedulers</a> / <a href="#/fields/schedulers/slurm-smoke-tests/">Slurm Smoke Tests: Does It Still Work?</a></nav>

# Check That Slurm Still Works After a Change

<!-- related-block -->
<div class="reading-time">Intermediate · Guide · 6 min read · Updated 23 Nov 2026</div>
<!-- related-block -->
<div class="tag-chips"><a class="chip" href="#/.docs/generated/explore/tags/hpc">hpc</a> <a class="chip" href="#/.docs/generated/explore/tags/quick">quick</a> <a class="chip" href="#/.docs/generated/explore/tags/slurm">slurm</a></div>


> **Quick guide for** the [Slurm smoke tests](/fields/schedulers/slurm-smoke-tests/README.md).
> Use it right after a config change, an upgrade, a rule edit or a node repair. You end with a pass, a fail, or a clear "inconclusive".

## Before you start

- Run the checks as an ordinary user who may submit jobs, not as root.
- Get the scripts from [`smoke-scripts/`](/fields/schedulers/slurm-smoke-tests/smoke-scripts/slurm-smoke.sh): `slurm-smoke.sh`, `slurm-snapshot.sh`, `slurm-policy-smoke.sh`, `node-fit.sh`, `slurm-db-backup-check.sh`.
- If a submit rule requires `--time`, the test jobs need one too (`SMOKE_TIME`).

---

## Part 1: After any change, a two-minute control-plane check

```bash
SMOKE_PARTITION=gpu ./slurm-smoke.sh
```

**Expect:** six `PASS` lines (munge, ping, nodes, srun, sbatch, sacct) and `ALL PASS`, exit status `0`.
**If not:** exit `1` is a failure, so read the `FAIL` line. Exit `2` is `INCONCLUSIVE`: the cluster was busy, so run it again.

---

## Part 2: Before and after a `slurm.conf` change

1. Save the state before.

   ```bash
   ./slurm-snapshot.sh /tmp/before
   ```

   **Expect:** a snapshot folder.
   **If not:** do not change anything yet.

2. Dry-run a job against the new rules.

   ```bash
   sbatch --test-only job.sh
   ```

   **Expect:** `sbatch: Job 103 to start at ... in partition gpu`.
   **If not:** the error names the rule, such as `Please set --time` or `invalid partition specified`.

3. Try the change on a hidden canary partition first.

   ```bash
   SMOKE_PARTITION=canary ./slurm-smoke.sh
   ```

   **Expect:** `ALL PASS` on one node.
   **If not:** fix the partition before you touch the real ones.

4. Reconfigure, then check.

   ```bash
   scontrol reconfigure
   ./slurm-snapshot.sh /tmp/after
   diff -ru /tmp/before /tmp/after
   ```

   **Expect:** only the differences you intended, and `ALL PASS` from the smoke test.
   **If not:** any error from `scontrol reconfigure` is a failure, so look at the controller log for `error:` lines.

**Don't:** trust a failed reconfigure. A partition naming a missing node survives it and stops the next restart.

---

## Part 3: After an upgrade

1. Restore the backup into a scratch database before the upgrade. **Expect:** `BACKUP RESTORES` from `slurm-db-backup-check.sh`.
   **If not:** you do not have a backup yet.
2. Take `./slurm-snapshot.sh /root/before-upgrade`.
3. After the daemons are back, check every version.

   ```bash
   slurmctld -V; slurmdbd -V; slurmd -V; sinfo -V
   scontrol show node -o | grep -o 'NodeName=[^ ]*\|Version=[^ ]*' | paste - -
   ```

   **Expect:** the target version on every line.
   **If not:** a node still runs old software.
4. Run `./slurm-smoke.sh`, then `sacct` for an old job. **Expect:** `ALL PASS`, and the old job is still readable.

**Don't:** expect to roll back once a daemon has started. Also use `sacctmgr ping` only on 24.11 and newer.

---

## Part 4: After a rule, QOS or preemption change

```bash
slurm-policy-smoke.sh
```

**Expect:** `7 passed, 0 failed`: no `--qos` becomes `low`, `--qos=high` becomes `high_physics`, a job without `--time` is refused, then a high job evicts a low one and the low job restarts.
**If not:** the failing line says which layer broke.

| Failing check | Look at |
|---|---|
| `no --qos becomes low` | The submit script is not loaded or the default routing changed |
| `high job got the node` | `PreemptType`, `PreemptMode` or the QOS `Preempt=` list |
| `low job was requeued` | The victim mode, `JobRequeue` or `--requeue` |

**Run:** stage 1 after any QOS edit or reconfigure, stage 2 after changing `PreemptType`.

---

## Part 5: A node back from repair

1. Compare the hardware with the promise.

   ```bash
   slurmd -C
   node-fit.sh
   ```

   **Expect:** `PASS cpus`, `PASS memory` and `PASS state`.
   **If not:** `FAIL cpus hardware 2, configured 4` means the node is not what `slurm.conf` says.
2. Fence the node and probe it.

   ```bash
   scontrol update NodeName=node2 State=DRAIN Reason="returning from repair"
   scontrol create reservation ReservationName=probe StartTime=now Duration=10 \
       Nodes=node2 Users=tester Flags=MAINT
   scontrol update NodeName=node2 State=RESUME
   sbatch -w node2 --reservation=probe -t 1 --wrap='hostname; echo SLURMD_NODENAME=$SLURMD_NODENAME'
   ```

   **Expect:** the job prints `SLURMD_NODENAME=node2`.
   **If not:** the job pends with `ReqNodeNotAvail`, so check the reservation.
3. Remove the fence.

   ```bash
   scontrol delete ReservationName=probe
   ```

**Don't:** trust `idle`. It only means `slurmd` registered. With `config_overrides` on, the controller believes the file, not the hardware.

---

## Part 6: Before and after a big change, a regression suite

```bash
grep -E '^(FAILED|ERROR) tests/' run.log | sed -E 's/ - .*//' | sort > run.fails
comm -13 baseline.fails after.fails
```

**Expect:** no output, meaning no new failures.
**If not:** every line is a new finding. Old failures are noise.

**Run it:** on a test cluster, with a baseline saved before the change.

---

## Tips and tricks

- Keep every snapshot. When something misbehaves on Thursday, "what changed since Monday" is a `diff`.
- A canary partition also hosts the scheduled smoke test.
- Give the probe reservation `Duration=10`. If you forget the last step, the fence expires on its own.
- Let a health check do the routine part: `HealthCheckProgram=/usr/sbin/nhc` with `HealthCheckInterval=300`.
- Wait several seconds after a daemon restart before running the smoke test. A run two seconds after reported busy nodes, and one six seconds after did not.
- Give the test job `-t`, or set `SMOKE_TIME`, if a submit rule requires `--time`.

## Warnings

> [!WARNING]
> No Slurm upgrade was performed while writing these pages. The upgrade checks are untested end to end.

- With `slurmdbd` stopped, jobs run perfectly and nothing is recorded. Only `sacct` shows it.
- A dead `slurmd` is invisible to `sinfo` for a while. Only launching a task on every node finds it quickly.
- A drained node cannot run a job even inside a reservation, so create the reservation first and resume second.
- With `config_overrides`, a node with half its configured CPUs shows `idle`.
- A failed `scontrol reconfigure` is a warning with a delay on it.

## If it fails

| What you see | Likely cause | Fix |
|---|---|---|
| `FAIL srun`, but `nodes` passed | A dead `slurmd` the controller has not noticed | Restart `slurmd`, run again |
| `FAIL sacct`, jobs still run | `slurmdbd` is down | Start it |
| `WAIT` and `INCONCLUSIVE` | The cluster is busy | Run again later |
| `Please set --time, jobs without one are not accepted` | A submit rule needs a time limit | Set `SMOKE_TIME` or `-t` |
| `ExitCode 0:53`, `Slurmd could not connect IO` | The directory is not writable | Run from a writable directory |

**Why it works:** [control plane](/fields/schedulers/slurm-smoke-tests/slurm-smoke-control-plane.md), [config change](/fields/schedulers/slurm-smoke-tests/slurm-smoke-config-change.md), [after an upgrade](/fields/schedulers/slurm-smoke-tests/slurm-smoke-after-upgrade.md), [policy](/fields/schedulers/slurm-smoke-tests/slurm-smoke-policy.md), [node readiness](/fields/schedulers/slurm-smoke-tests/slurm-smoke-node-readiness.md), [regression suites](/fields/schedulers/slurm-smoke-tests/slurm-smoke-regression-suites.md). Next: [preemption](/fields/schedulers/slurm-preemption/README.md).

<!-- related-block -->
<div class="see-also">

**See also**

- [Back From the Repair Shop: Is This Node Fit to Return to Service?](/fields/schedulers/slurm-smoke-tests/slurm-smoke-node-readiness.md) — Why idle does not mean a node is healthy, what Slurm does when hardware and slurm.conf disagree (and how config_overrides hides it), and a reservation fence for a probe job.
- [Does the Rulebook Still Work? Smoke-Testing QOS, Submit Rules and Preemption](/fields/schedulers/slurm-smoke-tests/slurm-smoke-policy.md) — A two-stage smoke test for QOS, submit rules and preemption: routing and refusals with no resources, then a real eviction and requeue, with a full script and its output.
- [Measure Twice, Reconfigure Once: Smoke-Testing a slurm.conf Change](/fields/schedulers/slurm-smoke-tests/slurm-smoke-config-change.md) — What a bad slurm.conf does (typo, partition naming a missing node) and the dry runs that catch it first: a snapshot diff, sbatch --test-only and a canary partition.
- [The Cluster That Worked Perfectly and Remembered Nothing: a Two-Minute Slurm Smoke Test](/fields/schedulers/slurm-smoke-tests/slurm-smoke-control-plane.md) — A six-check, two-minute Slurm smoke test (MUNGE, controller, nodes, srun, sbatch, sacct) as one script with three outcomes, tested against four injected failures and a busy cluster.
- [The Morning After the Upgrade: Smoke Tests for the Change You Cannot Undo](/fields/schedulers/slurm-smoke-tests/slurm-smoke-after-upgrade.md) — What to check around a Slurm upgrade: a backup proven by restoring it, versions on every node, a before/after snapshot, the control-plane smoke test, and why downgrading is not supported.
- [When Smoke Becomes a Fire Drill: SchedMD's Test Suite, ReFrame and the Baseline Rule](/fields/schedulers/slurm-smoke-tests/slurm-smoke-regression-suites.md) — What SchedMD's test suite and ReFrame do, how both were run against a live test cluster, and why results only mean something against a baseline taken before the change.

</div>
