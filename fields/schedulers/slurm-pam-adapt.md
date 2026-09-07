# The SSH Backdoor Every Slurm Cluster Has (Until You Close It)

> **Part of the `schedulers/` series.** Status: 🚧 living document — this one grows as more Slurm internals get explored.

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
  - [The mental model to keep](#the-mental-model-to-keep)

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

Per the [official documentation](https://slurm.schedmd.com/pam_slurm_adopt.html#SLURM_CONFIG), getting this working touches exactly three configuration surfaces. Skip any one of them and the module either won't function or won't have anything to "adopt" into.

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

One module, one PAM stanza, one `PrologFlags` change — and the gap between "what Slurm thinks is running" and "what's actually running" closes completely. It's a small configuration lift for a problem that otherwise quietly erodes your scheduler's accounting on every single multi-tenant cluster.