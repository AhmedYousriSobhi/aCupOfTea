
<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/fields/">Fields</a> / <a href="#/fields/system-administration/">System Administration</a> / <a href="#/fields/system-administration/node-health-check/">Node Health Check</a> / <a href="#/fields/system-administration/node-health-check/architecture-and-case-study/">Architecture and Case Study</a></nav>

# Generate NHC from a Cluster Definition and Scope a Client Request

<!-- related-block -->
<div class="reading-time">Advanced · Guide · 5 min read · Updated 23 Nov 2026</div>
<!-- related-block -->
<div class="tag-chips"><a class="chip" href="#/.docs/generated/explore/tags/gpu">gpu</a> <a class="chip" href="#/.docs/generated/explore/tags/hpc">hpc</a> <a class="chip" href="#/.docs/generated/explore/tags/nvidia">nvidia</a> <a class="chip" href="#/.docs/generated/explore/tags/slurm">slurm</a></div>


> **Quick guide for** parts 9 and 10: [Architecture-driven NHC](/fields/system-administration/node-health-check/architecture-and-case-study/architecture-driven-nhc.md) and the [Case study](/fields/system-administration/node-health-check/architecture-and-case-study/case-study-build-me-an-nhc.md). Part 1 builds and tests the configs, Part 2 is the checklist for a "build us an NHC" request.

## Before you start

- `pip install pyyaml`, and the tools from this folder: `nhc_gen.py`, `acme_arch.nhc`, `nhc_test_harness.sh`, `cluster-example.yaml`.
- A CI runner or throwaway container for the tests.
- `slurm.conf` and `cluster.yaml` in the same repository.

## Part 1: generate and test (part 9)

1. Describe each hardware class once in `cluster.yaml`: nodes, role, [CPU](/references/glossary?id=cpu "Central Processing Unit"), [NUMA](/references/glossary?id=numa "Non-Uniform Memory Access"), memory, fabric, mounts, GPUs.

   **Expect:** every node in exactly one class, and `YAML` is the only file humans edit.
   **If not:** the generator reports all problems in one run.

2. Generate, cross-checking `slurm.conf`.

   ```bash
   python3 nhc_gen.py cluster.yaml --out build/ --slurm-conf /etc/slurm/slurm.conf --strict
   ```

   **Expect:** `OK: 545 nodes in 4 classes -> nhc.conf, nhc-epilog.conf, nhc-deep.conf in build/`.
   **If not:** `Nothing written.` Fix the listed drift: uncovered nodes, `RealMemory`, `Gres` or thread counts.

3. Install the module next to the built-ins as `/etc/nhc/scripts/acme_arch.nhc`.

   **Expect:** `check_arch_numa_nodes`, `check_arch_gpu_count`, `check_arch_gpu_model` and `check_arch_dcgm_diag` are available.
   **If not:** declare module globals with `declare -g`.

4. Test the generated configs with real NHC, in CI or a container only.

   ```bash
   CI=true ./nhc_test_harness.sh build
   ```

   **Expect:** `# 12 passed, 0 failed`.
   **If not:** the harness exits non-zero. Treat "completed successfully; 0 passed" as a failure too.

5. Run both steps on every pull request.

   ```bash
   python3 nhc/nhc_gen.py nhc/cluster.yaml --out build --slurm-conf slurm/slurm.conf --strict
   sudo -E bash nhc/nhc_test_harness.sh build
   ```

   **Expect:** a pull request that adds nodes to Slurm but not to the architecture fails its own CI.

6. Deliver `build/` and `acme_arch.nhc` as an RPM or an Ansible role, then roll out with a dry run, a canary and the circuit breaker.

   **Expect:** rollback is a `dnf downgrade`.

7. For a new hardware generation, add one class and the `NodeName` line in the same pull request.

   **Expect:** CI generates and tests, and every new node has health checks on day one.

## Part 2: scope a client request (part 10)

1. Reply with understanding, a discovery call and a data bundle, not a config.

   **Expect:** a written proposal within two working days of the call.

2. Collect the bundle, one node of each type, as root.

   ```bash
   sinfo -R; scontrol show config | grep -i healthcheck; grep -i '^NodeName' /etc/slurm/slurm.conf
   lscpu | grep -E 'Socket|Core|Thread|NUMA node\(s\)'; free -g
   ibdev2netdev; ibstat | grep -E 'CA |Rate|State|Link layer'
   findmnt -t nfs,nfs4,lustre,ext4,xfs
   nvidia-smi -L; nvidia-smi --query-gpu=fabric.state,fabric.status --format=csv,noheader
   systemctl is-active nvidia-fabricmanager nvsm munge slurmd
   dmesg -T | grep -i 'NVRM: Xid' | tail -20
   ```

   **Expect:** the cluster they have, not the one they describe.
   **If not:** drains with empty reasons need triage before rollout.

3. Read the fabric state next to the Fabric Manager state.

   **Expect:** `Completed, Success` for every [GPU](/references/glossary?id=gpu "Graphics Processing Unit").
   **If not:** `In Progress, N/A` while `systemctl is-active nvidia-fabricmanager` says `active` is the hang. Add `check_arch_gpu_fabric`.

4. Cross-check the client's `slurm.conf` with `--strict` before proposing.

   **Expect:** an `OK:` line.
   **If not:** ask the client which side is intended, as with `ThreadsPerCore`.

5. Validate every assumption against vendor documentation and a test run.

   **Expect:** the proposal changes. In the case study it changed in 9 places, for example compute HCAs `mlx5_0,3,4,5,6,9,10,11` and a drain list of 48, 64, 74, 79, 95, 119, 120, with Xid 94 sent to monitoring.

6. Answer in the client's language: what was wrong, what is checked, what changes in Slurm, the rollout, how success is measured, what you need, what is out of scope.

   **Expect:** no NHC syntax in the answer.

## If it fails

| What you see | Likely cause | Fix |
|---|---|---|
| `not covered by any class` | Nodes in `slurm.conf` but not in the architecture | Add them to a class, so they get health checks |
| `RealMemory` exceeds what the node has | Slurm would drain it as `Low RealMemory` | Correct `slurm.conf` |
| The Xid check always passes | NHC's config parser drops backslashes | Use bracket expressions: `[(]`, `[)]`, `[[]`, `[]]`, `[.]` |
| `check_arch_numa_nodes` fails with an empty path | A plain `declare` inside a function is local | Use `declare -g` |
| "completed successfully; 0 passed" | NHC could not find its modules (wrong `INCDIR`) | Fix the path, fail the test on "0 passed" |
| The test machine started `sshd` or created `/scratch` | `MARK_OFFLINE=0` stops draining, not auto-fixes | Run only in CI or a container, or pass `--force` |

## Roll back

- A bad definition fails CI, so nothing is written and nothing reaches a node.
- Version the generated RPM per Git tag, and roll back with `dnf downgrade`.

**Don't:** edit generated files (change the YAML and regenerate), or push a generated config to the fleet without a canary.

**Why it works:** [Architecture-driven NHC](/fields/system-administration/node-health-check/architecture-and-case-study/architecture-driven-nhc.md) and the [Case study](/fields/system-administration/node-health-check/architecture-and-case-study/case-study-build-me-an-nhc.md).

<!-- related-block -->
<div class="see-also">

**See also**

- [Architecture-Driven NHC: Generate Health Checks from Your Cluster's Definition](/fields/system-administration/node-health-check/architecture-and-case-study/architecture-driven-nhc.md) — Describe your cluster's architecture once in YAML, generate every NHC config from it, cross-check it against slurm.conf, and prove the result with real NHC before it ships.
- [Case Study: "Build Us an NHC", From a Vague Ask to a Validated Proposal](/fields/system-administration/node-health-check/architecture-and-case-study/case-study-build-me-an-nhc.md) — A client asks for an NHC for their DGX H100 and AMD EPYC Slurm cluster; the discovery questions, first proposal, validation against vendor specs, and the final answer.

</div>
