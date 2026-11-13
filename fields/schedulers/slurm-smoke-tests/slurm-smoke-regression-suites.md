
# When Smoke Becomes a Fire Drill: SchedMD's Test Suite, ReFrame and the Baseline Rule

<!-- related-block -->
<div class="reading-time">9 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [The Cluster That Worked Perfectly and Remembered Nothing: a Two-Minute Slurm Smoke Test](/fields/schedulers/slurm-smoke-tests/slurm-smoke-control-plane.md)  ·  **See also:** [Does the Rulebook Still Work? Smoke-Testing QOS, Submit Rules and Preemption](/fields/schedulers/slurm-smoke-tests/slurm-smoke-policy.md), [The Changelog Nobody Reads: What Moved Between Slurm 23.11 and 26.05](/fields/schedulers/slurm-cluster-operations/slurm-version-changes.md), [The Morning After the Upgrade: Smoke Tests for the Change You Cannot Undo](/fields/schedulers/slurm-smoke-tests/slurm-smoke-after-upgrade.md), [Upgrading Slurm: The Order, the Window, and the Parts That Bite](/fields/schedulers/slurm-cluster-operations/slurm-upgrade-order.md)

</div>


> **Part 6 of [Slurm Smoke Tests](/fields/schedulers/slurm-smoke-tests/README.md).** The runs below were done on a two-node test cluster (Slurm 23.11.4 from the Ubuntu package, accounting on, a Lua submit script that requires `--time`, both `slurmd` daemons on one Ubuntu 24.04 machine with 2 CPUs). Both tools were run as an ordinary user. Each run is one run, on a deliberately small and unusual machine, so the pass and fail counts describe *this* cluster, not Slurm. The names and the story are invented. **Do not run either suite against a production cluster without reading its documentation first.** SchedMD's own README says its automatic-configuration mode "is not supported for use with local installations".

## Table of Contents

- [When Smoke Becomes a Fire Drill: SchedMD's Test Suite, ReFrame and the Baseline Rule](#when-smoke-becomes-a-fire-drill-schedmds-test-suite-reframe-and-the-baseline-rule)
  - [Table of Contents](#table-of-contents)
  - [The night before](#the-night-before)
  - [Smoke test or regression suite](#smoke-test-or-regression-suite)
  - [SchedMD's own suite](#schedmds-own-suite)
  - [ReFrame](#reframe)
  - [Which tool for which question](#which-tool-for-which-question)
  - [Version notes](#version-notes)
  - [Back to the night before](#back-to-the-night-before)
  - [References](#references)

---

## The night before

Priya has an upgrade on Saturday. On Friday evening she remembers that SchedMD ships a test suite, runs it against the cluster, and goes to get dinner. When she comes back the summary says 32 failures and 7 errors.

She does what anyone would do. She opens a ticket with her manager, drafts a message asking to postpone the upgrade, and starts reading the first failure. It says `Please set --time, jobs without one are not accepted`. That is not a Slurm problem. That is her own submit rule, from a Wednesday two months ago, refusing a test that did not know it existed.

A test suite is a very loud instrument. It only helps if you know what it sounded like before you changed anything.

---

## Smoke test or regression suite

| | Smoke test | Regression suite |
|---|---|---|
| Question | Is it basically working? | Did anything that used to work stop working? |
| Size | 6 to 10 checks | Hundreds of tests |
| Time | Seconds to minutes | Minutes to hours |
| Runs | After every change | Before and after the big ones: an upgrade, a new plugin |
| Where | Production, as a user | A test cluster, or production only with a lot of care |
| Failures mean | Something important is down | Something *differs*. Often your own policy |
| Examples | The [control-plane script](/fields/schedulers/slurm-smoke-tests/slurm-smoke-control-plane.md) | SchedMD's suite, ReFrame |

---

## SchedMD's own suite

The Slurm source tree has a `testsuite` directory. Its README describes three suites run through one command, `run-tests`: a **unit** suite, an **expect** suite of shell-style tests grouped by area, and a **python** suite run under pytest. The python suite has two modes:

- **Local-config mode** is for an existing installation. It aims to avoid changing "your Slurm configuration, accounting database configuration and system environment", and tests that need a different configuration are skipped.
- **Auto-config mode** reconfigures Slurm for each test, and is "intended to be used primarily within automated systems" such as containers.

Local-config is the only sensible mode for a real cluster, and the testsuite README notes that several tests say to use a throwaway database. Only the python suite was run here.

### How it was run

The source of the version in use was cloned (the tag for 23.11.4, so the tests match the daemons), given a four-line config, and run as an ordinary user:

```bash
git clone --depth 1 --branch slurm-23-11-4-1 https://github.com/SchedMD/slurm.git
cd slurm/testsuite
cat > testsuite.conf <<'EOF'
SlurmSourceDir=/path/to/slurm
SlurmBuildDir=/path/to/slurm
SlurmInstallDir=/usr
SlurmConfigDir=/etc/slurm
EOF
cd python
./run-tests-python -q
```

Two things were not in the README's steps. The wrapper starts `pytest-3`, which this machine did not have, so a symlink named `pytest-3` pointing at `pytest` had to be put on the `PATH`. And the tests need the `pexpect` Python package. The README has you copy `testsuite.conf.sample`, which the build generates. The source was not built here, so the four keys were written by hand. The README also says that if the test user is the `SlurmUser`, you should name an unprivileged user in `SlurmTestUser`. Running as a normal user avoided that.

### A first try

Three tests, chosen at random, ran in 0.11 seconds:

```text
tests/test_101_1.py::test_help SKIPPED (This test requires the test ...)
tests/test_102_2.py::test_usage PASSED
tests/test_103_1.py::test_usage PASSED
======================== 2 passed, 1 skipped in 0.11s =========================
```

### The whole python suite, twice

The python suite has 127 test files. The full run, as an ordinary user, with the site's Lua rule switched off and then on:

| Run | Passed | Failed | Errors | Skipped | Time |
|---|---|---|---|---|---|
| Lua submit script **off** | 54 | 9 | 5 | 361 | 2 min 42 s |
| Lua submit script **on** (requires `--time`) | 37 | 25 | 7 | 360 | 1 min 6 s |

The huge skip count is the local-config mode doing what the README says: most tests need a configuration this cluster does not have, so they are skipped, not failed. The second run's log has 46 lines containing `Please set --time`. The first has none.

The failing tests were saved to a file for each run, sorted, and compared:

```bash
grep -E '^(FAILED|ERROR) tests/' run.log | sed -E 's/ - .*//' | sort > run.fails
comm -13 baseline.fails after.fails      # the failures that are new
```

The result: 14 failures in the baseline, 32 with the policy on, **18 present only with the policy on, and none present only in the baseline**. Those 18 included `test_116_22.py::test_chdir`, `test_116_41.py::test_job_name` and `test_122_1.py::test_submit_and_cancel`. Only some of the messages were read, and the one for `test_122_1` quoted `sbatch --wrap "sleep 60"` being refused for lacking a time limit. The 46 mentions of the rule in the log make it the likely cause of the rest, but each was not checked. The suite did not find 18 broken things. It most probably found one rule, many times.

The 14 that remained with the policy off were not investigated. Their names suggest causes specific to this setup: four `test_version` tests, a failing `sgather --usage`, and tests that need more CPUs than a 2-CPU machine has. That is a guess from the test names, not a finding. It is the point of a baseline: those 14 are noise on this cluster, and they stay noise until something changes.

---

## ReFrame

[ReFrame](https://reframe-hpc.readthedocs.io/) is a framework for writing regression tests for HPC systems. A test is a Python class that says what to run and what a correct answer looks like; ReFrame generates the job script, submits it to the scheduler, waits, and checks the output. Its documentation says it does not assume a run succeeded: the test carries its own validation.

Installed into a virtualenv with `pip install reframe-hpc` (version 4.11.0 here), it needs two files. A settings file tells it how to reach Slurm:

```python
site_configuration = {
    'systems': [{
        'name': 'smoke', 'descr': 'two-node test cluster', 'hostnames': ['.*'],
        'partitions': [{
            'name': 'gpu', 'scheduler': 'slurm', 'launcher': 'srun',
            'access': ['-p gpu'], 'environs': ['builtin'], 'max_jobs': 4,
        }],
    }],
    'environments': [{'name': 'builtin', 'cc': 'cc', 'cxx': '', 'ftn': ''}],
    'logging': [{'handlers': [{'type': 'stream', 'name': 'stdout', 'level': 'info', 'format': '%(message)s'}]}],
}
```

And a test file holds the checks. One passes on purpose and one fails on purpose:

```python
import reframe as rfm
import reframe.utility.sanity as sn
from reframe.core.builtins import sanity_function


@rfm.simple_test
class OneTaskPerNode(rfm.RunOnlyRegressionTest):
    """A task starts on both nodes and reports its Slurm node name."""
    valid_systems = ['*']
    valid_prog_environs = ['*']
    num_tasks = 2
    num_tasks_per_node = 1
    time_limit = '2m'
    executable = 'bash'
    executable_opts = ['-c', "'echo node=$SLURMD_NODENAME'"]

    @sanity_function
    def two_nodes_answered(self):
        # one task per node, two tasks: two matching lines mean two nodes answered
        return sn.assert_eq(sn.count(sn.extractall(r'node=(\S+)', self.stdout, 1)), 2)


@rfm.simple_test
class ThisOneShouldFail(rfm.RunOnlyRegressionTest):
    """Deliberately wrong expectation, to see what a failure looks like."""
    valid_systems = ['*']
    valid_prog_environs = ['*']
    time_limit = '1m'
    executable = 'echo'
    executable_opts = ['hello']

    @sanity_function
    def never(self):
        return sn.assert_found(r'goodbye', self.stdout)
```

```bash
reframe -C settings.py -c smoke_checks.py -r --prefix /shared/path/rf
```

```text
[ RUN     ] OneTaskPerNode /b83630ca @smoke:gpu+builtin
[ RUN     ] ThisOneShouldFail /5558de74 @smoke:gpu+builtin
[       OK ] (1/2) OneTaskPerNode /b83630ca @smoke:gpu+builtin
[     FAIL ] (2/2) ThisOneShouldFail /5558de74 @smoke:gpu+builtin
...
  * Failing phase: sanity
  * Reason: sanity error: pattern 'goodbye' not found in 'rfm_job.out'
```

Behind the scenes it wrote this job script and submitted it with `sbatch`:

```bash
#!/bin/bash
#SBATCH --job-name="rfm_OneTaskPerNode"
#SBATCH --ntasks=2
#SBATCH --ntasks-per-node=1
#SBATCH --output=rfm_job.out
#SBATCH --error=rfm_job.err
#SBATCH --time=0:2:0
#SBATCH -p gpu
srun bash -c 'echo node=$SLURMD_NODENAME'
```

Note the `--time` line: ReFrame set it from `time_limit`, which is why it worked on a cluster that refuses jobs without one. Note also what `sacct` said about the failing test's job: `COMPLETED`. The job ran perfectly. The *answer* was wrong, and only the framework that knew what the right answer was could tell. A smoke test that only looks at job states would have passed it.

Two practical points come from the ReFrame documentation and were not tested on a second setup. Its stage and output directories must live on storage shared with the compute nodes, so pass `--prefix` pointing there. And its Slurm backend gets job state from `sacct`, so it needs accounting enabled; with accounting off, its `squeue`-based backend is the alternative.

---

## Which tool for which question

| Question | Tool |
|---|---|
| "Did my change break the basics?" | The [control-plane smoke test](/fields/schedulers/slurm-smoke-tests/slurm-smoke-control-plane.md), every time |
| "Do my rules still do what I mean?" | The [policy smoke test](/fields/schedulers/slurm-smoke-tests/slurm-smoke-policy.md) |
| "Did the upgrade change behaviour I did not know I relied on?" | SchedMD's suite, on a test cluster, before and after, with a baseline |
| "Does *my site's* software, filesystem and network still work for *my* users?" | ReFrame (or similar) tests written for your own workloads, so they can also check performance |

SchedMD's suite tests Slurm. It knows nothing about your filesystem, your container runtime or your GPU drivers. ReFrame tests what you teach it. Neither replaces the smoke test, and the smoke test replaces neither.

---

## Version notes

The suite was run on 23.11.4 only, with that version's tests. Newer source trees have more tests, and the layout of `testsuite` may change, so read the README of the version you run. The unit and expect suites were not run at all. One thing worth knowing: the suite found the Lua policy in one run, and the [changelog](/fields/schedulers/slurm-cluster-operations/slurm-version-changes.md) lists 26.05 as logging a stack trace for runtime errors in a submit script, which makes a policy failure inside a test easier to read.

---

## Back to the night before

Replay Friday with the baseline rule. Last month, on a quiet evening, Priya ran the suite once and saved the list of failures: 14 of them, all things she could explain or at least recognise. She wrote the file into the cluster's runbook with the date and the Slurm version.

On Friday she runs it again, as the first step of the upgrade rehearsal on the test cluster, and compares. `comm -13` prints 18 names, and she reads the first one: `Please set --time`. She switches the time-limit rule off on the test cluster for the run, reruns, and the 18 disappear. The Saturday upgrade goes ahead. After it, she runs the suite one more time and compares with the same file. Nothing is new.

**Takeaway:** a regression suite finds *differences*, not faults, so run it on a test cluster, save the list of failures as a baseline before the change, and compare after (new failures are your findings, old ones are noise), and use ReFrame when the question is whether your own site's workloads still work, because it can check the answer and not only the job state.

**Next:** back to the [series overview](/fields/schedulers/slurm-smoke-tests/README.md), which has a one-page checklist that ties the six together.

---

## References

- [SchedMD Slurm testsuite README](https://third-party-mirror.googlesource.com/SchedMD/slurm/+/refs/heads/master/testsuite/README) (`run-tests`, the unit, expect and python suites, `testsuite.conf`)
- [SchedMD Slurm python testsuite README](https://third-party-mirror.googlesource.com/SchedMD/slurm/+/refs/heads/master/testsuite/python/README) (local-config and auto-config modes)
- [ReFrame tutorial](https://reframe-hpc.readthedocs.io/en/stable/tutorial.html) (tests as Python classes, the `slurm` scheduler backend)
- [Slurm: Upgrade Guide](https://slurm.schedmd.com/upgrades.html) ("Test key functionality")
