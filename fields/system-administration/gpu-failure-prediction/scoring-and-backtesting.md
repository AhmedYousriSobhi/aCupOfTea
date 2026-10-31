---
id: gpu-pred-backtesting
title: "Is the Prediction Any Good?"
sidebar_label: "5. Is the prediction any good?"
order: 5
summary: How to judge GPU failure predictions - base rates, precision, recall, lead time, horizons, label quality, leakage and drift - and when a learned model is worth it.
level: advanced
type: concept
domains: [systems-and-hpc]
tags: [gpu, nvidia, hpc]
relations:
  prerequisites: [gpu-pred-alert-to-drain]
---

# Is the Prediction Any Good?

> **Part 5 of the [Predicting GPU Node Failures series](/fields/system-administration/gpu-failure-prediction/README.md), the last one.** A prediction you never checked is a superstition. This page gives you the ideas to check one: why rare events fool intuition, the three numbers that describe a predictor, the mistakes that make those numbers lie, and when a machine-learning model is actually worth it. By the end you'll be able to defend (or demolish) any "we predict GPU failures" claim.

## Table of Contents
- [Is the Prediction Any Good?](#is-the-prediction-any-good)
  - [Table of Contents](#table-of-contents)
  - [Concept 1: the base-rate trap](#concept-1-the-base-rate-trap)
  - [Concept 2: four outcomes, three numbers](#concept-2-four-outcomes-three-numbers)
  - [Concept 3: the horizon](#concept-3-the-horizon)
  - [Concept 4: what counts as a failure](#concept-4-what-counts-as-a-failure)
  - [Concept 5: backtesting, and how it lies](#concept-5-backtesting-and-how-it-lies)
  - [Rules or a model?](#rules-or-a-model)
  - [What a model must never do](#what-a-model-must-never-do)
  - [The interview answer, revisited](#the-interview-answer-revisited)
    - [References](#references)

---

## Concept 1: the base-rate trap

[Part 1](/fields/system-administration/gpu-failure-prediction/what-fails-and-what-warns.md#what-the-field-studies-say) quoted two facts from Google's DRAM study that sound contradictory:

- A correctable error made an uncorrectable error in the same month between 9 and 400 times more likely.
- Even so, the chance of an uncorrectable error after a correctable one was only 0.1 to 2.3% per month.

Both are true because uncorrectable errors are **rare to begin with**. Multiply a tiny number by 400 and you can still get a small number. This is the **base-rate trap**: a signal can be enormously *informative* and still be *wrong most of the time* when it fires.

Work it through with the study's own upper figure. If you replaced every part that showed a correctable error, at most 2.3% of those parts would have had an uncorrectable error that month. At least 97.7% of the replacements would, that month, have been unnecessary. That's why the authors said early replacement only makes sense where downtime is very costly.

Two lessons follow:

- **"X makes failure N times more likely" is not a reason to act.** Ask how likely failure is *after* X, in absolute terms.
- **Cheap actions tolerate weak signals; expensive actions don't.** Flagging a GPU on a dashboard can follow a signal that's usually wrong. Draining a node, or worse, pulling a GPU, needs one that's usually right.

---

## Concept 2: four outcomes, three numbers

Every time a rule could have fired, one of four things happened:

| | GPU failed soon after | GPU didn't fail |
|---|---|---|
| **Rule fired** | True positive: a real warning | False positive: a false alarm |
| **Rule stayed quiet** | False negative: a missed failure | True negative: correctly quiet |

From that table come the three numbers that describe any predictor:

| Number | Question | Plain meaning |
|--------|----------|---------------|
| **Precision** | When it fires, how often is it right? | "Should I trust this alert?" |
| **Recall** | Of all real failures, how many did it warn about? | "How much does it catch?" |
| **Lead time** | How much warning did the right alerts give? | "Is the warning early enough to use?" |

Precision and recall pull against each other. Make a rule more sensitive and it catches more failures (recall up) but raises more false alarms (precision down). Neither number alone means anything: a rule that fires on every GPU every day has perfect recall, and a rule that never fires has no false alarms.

Different action tiers from [part 3](/fields/system-administration/gpu-failure-prediction/rules-that-predict.md) need different balances:

| Tier | Needs | Because |
|------|-------|---------|
| Drain now | Very high precision | Every false alarm costs a node |
| Drain and reset | High precision, useful lead time | Gentle, but still capacity |
| Early warning | Recall and long lead time; precision can be low | A wrong warning costs a glance |

The rule of thumb: **a rule earns its action with its precision.** A warning rule gets promoted to a draining rule only when its measured precision says so.

---

## Concept 3: the horizon

"Did the GPU fail *after* the alert?" needs a time limit, or every alert is eventually right: everything fails someday. That limit is the **horizon**.

The horizon isn't a statistical choice; it's an operational one. It should be the window in which a warning is still *useful*, which ties back to [part 4](/fields/system-administration/gpu-failure-prediction/from-alert-to-drain.md#principle-2-lead-time-must-beat-drain-time): long enough to drain and checkpoint, short enough that the warning is about this failure and not some later one.

The same alerts can look excellent or useless depending on the horizon. In a small hand-made test of a backtest, alerts that came 13 to 36 hours before failures scored well with a 72-hour horizon and scored zero with a 12-hour one. Nothing about the alerts changed; only the question did. **Always state the horizon next to any precision or recall number.**

---

## Concept 4: what counts as a failure

Every number above depends on the list of failures you compare against: your **labels**. Bad labels make every score meaningless, and they're the hardest part of the whole project.

Good sources, roughly from most to least trustworthy:

1. RMA records with the GPU identified.
2. Drain reasons written by humans or node health checks.
3. Fatal Xids in the kernel log (64, 79, 95).
4. Job failures that users blamed on a GPU.

Common label problems:

| Problem | Effect |
|---------|--------|
| Software crashes counted as GPU failures | The predictor gets blamed for missing failures no hardware signal could see |
| The GPU your automation drained "didn't fail" | The early drain *prevented* the failure, so a good prediction scores as a false alarm |
| GPUs that haven't failed *yet* treated as healthy forever | Recent warnings look wrong just because there's been no time to be proven right |

The last two have names in statistics. Acting on a prediction changes the outcome you're trying to measure (an **intervention** problem). And a GPU that hasn't failed by the end of your data isn't "healthy," it's **censored**: you just don't know yet. Keep a list of drained GPUs and what happened to them after the reset, and leave the newest warnings out of the score until their horizon has passed.

> [!TIP]
> Start collecting labels on day one, before you trust any rule. The dry-run log from part 4 plus a spreadsheet of RMAs is already a usable label set.

---

## Concept 5: backtesting, and how it lies

**Backtesting** means replaying history: take the alerts your rules *would have* fired, take the failures that *actually* happened, and compute precision, recall and lead time. It's the only way to tune the knobs from part 3 on evidence instead of taste.

Three ways a backtest flatters you:

- **Tuning and grading on the same data.** If you adjust the threshold until last quarter's failures are all caught, of course they're caught. Tune on older months, then grade on newer months you held back. This is a **time-based split**, and with time-ordered data it's the only honest one.
- **Leakage.** A feature that is really the failure itself, such as "an Xid 79 happened," makes a predictor look perfect at predicting Xid 79. Ask of every input: "could I have known this *before* the failure?"
- **Drift.** A driver or firmware update can change how often counters tick or how flags behave. A rule tuned before the update may be wrong after it. Re-run the backtest after every driver or exporter change, and compare.

> [!WARNING]
> A backtest score with no stated horizon, no time split and no description of the labels is not a score. Ask for all three whenever someone shows you one, including yourself.

---

## Rules or a model?

"AIOps" often means a learned model that combines many weak signals into one risk score per GPU. In principle it can beat rules: a GPU with a slowly rising error rate, one bank low on spares and some PCIe retries might be risky even when no single rule fires.

Two pieces of evidence argue for patience:

- **You probably don't have enough failures yet.** For logistic regression, the simplest common model, Peduzzi et al. (1996) found that with fewer than about 10 outcome events per predictor variable, the estimates became biased and confidence intervals unreliable. A model with six inputs wants on the order of 60 real, labeled GPU failures. Many clusters don't have that many.
- **Simple signals are hard to beat.** In Google's DRAM study, a classification-tree model using correctable-error counts and memory attributes did not predict uncorrectable errors significantly better than the simple correctable-error signal. That was host memory, not GPU HBM, but it's a reason to expect modest gains, not magic.

The recommended path, and what each step costs:

| Step | Gain | Cost |
|------|------|------|
| Rules from NVIDIA's documented states and events | Confident, explainable, available today | Can't combine weak signals |
| Trend rules with personal baselines | Early warning | Knobs to tune; lower precision |
| Logistic regression on per-GPU-day features | Combines signals; each weight is readable | Needs dozens of labeled failures |
| Gradient-boosted trees or similar | Captures interactions | Hard to explain; easy to overfit |

Every step up buys recall and costs explainability. At 3 AM, "drained because spare rows ran out" is an answer. "Drained because the risk score was 0.83" is a question.

Whatever you build, judge it exactly like the rules: same labels, same horizon, same time split, same three numbers. If it doesn't beat the best rule on held-out months, keep the rule.

---

## What a model must never do

- **Skip the tiers.** A model's score starts as a warning and earns the right to drain through backtests, exactly like a rule.
- **Decide an RMA.** NVIDIA's field diagnostic decides that; the model only points at which GPU to test.
- **Overrule a documented flag.** Remap failure and fatal Xids stay as rules. A model that disagrees with them is the one that's wrong.
- **Treat missing data as safe.** No telemetry means "unknown," never "low risk."

---

## The interview answer, revisited

You can now answer the original question with reasons, not buzzwords:

> "I define operational excellence in two halves: performance and survival. For survival I watch the GPU memory error ladder: corrected errors, row remaps, spare-row budget, pending remaps, and fatal Xids. I react immediately to the states NVIDIA defines as failures, drain gracefully on damage, and treat trends against each GPU's own baseline as early warnings. My automation only drains, never more, behind a budget and a staged rollout. And I measure every rule by precision, recall and lead time on held-out history, because failures are rare and rare events fool intuition. I'd only move to a learned model once I had enough labeled failures to prove it beats the rules."

**Takeaway:** a GPU failure prediction is only as good as its measured precision, recall and lead time on honest, held-out history, so respect base rates, state your horizon, guard your labels, and let evidence decide when rules give way to a model.

That's the end of the concepts. To deploy all of it, continue to the [runbook](/fields/system-administration/gpu-failure-prediction/runbook.md), the deep-technical companion with every config, test and script. Or go back to the [overview](/fields/system-administration/gpu-failure-prediction/README.md), or the reactive side in the [Node Health Check series](/fields/system-administration/node-health-check/README.md).

### References
- [Schroeder, Pinheiro, Weber, "DRAM Errors in the Wild: A Large-Scale Field Study", SIGMETRICS 2009](https://www.cs.toronto.edu/~bianca/papers/sigmetrics09.pdf)
- [Peduzzi et al., "A simulation study of the number of events per variable in logistic regression analysis", J Clin Epidemiol 1996](https://pubmed.ncbi.nlm.nih.gov/8970487/)
- [Cui et al., "Characterizing GPU Resilience and Impact on AI/HPC Systems", arXiv:2503.11901](https://arxiv.org/abs/2503.11901)
- [Grattafiori et al., "The Llama 3 Herd of Models", arXiv:2407.21783](https://arxiv.org/abs/2407.21783)
- [NVIDIA GPU Memory Error Management: RMA Policy](https://docs.nvidia.com/deploy/a100-gpu-mem-error-mgmt/rma-policy-thresholds-for-row-remapping.html)
- [Prometheus: alerting rules and the `ALERTS` series (alert history for backtests)](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)