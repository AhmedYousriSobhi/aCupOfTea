---
id: probability-quick-guide
title: "Pick and Compute the Right Probability Model"
sidebar_label: "Quick guide: probability"
order: 13
summary: Direct steps for parts 7 to 11 - count outcomes, flip a test result with a tree, compute an expected value, choose binomial or Poisson, and read a normal curve - with the check for each.
level: beginner
type:
  - guide
  - reference
domains:
  - statistics
tags:
  - statistics
relations:
  related:
    - counting-the-ways
    - the-test-that-was-99-percent-accurate
    - what-to-expect
    - coins-and-calls
    - the-bell-curve
    - probability-technical-reference
---

# Pick and Compute the Right Probability Model

> **Quick guide for** [Counting the Ways](/fields/data-science/probability-statistics/probability/counting-the-ways.md), [The Test That Was 99% Accurate](/fields/data-science/probability-statistics/probability/the-test-that-was-99-percent-accurate.md), [What to Expect](/fields/data-science/probability-statistics/probability/what-to-expect.md), [Coins and Calls](/fields/data-science/probability-statistics/probability/coins-and-calls.md) and [The Bell Curve](/fields/data-science/probability-statistics/probability/the-bell-curve.md).
> Use it when you have a probability question and need the method and the check. One Part per story page.

## Before you start

- Python 3 with the standard library only (`itertools`, `math`, `fractions`, `statistics`).
- Write down whether outcomes are equally likely and whether the tries are independent.
- Formal definitions: [technical reference](/fields/data-science/probability-statistics/probability/technical-reference.md).

## Part 1: Count outcomes (equally likely)

1. List the outcomes and mark the event.

```python
import itertools
grid = list(itertools.product(range(1, 7), repeat=2))
double = {g for g in grid if g[0] == g[1]}
eight  = {g for g in grid if sum(g) == 8}
print(len(double | eight))
```

**Expect:** `10`, so `P(double or 8) = 10/36`.
**If not:** you added the lists and counted the shared cell twice: use `P(A) + P(B) - P(A and B)`.

2. For "at least one", count the none: `1 - P(none)`.

**Expect:** at least one six in two rolls is `1 - 25/36 = 11/36`.

## Part 2: Flip a test result (Bayes)

1. Build the crowd of 100,000: split by the truth, then by the test.
2. Keep only the positives and count again.

```python
from fractions import Fraction as F
sick = 100_000 * F(1, 1000); clean = 100_000 - sick
tp = sick * F(99, 100); fp = clean * F(1, 100)
print(tp, fp, tp / (tp + fp))
```

**Expect:** `99 999 11/122`, about 9%.
**If not:** you computed `P(positive | contaminated)`, which is the leaflet's 99%, not the `P(contaminated | positive)` you need.

3. For a second independent positive, use the 11/122 as the new base rate. **Expect:** `363/400 = 90.75%`.

## Part 3: Expected value and spread

1. Write the table of value and probability. The probabilities must add to 1.
2. `E[X] = sum of x * p`; `Var = E[X^2] - E[X]^2`.

**Expect:** the lucky tin gives `9/2`, variance `149/4`, SD about 6.1.
**If not:** a value of 4.5 is not a possible prize and that is fine: it is the balance point, not the likeliest value.

Rules: `E[X + Y] = E[X] + E[Y]` always; variances add only for independent pulls.

## Part 4: Binomial or Poisson

| The question counts | Recipe | Mean, variance |
|---|---|---|
| Yeses in `n` independent tries, same `p` | Binomial | `np`, `np(1-p)` |
| Events in a window, constant rate | Poisson | `λ`, `λ` |

```python
import math
print(math.comb(10, 3) * 0.3**3 * 0.7**7)   # P(exactly 3 smoky of 10)
```

**Expect:** about `0.2668`.
**If not:** for a Poisson, variance far from the mean means mixed rates: use one Poisson per period.

## Part 5: Read a normal curve

1. Draw the histogram first. One hump: go on. Two humps or a long tail: use percentiles.
2. Standardise and read the area.

```python
from statistics import NormalDist
bag = NormalDist(100, 4)
print(bag.zscore(106), round(bag.cdf(106), 4), round(bag.inv_cdf(0.95), 2))
```

**Expect:** `1.5 0.9332 106.58`.
**If not:** a point has probability 0; ask about a range.

## Tips and tricks

- Rebuild the crowd instead of memorising Bayes' rule.
- Use `Fraction` to keep exact answers.
- Seed a simulation (`random.seed(9)`) so a run repeats.
- Within 1, 2, 3 SD of a normal is 68.27%, 95.45%, 99.73%.

## Warnings

> [!WARNING]
> A formula never checks its own assumptions. Independent, same `p`, constant rate and one hump are what the table or the curve silently assume.

- Never add overlapping chances: `10 × 0.3 = 300%` is wrong; use `1 - 0.7^10 = 0.9718`.
- A second positive only helps if the two mistakes are independent.
- Passing one normality check does not make a crowd normal.

## If it fails

| What you see | Likely cause | Fix |
|---|---|---|
| "or" answer too big | Shared outcome counted twice | Subtract the overlap |
| Answer 99% for a rare thing | Wrong crowd (flipped condition) | Count inside the positives |
| Poisson variance far above mean | Two rates averaged | One Poisson per period |
| Bell gives wrong shares | Data not one hump | Percentiles, not the 68-95-99.7 rule |

## Try it

Run [the Bayes lab](/fields/data-science/probability-statistics/labs/bayes.html ':ignore') and [the distributions lab](/fields/data-science/probability-statistics/labs/distributions.html ':ignore'); the starting dials reproduce the numbers above.

**Don't:** trust a result you have not checked against a count or a simulation.

**Why it works:** the five story pages above. Next: [Inference](/fields/data-science/probability-statistics/inference/README.md).
