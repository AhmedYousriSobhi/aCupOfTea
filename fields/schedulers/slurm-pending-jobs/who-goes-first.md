---
id: slurm-priority-multifactor
title: "Who Goes First: Slurm's Priority Number, Taken Apart"
sidebar_label: "2. Who goes first"
order: 2
summary: How Slurm's multifactor priority is computed from age, fairshare and QOS weights, why every weight defaults to zero, how Fair Tree turns usage into a rank, and reading sprio and sshare.
level: intermediate
type: [concept, guide]
domains: [systems-and-hpc]
tags: [slurm, hpc]
relations:
  prerequisites: [slurm-pending-reasons]
  related: [slurm-accounting-multi-tenancy]
---

# Who Goes First: Slurm's Priority Number, Taken Apart

> **Part 2 of [Why Is My Job Still Pending?](/fields/schedulers/slurm-pending-jobs/README.md)** [Part 1](/fields/schedulers/slurm-pending-jobs/why-is-my-job-pending.md) showed that `Priority` means "not first in line". This page opens up the number that decides the line, so you can explain any order to a user and set the weights on purpose.

- ["She submitted after me"](#she-submitted-after-me)
- [The formula](#the-formula)
- [The default that does nothing](#the-default-that-does-nothing)
- [Reading sprio](#reading-sprio)
- [Fairshare: why alice got 0.2](#fairshare-why-alice-got-02)
- [Age: the slow climb](#age-the-slow-climb)
- [QOS: the express lane](#qos-the-express-lane)
- [Choosing weights](#choosing-weights)
- [Back to the complaint](#back-to-the-complaint)
- [References](#references)

---

## "She submitted after me"

Alice submits a job at 09:00. Bob submits at 09:01, carol at 09:05. Carol's job starts first, then bob's. Alice's is still waiting at lunch. She sends the obvious email: "Slurm is supposed to be first come, first served. She submitted after me."

It isn't, and on a shared cluster you don't want it to be. Alice had been running jobs all week; carol hadn't run anything. A queue that ignored that would let whoever submits most often take the whole machine. This page shows exactly how Slurm decided, with the numbers from our lab.

> [!NOTE]
> Lab: Slurm **23.11.4** with slurmdbd. Two accounts, `physics` (users alice, bob, admin) and `chem` (user carol). Alice had used about a minute of CPU time before the test; nobody else had used anything. Weights: fairshare 10000, QOS 5000, age 1000. `PriorityCalcPeriod=1` (minutes) so priorities updated quickly; the default is 5.

---

## The formula

With `PriorityType=priority/multifactor`, each pending job's priority is a weighted sum. From the docs:

```text
Job_priority = site_factor
             + PriorityWeightAge       * age_factor
             + PriorityWeightAssoc     * assoc_factor
             + PriorityWeightFairshare * fairshare_factor
             + PriorityWeightJobSize   * job_size_factor
             + PriorityWeightPartition * partition_factor
             + PriorityWeightQOS       * QOS_factor
             + SUM(TRES weights * TRES factors)
             - nice_factor
```

Every **factor** is a number between 0.0 and 1.0. Every **weight** is an integer you choose in `slurm.conf`. So the weights decide what matters, and how much:

| Factor | 1.0 means | Weight in our lab |
| --- | --- | --- |
| Age | The job has waited `PriorityMaxAge` or longer | 1000 |
| Fairshare | This user is the most under-served | 10000 |
| QOS | The job's QOS has the highest QOS priority | 5000 |
| Job size, partition, association, TRES | Various | 0 (off) |

Rule of thumb: **the weights are the policy.** A factor with weight 0 doesn't exist.

---

## The default that does nothing

`priority/multifactor` is the default `PriorityType`. And every `PriorityWeight*` setting defaults to **0**. Put those together, and a cluster nobody tuned computes this for every job:

We set all weights to 0 on the lab and looked:

```text
 JOBID   USER  PRIORITY    AGE FAIRSHARE    QOS
    39  alice         1      0         0      0
    40  alice         1      0         0      0
    41  alice         1      0         0      0
    42  carol         1      0         0      0
    43  carol         1      0         0      0
```

Every job has priority 1. Ties go by submission order, so this is plain first come, first served: alice's job 39 was first in line (`Resources`). Carol's job 43 was submitted with an "urgent" QOS that should put it first; with a QOS weight of 0, it was last of the five.

So if your users say the queue is FIFO, check `scontrol show config | grep PriorityWeight` before anything else. Fairshare limits you set in `sacctmgr` do nothing for the order unless `PriorityWeightFairshare` is above 0.

---

## Reading sprio

**`sprio`** shows each pending job's priority split into its factors, already multiplied by their weights. With the lab's weights:

```bash
sprio -o "%.6i %.6u %.9Y %.6A %.9F %.6Q"
```

```text
 JOBID   USER  PRIORITY    AGE FAIRSHARE    QOS
    41  alice      2000      0      2000      0
    42  carol     10000      0     10000      0
    43  carol     15000      0     10000   5000
```

Read across: carol's job 42 has fairshare 1.0 × 10000. Job 43 has the same fairshare plus the QOS bonus. Alice's job gets 0.2 × 10000 = 2000. That's the whole answer to her email: carol's jobs outrank hers by 8000 and 13000 before anyone has waited a minute.

`sprio -j <id> -l` adds every column, including the ones at weight 0.

---

## Fairshare: why alice got 0.2

**Fairshare** compares how much each user and account has *used* with how much they're *entitled to* (their shares in `sacctmgr`), and favours the under-served. Since 19.05 Slurm uses the **Fair Tree** algorithm by default. It ranks every user, and gives each a fairshare factor of their rank divided by the number of user associations.

`sshare` shows the inputs:

```bash
sshare -a -o account,user,rawshares,rawusage,effectvusage,fairshare
```

```text
Account                    User  RawShares    RawUsage  EffectvUsage  FairShare
-------------------- ---------- ---------- ----------- ------------- ----------
root                                                59      1.000000
 root                      root          1           0      0.000000   1.000000
 chem                                    1           0      0.000000
  chem                    carol          1           0      0.000000   1.000000
 physics                                 1          59      1.000000
  physics                 admin          1           0      0.000000   0.600000
  physics                 alice          1          59      1.000000   0.200000
  physics                   bob          1           0      0.000000   0.600000
```

There are five user associations, so ranks become fifths:

| Step | Result |
| --- | --- |
| `chem` and `physics` have equal shares. `chem` used nothing, `physics` used everything | `chem` ranks above `physics`. Carol gets the top rank: **1.0** |
| Inside `physics`, admin and bob used nothing; alice used all of it | admin and bob tie at rank 3 of 5: **0.6**. Alice is last: **0.2** |

Two things follow. Bob's fairshare is pulled down by his *account's* usage, not his own: he'd used nothing, yet ranks below carol, because his account-mates used the cluster. And to see why one user outranks another, the docs' advice is to find their first common ancestor account in `sshare`, and compare there.

Usage doesn't count forever. It decays with a half-life of `PriorityDecayHalfLife`, 7 days by default, so last week's heavy user is this week's normal one.

---

## Age: the slow climb

**Age** rises linearly from 0 to 1.0 over `PriorityMaxAge` (default 7 days), so a job that has waited long enough eventually beats newer work. We set `PriorityMaxAge` to 10 minutes to see it move, and waited five:

```text
 JOBID   USER  PRIORITY    AGE FAIRSHARE    QOS
    39  alice      2485    485      2000      0
    42  carol     10480    480     10000      0
    43  carol     15480    480     10000   5000
```

Half of 10 minutes, about half of the 1000 weight. With the defaults, a job gains its full age weight only after a week of waiting.

The trade-off is in the ratio. Here the age weight (1000) is a tenth of fairshare (10000): even a week-old job from a heavy user would never pass a fresh job from an idle one. That might be what you want. If not, raise the age weight until a long wait can win.

---

## QOS: the express lane

The **QOS factor** is the job's QOS priority divided by the highest QOS priority on the cluster. We created one QOS with a priority:

```bash
sacctmgr -i add qos urgent Priority=100
sacctmgr -i modify user carol set qos+=urgent
sbatch -q urgent ...
```

`urgent` is the only QOS with a priority, so its factor is 1.0, and carol's job got the full 5000 on top (job 43 above). A QOS with `Priority=50` would get half.

This is the right tool for "deadline this week" requests: a QOS that only some users may use, often with a limit on how many jobs can use it at once ([part 3](/fields/schedulers/slurm-pending-jobs/limits-that-wait-forever.md)), instead of an admin raising one job's priority by hand.

---

## Choosing weights

There's no correct set, but there is a sensible way to choose. The size of each weight is what matters relative to the others:

| If you want | Then |
| --- | --- |
| Fair use between groups to dominate | Fairshare weight largest, by a clear margin |
| No job to wait forever | Age weight big enough that a full `PriorityMaxAge` beats a fairshare gap |
| Urgent work to jump the line | QOS weight above any realistic fairshare difference, and the QOS restricted |
| Big jobs not to starve behind small ones | Some job size weight, or a reservation |

Weights are integers, so use large ones (like 10000) to leave room for fine distinctions. After any change, run `sprio -l` on a busy queue and check the order looks like your policy. Then tell your users what the policy is. "Fairshare first, then age" in the user guide prevents half of the emails like alice's.

---

## Back to the complaint

Alice's email gets a two-line reply with numbers in it: "Your job's priority is 2000 and carol's is 10000. This week you've used most of physics' share and chem hasn't used any, so the scheduler is putting chem first. Your usage halves every 7 days."

That's the queue working as designed, explained in a way she can check herself with `sprio` and `sshare`. If the design itself is wrong (say, alice has a deadline), that's a policy decision, made with a QOS, not by a quiet `scontrol update` on one job.

And if a cluster's users are right that it's FIFO, the fix is a few lines in `slurm.conf`, because every weight started at zero.

**Takeaway:** priority is a weighted sum of factors, every weight defaults to 0, and `sprio` plus `sshare` explain any order; under Fair Tree, a user's fairshare is their rank among all users.

**Next:** [Part 3, Limits That Wait Forever](/fields/schedulers/slurm-pending-jobs/limits-that-wait-forever.md), covers the jobs that wait no matter what their priority is.

---

## References

- [Multifactor Priority Plugin](https://slurm.schedmd.com/priority_multifactor.html): the formula, each factor, `sprio`.
- [Fair Tree Fairshare Algorithm](https://slurm.schedmd.com/fair_tree.html): ranking, the `rank / user_assoc_count` factor, ties, and the common-ancestor rule.
- [slurm.conf(5)](https://slurm.schedmd.com/slurm.conf.html#OPT_PriorityType): `PriorityType` (default multifactor), `PriorityWeight*` (default 0), `PriorityMaxAge` and `PriorityDecayHalfLife` (default 7 days), `PriorityCalcPeriod` (default 5 minutes).
- [sprio(1)](https://slurm.schedmd.com/sprio.html) and [sshare(1)](https://slurm.schedmd.com/sshare.html): reading priorities and fairshare.
- [Slurm QOS](https://slurm.schedmd.com/qos.html): QOS priority and the QOS factor.
