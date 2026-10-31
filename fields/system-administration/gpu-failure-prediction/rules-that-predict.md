---
id: gpu-pred-rules
title: "From Signals to Decisions"
sidebar_label: "3. From signals to decisions"
order: 3
summary: How to design GPU failure rules - state, event and trend rules, personal baselines, persistence, noise floors and action tiers - and the traps that make rules silently fail.
level: advanced
type: concept
domains: [systems-and-hpc]
tags: [gpu, nvidia, hpc]
relations:
  prerequisites: [gpu-pred-collecting-signals]
---

# From Signals to Decisions

> **Part 3 of the [Predicting GPU Node Failures series](/fields/system-administration/gpu-failure-prediction/README.md).** A signal is not a decision. This page is about the thinking between the two: what kinds of rules exist, how to make a rule notice change without crying wolf, and how to tie each rule to a specific action. By the end you'll be able to design a GPU failure rule set on a whiteboard and explain every line of it.

## Table of Contents
- [From Signals to Decisions](#from-signals-to-decisions)
  - [Table of Contents](#table-of-contents)
  - [Concept 1: three kinds of rule](#concept-1-three-kinds-of-rule)
  - [Concept 2: compare a GPU with itself](#concept-2-compare-a-gpu-with-itself)
  - [Concept 3: persistence and noise floors](#concept-3-persistence-and-noise-floors)
  - [Concept 4: tiers that map to actions](#concept-4-tiers-that-map-to-actions)
  - [The rule set, on one page](#the-rule-set-on-one-page)
  - [The first-event trap](#the-first-event-trap)
  - [Rules are code: test them](#rules-are-code-test-them)
  - [Knobs are opinions](#knobs-are-opinions)
    - [References](#references)

---

## Concept 1: three kinds of rule

Every useful GPU health rule is one of three kinds. They differ in what they look at and how certain they are.

| Kind | Question it asks | Example | Certainty |
|------|------------------|---------|-----------|
| **State** | "Is the GPU in a known-bad condition right now?" | Remap failure flag is set; a remap is pending | High: NVIDIA defines the meaning |
| **Event** | "Did something bad just happen?" | A new Xid 79, 95 or 64 | High, but it's already happened |
| **Trend** | "Is this GPU getting worse?" | Correctable error rate climbing; spare rows running out | Lower: this is the actual *prediction* |

State and event rules are mostly reaction: fast, confident, and late. Trend rules are prediction: early, uncertain, and the only part that's truly "AIOps." A good rule set needs all three, and it must never let the uncertain kind trigger the drastic actions on its own.

---

## Concept 2: compare a GPU with itself

The obvious trend rule is a fixed threshold: "alert when a GPU has more than N correctable errors per hour." It breaks in two ways.

- **What's normal differs.** Part 1 showed that errors concentrate: a few parts produce almost all of them. A fleet-wide threshold is either too high for a GPU that just started failing, or too low for a GPU that has always produced a steady trickle and never got worse.
- **Nobody publishes the number.** There's no NVIDIA figure for "a normal single-bit error rate for H100 HBM3." Any fixed threshold you pick is a guess.

The better question is: **"Is this GPU behaving differently from its own recent past?"** Compare the last hour's error rate with the same GPU's rate over the last day. A GPU that always produces 1 error a minute stays quiet. A GPU that jumps from 1 to 30 a minute gets noticed, whatever the absolute numbers are.

This is a **personal baseline**, and it's the core idea behind most anomaly detection: model what's normal *for this thing*, then look for departures.

---

## Concept 3: persistence and noise floors

Two problems make baseline rules noisy, and each has a simple fix.

**Problem 1: blips.** A single bad scrape or a momentary flag can flip a rule on and off. The fix is **persistence**: require the condition to hold for a while before acting. How long depends on what's at stake:

| Condition | Sensible persistence | Why |
|-----------|---------------------|-----|
| Remap failure flag | A couple of minutes | It's latched; you're only guarding against a bad read |
| Remap pending | Longer, say 15 minutes | NVIDIA says unaffected work keeps running; no rush |
| Fatal Xid | None | The event already happened |
| Rising error trend | Tens of minutes | Trends are noisy; you want it to hold |

**Problem 2: ratios explode near zero.** "3× its baseline" sounds sensible until a GPU with zero errors yesterday has one today: infinitely more than its baseline. The fix is a **noise floor**: a minimum absolute amount of activity before the ratio counts. "At least 3× the baseline *and* at least 10 errors in the hour." The second clause ignores a GPU going from silent to slightly less silent.

When we tested a rule set like this, removing the noise floor did exactly that: a quiet GPU with 5 errors in an hour fired a "rate accelerating" alert. Ratios without floors page you about nothing.

---

## Concept 4: tiers that map to actions

A rule that only says "something is wrong" pushes the hard part onto whoever reads it at 3 AM. Each rule should say **what to do**, and the doing should depend on how sure you are and how bad it is.

| Tier | Meaning | Action | Rules in this tier |
|------|---------|--------|-------------------|
| **1. Broken** | Already failed | Stop sending work now; evidence, diagnostics, likely RMA | Remap failure; Xid 64, 79, 95 |
| **2. Will break jobs** | Damaged, still running | Let current jobs finish, then reset the GPU | Remap pending; uncorrectable errors; Xid 48, 94 |
| **3. Early warning** | Wearing out | Plan, watch, prefer it for short jobs | Spares nearly gone; error rate accelerating |
| **Blind spot** | Can't see | Fix the monitoring | Telemetry missing |

Tier 2 is worth a second look. Why not reset the GPU immediately? Because a reset needs an empty GPU, and NVIDIA's guidance for a pending remap and for "drain and reset" situations is to stop new work, let existing work finish or checkpoint, *then* reset. A scheduler drain does exactly that.

A design trick that keeps this clean: give every alert an **action label** (`drain_now`, `drain_and_reset`, `plan_rma`, `watch`) and let the automation in [part 4](/fields/system-administration/gpu-failure-prediction/from-alert-to-drain.md) look only at that label. The automation never has to know what Xid 95 means; the rule author decides once, in one place.

---

## The rule set, on one page

Here's a complete rule set in plain words. Each line maps to one Prometheus alerting rule over dcgm-exporter metrics.

| Rule | Kind | Fires when | Holds for | Action |
|------|------|-----------|-----------|--------|
| Remap failure | State | Failure flag is 1 | 2 min | `drain_now` |
| Fatal Xid | Event | New Xid 64, 79 or 95 in the last 10 min | - | `drain_now` |
| Remap pending | State | Pending flag is 1 | 15 min | `drain_and_reset` |
| Uncorrectable error | Event | Double-bit count rose in the last hour, or new Xid 48 / 94 | - | `drain_and_reset` |
| Spares nearly gone | Trend | Any bank in the "Low" or "None" bucket | 1 h | `plan_rma` |
| Errors accelerating | Trend | Last-hour SBE rate > 3× its 24 h rate, and ≥ 10 SBEs in the hour | 30 min | `watch` |
| Telemetry missing | Blind spot | Exporter down | 10 min | `watch` |

Notice what's *not* there: no rule drains on Xid 13, which NVIDIA lists as a graphics engine exception that is often the application's fault. And no trend rule drains anything.

---

## The first-event trap

This trap is worth understanding because it hides the most important event in the whole series: the first time a GPU falls off the bus.

Recall from [part 2](/fields/system-administration/gpu-failure-prediction/collecting-the-signals.md#five-ways-the-numbers-lie) that the per-code Xid counter is *born* on its first event: before the first Xid 79 there is no Xid 79 series at all, and then one appears with the value 1. The natural rule asks "did this counter increase in the last 10 minutes?" To answer, the monitoring system subtracts the old value from the new one. There is no old value, so it sees 1 → 1, which is no increase. The alert stays silent.

We confirmed it with a rule unit test: we expected an increase of 1 and the test reported 0.

```text
exp: {... gpu="3", instance="cn042:9400", xid="79"} 1E+00
got: {... gpu="3", instance="cn042:9400", xid="79"} 0E+00
```

The fix is to ask a second question alongside the first: **"does this series exist now when it didn't 10 minutes ago?"** In PromQL:

```yaml
expr: |
  increase(DCGM_EXP_XID_ERRORS_TOTAL[10m]) > 0
  or
  (DCGM_EXP_XID_ERRORS_TOTAL unless DCGM_EXP_XID_ERRORS_TOTAL offset 10m)
```

The general lesson goes beyond Xids: **any rule built on "change" must say what it does when there's no "before."** Counters that appear on demand, nodes that just joined, exporters that just restarted all have no before.

---

## Rules are code: test them

A rule that never fires looks exactly like a rule on a healthy cluster. That's why rules should be treated like code: written down, versioned, and tested with fake inputs where you know the right answer.

A good test set for GPU rules covers four kinds of case:

| Case | Example | Why |
|------|---------|-----|
| Should fire | A remap failure flag set for 10 minutes | Proves the rule works |
| Should *not* fire | A steady, unchanging error rate; an application Xid 13 | Proves it isn't noisy |
| Edge | The first-ever Xid 79; a GPU going from 0 to 5 errors | Where rules actually break |
| Silence | Every counter flat on a healthy GPU | Proves the quiet path stays quiet |

Then comes the step most people skip: **prove the tests can fail.** Deliberately break a rule (remove the "new series" branch, remove the noise floor) and check that a test goes red. When we did this, both breaks were caught. A test suite that can't fail tells you nothing.

> [!IMPORTANT]
> Run the rule tests whenever the telemetry configuration changes, not just when the rules do. Renaming one metric upstream silently disables every rule that used the old name, and only a test will notice.

---

## Knobs are opinions

The numbers in the rule set (3× baseline, 10 errors, 15 minutes) are **starting opinions, not facts about GPUs.** They encode trade-offs:

| Knob | Turn it up and you get | Turn it down and you get |
|------|------------------------|--------------------------|
| Baseline ratio | Fewer, surer warnings, later | Earlier warnings, more false alarms |
| Noise floor | Quiet GPUs never trip it | Real but small degradations get noticed |
| Persistence | Fewer flapping alerts, slower reaction | Faster reaction, more flapping |

The only honest way to set them is against your own failure history, which is what [part 5](/fields/system-administration/gpu-failure-prediction/scoring-and-backtesting.md) is about.

**Takeaway:** combine state, event and trend rules; judge trends against each GPU's own baseline with persistence and a noise floor; give every rule an action tier; and test the rules, including the cases where they should stay silent and the case where there's no "before."

Next: [part 4, acting without making it worse](/fields/system-administration/gpu-failure-prediction/from-alert-to-drain.md).

### References
- [NVIDIA GPU Memory Error Management: Error Recovery and Response Flags](https://docs.nvidia.com/deploy/a100-gpu-mem-error-mgmt/error-recovery-and-response-flags.html)
- [NVIDIA GPU Debug Guidelines: GPU Node Triage (Xid actions)](https://docs.nvidia.com/deploy/gpu-debug-guidelines/gpu-node-triage.html)
- [Prometheus: alerting rules (`for`, labels)](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
- [Prometheus: unit testing rules](https://prometheus.io/docs/prometheus/latest/configuration/unit_testing_rules/)
- [PromQL functions: `increase()`, `rate()`](https://prometheus.io/docs/prometheus/latest/querying/functions/)
- [Schroeder, Pinheiro, Weber, "DRAM Errors in the Wild", SIGMETRICS 2009 (error concentration)](https://www.cs.toronto.edu/~bianca/papers/sigmetrics09.pdf)