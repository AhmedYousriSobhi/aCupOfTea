---
id: old-data-and-background-work
sidebar_label: Old Data and Background Work
summary: How to give pre-existing data an owner without surprises, and why background monitors and their cached readings must follow the signed-in person.
level: intermediate
type: concept
domains: [software-engineering, system-design]
tags: [system-design, software-engineering, programming]
---

# The Orphans Come Home: Old Data and Background Work

*Local App Accounts, tea talk 4 of 6. Previous: [Sessions and Two Walls](/programming/local-app-accounts/sessions-and-two-walls.md). Next: [Lock, Recovery and Going Online](/programming/local-app-accounts/lock-recovery-and-going-online.md).*

Two awkward questions arrive the moment accounts exist. What happens to the data created *before* anyone had an account? And what happens to everything the app does in the background when the person who started it signs out? This talk answers both, and the second answer comes with two bugs worth framing.

---

## The one-sentence version

**A data migration is a trust event, and background work is part of the session: when the person leaves, both the work and its cached results must go with them.**

---

## Words you'll meet

| Term | Plain meaning |
| --- | --- |
| **Atomic** | Two related meanings. In concurrent code: *indivisible*, so nobody can observe it half-done. In databases (ACID): *all or nothing*, so if a fault hits partway through, every write is rolled back |
| **Isolation** | Overlapping operations don't see or disturb each other's half-finished work. It's the ACID letter that handles concurrency |
| **Race condition** | Two actions overlap and the result depends on who got there first |
| **Derived data** | Data computed from other data, such as a cache or a "last known status." It goes stale when its source changes |
| **Idempotent** | Safe to do more than once: doing it again changes nothing further |

---

## Part 1: the orphans

**Scene.** Ahmed has used the app for a year, *before* accounts. His profiles have no owner. On his first sign-in they appear on a **claim screen**: each profile with its cluster and note counts, nothing ticked until he chooses.

Four rules make that screen safe:

1. **Nothing is claimed silently.** Skipping leaves the profiles unowned and hidden. A small banner and an "Unclaimed data (N)" menu entry show how many are waiting, by count only.
2. **A safety copy first.** Before ownership changes, the data is backed up. If the backup fails, nothing changes.
3. **All or nothing.** The change is applied as one step. If someone else claimed one in between, everything is undone, not half of it.
4. **A confirmation, and no undo.** Nothing is pre-selected, and a second step says what will be taken and that there is no undo.

And the question every new user asks: *"How do I know these clusters are mine?"* Each row has a small arrow that opens the **names** of the clusters inside. Those names are shown only to the **first** account on the computer, the person who owned everything before accounts existed. Later accounts see counts only, so a second person who signs up can't read the first person's cluster names before they're claimed.

Unclaimed profiles are paused: no monitoring, no reminders, no alerts, because nobody is there to receive them.

### Two different problems hiding in rule 3

*Atomic* (the database sense) covers a **failure partway through**: if something breaks halfway, every change is rolled back, so you never end up with half the profiles claimed.

A **race condition** is two claimers reaching the same profile at the same moment. That one is about *isolation*, not atomicity: the claim must check "is it still unowned?" inside the same transaction as the write, so only one claimer wins.

The word "atomic" is also used in concurrent code to mean *indivisible* (nobody can see the operation half-done). It's related, but it is not the same promise.

> **Lesson.** Make consent explicit, the change atomic, a backup first, and show people proof of what they're taking.

---

## Part 2: the Night Watch

**Scene.** The app does a lot while you aren't looking: checking that clusters are reachable, polling the job scheduler, watching a ticket tracker, tracking storage, firing reminders. Before accounts, all of that started with the app. Now it starts **when someone signs in** and stops **when they sign out**.

```
sign out  ->  close SSH and console sessions
              stop tunnels
              close pop-out windows
              stop every background monitor (last started, first stopped)
              forget the last readings (reachability, scheduler snapshots)
sign in   ->  start every monitor, recompute reminders
```

Sign-out also shows a short list of what it's about to close. So when Ahmed signs out and Abdelrahman signs in, nothing of Ahmed's is still running behind his back, and Abdelrahman's monitors watch only Abdelrahman's clusters.

### Bug one: the ghost reading

A tester signed out, switched a test VM off, signed back in, and the card still said the VM was up for a moment before flipping to down. The monitors had stopped, but their **last answers were still in memory**. The fix: clear those cached readings on sign-out too, so each card says *checking* until it has really been probed.

A "last known status" is *derived data*: a copy computed from reality, so it goes stale the moment reality changes. Anything derived (caches, snapshots, indexes) needs a rule for when it's thrown away.

### Bug two: the late arrival

A tester on a Mac opened the app after an update and found the overview stuck on grey placeholder cards. The cause is only visible in the real app: a **remembered sign-in** happens while the app is still starting up, *before* some monitors have registered. The system considered itself "on duty", but a monitor that showed up late was never told to start.

The fix was one rule: **a monitor that turns up while the system is on duty starts at once.**

That's an *idempotent start*: make "start" safe to call at any time, in any order, any number of times. "Start everything when X happens" is fragile whenever a component can register *after* X.

> **Lessons.** (1) Cached and derived state is part of what a sign-out must clear. (2) Don't assume startup order; make start safe to call late.

---

## Recap

- Old data gets an owner only by explicit choice, with a backup, an all-or-nothing change and a confirmation.
- Atomicity handles failures partway through; isolation handles two actors colliding.
- Background work starts on sign-in and stops on sign-out, and cached readings are cleared with it.
- A component that registers late must still start.

**Next tea talk:** [Lock, Recovery and Going Online](/programming/local-app-accounts/lock-recovery-and-going-online.md), covering the lock screen, forgotten passwords, and the door already built for online sign-in.