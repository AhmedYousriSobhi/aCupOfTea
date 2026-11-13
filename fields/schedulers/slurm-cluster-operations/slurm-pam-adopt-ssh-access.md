
# The SSH Backdoor Every Slurm Cluster Has (Until You Close It)

<!-- related-block -->
<div class="reading-time">8 min read</div>
<!-- related-block -->
<div class="related-strip">

**See also:** [Rebooting a Slurm Cluster Without Losing Your Job (Or Anyone Else's)](/fields/schedulers/slurm-cluster-operations/slurm-reboot-order.md), [Slurm cgroups in Practice: What Gets Constrained, and Where the Numbers Lie](/fields/schedulers/slurm-inside-a-job/slurm-cgroups-in-practice.md), [Upgrading Slurm: The Order, the Window, and the Parts That Bite](/fields/schedulers/slurm-cluster-operations/slurm-upgrade-order.md), [Who Starts the Ranks? OpenMP and MPI Under Slurm](/fields/system-administration/openmp-and-open-mpi/mpi-and-openmp-under-slurm.md)

</div>


> **Part of the `schedulers/` series.** By the end you'll have SSH on compute nodes limited to users with a job there, their sessions inside the job's limits, and your admins still able to log in.
>
> Tested with Slurm **23.11.4** and `libpam-slurm-adopt` on Ubuntu 24.04 nodes (cgroup v1), against the pam_slurm_adopt documentation for Slurm 26.11.

## Table of Contents
- [The SSH Backdoor Every Slurm Cluster Has (Until You Close It)](#the-ssh-backdoor-every-slurm-cluster-has-until-you-close-it)
  - [Table of Contents](#table-of-contents)
  - [The problem nobody notices until it bites](#the-problem-nobody-notices-until-it-bites)
  - [Enter `pam_slurm_adopt`](#enter-pam_slurm_adopt)
  - [How it actually decides who gets in](#how-it-actually-decides-who-gets-in)
  - [Installing it](#installing-it)
  - [Configuring it — three places, three changes](#configuring-it--three-places-three-changes)
    - [1. Slurm side](#1-slurm-side)
    - [2. SSH side](#2-ssh-side)
    - [3. PAM side](#3-pam-side)
    - [4. Turn off pam\_systemd](#4-turn-off-pam_systemd)
    - [5. Keep the admins in, and fail closed](#5-keep-the-admins-in-and-fail-closed)
  - [Proving it on a node](#proving-it-on-a-node)
  - [Roll it out like any risky change: one node first, this matrix, then the rest, with a root session open the whole time.](#roll-it-out-like-any-risky-change-one-node-first-this-matrix-then-the-rest-with-a-root-session-open-the-whole-time)
  - [The mental model to keep](#the-mental-model-to-keep)
  - [References](#references)

---

## The problem nobody notices until it bites

Here's a scenario that plays out on unprotected clusters constantly:

A user submits a job through `sbatch`. Slurm dutifully allocates a slice of a compute node, wraps it in a cgroup, and enforces the CPU/memory limits that job asked for. So far, so good — the scheduler is doing its job.

Then the same user, out of habit or curiosity, does this:

```bash
ssh compute-node-042
```

And... it just works. No job context, no cgroup, no resource accounting. That SSH session lands on the node completely outside Slurm's supervision. From there, a user (or a stray leftover process) can:

- 🔓 **Consume resources that aren't counted under any job's cgroup**
- 🔓 **Escape the job's CPU/memory limits entirely**
- 🔓 **Keep running long after the job that "owned" the node has ended**

None of this requires malicious intent — it's usually just someone debugging or checking on a running job the easy way. But the effect is the same: your scheduler's accounting is now a polite fiction.

## Enter `pam_slurm_adopt`

This is a PAM (Pluggable Authentication Module) module that ships *with* Slurm, and its job is refreshingly narrow:

> **Every login or process on a compute node must belong to a Slurm job — no exceptions.**

> [!NOTE]
> Official reference: [Slurm documentation — pam_slurm_adopt](https://slurm.schedmd.com/pam_slurm_adopt.html)

## How it actually decides who gets in

When a user tries to SSH into a compute node, here's the decision Slurm makes on their behalf:

```
User attempts SSH into compute node
              │
              ▼
   Does this user have an active
   Slurm job running on THIS node?
              │
      ┌───────┴───────┐
     YES               NO
      │                 │
      ▼                 ▼
 Session is "adopted"   Login denied
 into that job's cgroup (unless configured
      │                 otherwise)
      ▼
 Same CPU/memory limits
 as the job apply to the
 SSH session too
```

The practical upshot:

- ✅ Only users with a **currently running job** on that specific node can log in.
- ✅ Whatever they do once they're in — spawn processes, run a quick `htop`, debug something — stays **inside the job's resource allocation.** No more phantom, unaccounted-for work.

---

## Installing it

Nothing exotic here — follow Slurm's own [installation guide](https://slurm.schedmd.com/pam_slurm_adopt.html#INSTALLATION). It typically ships alongside your Slurm build/package, so if you're already building Slurm from source with the standard contribs enabled, you likely already have the module available.

---

## Configuring it — three places, three changes

Per the [official documentation](https://slurm.schedmd.com/pam_slurm_adopt.html#SLURM_CONFIG), the module itself needs three configuration surfaces. Skip any one of them and it either won't function or won't have anything to "adopt" into. Steps 4 and 5 are the ones people skip: without them, it *looks* like it works.

### 1. Slurm side

- [ ] **Enable the `task/cgroup` plugin** in `slurm.conf`. This is a hard prerequisite — `pam_slurm_adopt` has nothing to adopt sessions *into* without cgroup containment already active. Walk through the [Slurm cgroups guide](https://slurm.schedmd.com/cgroups.html) if you haven't set this up yet.

- [ ] **Set `PrologFlags=contain`** in `slurm.conf`. This is the flag that actually creates the "extern" step — the container that SSH-launched processes get folded into.

> [!WARNING]
> **Jobs launched *without* `PrologFlags=contain` don't get an extern step at all** — which means `pam_slurm_adopt` has no valid target to adopt an SSH session into for those jobs, regardless of how correctly everything else is configured.

> [!TIP]
> `UsePAM` in `slurm.conf` is a **completely different setting** and has nothing to do with `pam_slurm_adopt`. Don't confuse the two while troubleshooting — chasing `UsePAM` when the real issue is `PrologFlags` is a common dead end.

### 2. SSH side

- [ ] In `/etc/ssh/sshd_config`, confirm:

```
UsePAM yes
```

This is typically the default already — but confirm it explicitly rather than assuming, especially on hardened or custom-imaged nodes.

### 3. PAM side

- [ ] In your `/etc/pam.d` config (typically the `sshd` service file), add:

```
account    required      pam_slurm_adopt.so
```

> [!NOTE]
> You can use either `required` or `sufficient` as the PAM control flag, depending on how strict you want the enforcement stacked against other `account` rules already in that file.

Also check that nothing earlier in the account stack short-circuits it. The docs call out `account sufficient pam_localuser.so` in some distributions' included files: it succeeds for every local user before `pam_slurm_adopt` is ever asked.

### 4. Turn off pam_systemd

This is the trap that makes everything above look fine while doing nothing. We tested it on a node with only steps 1–3 done. Alice had a job on the node with a 500 MB memory limit, so her SSH login was allowed. Then we looked at where her shell landed:

```text
4:memory:/docker/.../user.slice/user-2001.slice/session-15.scope
```

Systemd's user session, not the job. `pam_systemd`, which runs later in the session phase on most distributions, moved the process into its own `user.slice` after `pam_slurm_adopt` had adopted it. Admitted, but unconfined.

The docs say it plainly: `pam_systemd` conflicts with `pam_slurm_adopt` and must be disabled in every file included by sshd (`common-session` on Debian and Ubuntu, `password-auth` and `system-auth` on RHEL). On Ubuntu:

```bash
sed -i 's/^session\toptional\tpam_systemd.so/#&/' /etc/pam.d/common-session
```

Same login, same job, afterwards:

```text
4:memory:/slurm_cn001/uid_2001/job_2/step_extern/task_0
```

Inside the job's `extern` step, under its 500 MB limit (`memory.limit_in_bytes` read `524288000`).

The price: no systemd user session on compute nodes. `/run/user/$UID` isn't created and `XDG_RUNTIME_DIR` is unset (we saw `unset` in that same login). Software that needs a user D-Bus won't work there. The docs offer a partial workaround, a `TaskProlog` that points `XDG_RUNTIME_DIR` at a per-user directory in `/dev/shm`.

### 5. Keep the admins in, and fail closed

`pam_slurm_adopt` lets **root** in always. Everyone else needs a job, and that includes your admins. With only the line from step 3, our Ansible account was locked out of the node the same way as a user with no job:

```text
pam_slurm_adopt[423]: send_user_msg: Access denied by pam_slurm_adopt: you have no active jobs on this node
```

That's every playbook in the [Ansible series](/fields/devops/ansible/README.md) failing with `UNREACHABLE!` on that node. The docs' fix is to stack `pam_access` in front of it, for an admin group:

```bash
groupadd -f hpcadmins
usermod -aG hpcadmins admin
printf '+:(hpcadmins):ALL\n-:ALL:ALL\n' >> /etc/security/access.conf
```

and in `/etc/pam.d/sshd`, replacing the line from step 3:

```text
account    sufficient    pam_access.so
account    required      pam_slurm_adopt.so action_adopt_failure=deny action_generic_failure=deny
```

`pam_access` as `sufficient` lets the admin group straight through; for everyone else it fails, and the decision falls to `pam_slurm_adopt`.

The two `action_..._failure=deny` options matter just as much. By default, if adoption itself fails, or the module hits an error, the login is **allowed**: the default is chosen so you don't lock yourself out while testing. In production that means a plugin problem quietly lets users in unconfined. The docs recommend setting both to `deny` once it works. (We didn't simulate a module failure in the lab; this is from the documentation.)

> [!CAUTION]
> Test from a second session that's already open as root before you log out. A PAM mistake on sshd locks out everyone but root, and only if root SSH login is allowed.

---

## Proving it on a node

With all five steps on one node, we ran the whole matrix:

| Who | Situation | Result |
| --- | --- | --- |
| admin (in `hpcadmins`) | No job | Logged in |
| alice | Job running on the node | Logged in, inside `job_2/step_extern` |
| alice | Same job, just cancelled | Denied |
| bob | Never had a job | Denied |
| Ansible (`admin`) | `ansible cn001 -m ping` | `SUCCESS` |

Roll it out like any risky change: one node first, this matrix, then the rest, with a root session open the whole time.
---

## The mental model to keep

```
Without pam_slurm_adopt:
  Job resource limits  ═══╗
                           ╠══► enforced only for srun/sbatch-launched processes
  SSH sessions ───────────╝     (everything else runs free)

With pam_slurm_adopt:
  Job resource limits  ═══╗
                           ╠══► enforced for EVERYTHING on the node
  SSH sessions ───────────╝     tied to that user's active job
```

One module, `PrologFlags=contain`, `pam_systemd` out of the way, and a door for admins: the gap between "what Slurm thinks is running" and "what's actually running" closes. Skip the `pam_systemd` step and you get the worst of both: users believe they're contained, and they aren't.

**Takeaway:** `pam_slurm_adopt` only confines SSH sessions if `pam_systemd` is off and adoption failures are set to deny; check where a real login lands with `/proc/self/cgroup` before you trust it.

---

## References

- [pam_slurm_adopt](https://slurm.schedmd.com/pam_slurm_adopt.html): installation, `PrologFlags=contain`, the `pam_systemd` conflict and XDG workaround, `pam_access` stacking for admins, and the `action_*` options.
- [slurm.conf: PrologFlags](https://slurm.schedmd.com/slurm.conf.html#OPT_PrologFlags): `Contain` and the extern step.
- [Slurm cgroups guide](https://slurm.schedmd.com/cgroups.html): `task/cgroup` and `proctrack/cgroup`.
- [pam_access(8)](https://man7.org/linux/man-pages/man8/pam_access.8.html) and [access.conf(5)](https://man7.org/linux/man-pages/man5/access.conf.5.html): the admin group rule.
- [pam_systemd(8)](https://www.freedesktop.org/software/systemd/man/latest/pam_systemd.html): what it does to a login session.