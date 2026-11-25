
<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/fields/">Fields</a> / <a href="#/fields/data-science/">Data Science</a> / <a href="#/fields/data-science/probability-statistics/">Probability &amp; Statistics, One Sip at a Time</a> / <a href="#/fields/data-science/probability-statistics/inference/">Inference</a></nav>

# From a Sample to a Statement: Intervals, Tests and Lines

<!-- related-block -->
<div class="reading-time">Beginner · Guide · 3 min read · Updated 25 Nov 2026</div>
<!-- related-block -->
<div class="tag-chips"><a class="chip" href="#/.docs/generated/explore/tags/statistics">statistics</a></div>


> **Quick guide for** [Averages and Intervals](/fields/data-science/probability-statistics/inference/averages-and-intervals.md) (parts 12 and 13), [The Courtroom for Numbers](/fields/data-science/probability-statistics/inference/the-courtroom-for-numbers.md) and [Two Things Moving Together](/fields/data-science/probability-statistics/inference/two-things-moving-together.md).
> Python 3, standard library only. Formal statements: [technical reference](/fields/data-science/probability-statistics/inference/technical-reference.md).

## 1. How wobbly is an average?

`SE = sigma / sqrt(n)`. Four times the sample halves it. Averages pile into a bell whatever the crowd (`n >= 30` is a rule of thumb only; skewed crowds need more).

**Trap:** bias is not cured by `n`: tight and wrong.

## 2. Give a range

```python
import math, statistics as st
from statistics import NormalDist

z = NormalDist().inv_cdf(0.975)            # 1.96
def interval(sample):                      # estimate +/- z * standard error
    m = st.fmean(sample)
    se = st.stdev(sample) / math.sqrt(len(sample))
    return m - z * se, m + z * se
```

Proportion: `SE = sqrt(p * (1 - p) / n)`. Small `n`: use the t distribution (`n = 10`: 2.262, `n = 40`: 2.023, not 1.96). No formula: bootstrap, resampling your sample with replacement and taking the middle 95% of the means.

**Trap:** 95% is about the method (95 of 100 nets catch the truth), not one interval.

## 3. Could luck do this?

1. Say the null: luck only, the labels mean nothing.
2. Re-deal the labels many times; count how often luck gives a result at least as extreme.
3. That share is the p-value. Small p means luck is a poor explanation.

Many tests: `P(at least one false alarm) = 1 - 0.95^k` (`k = 20` gives 0.64). Report the effect size and interval, and how many things you tried.

**Trap:** p is not the chance the null is true, and not the size of the effect.

## 4. Do two columns move together?

```python
import statistics as st
fit = st.linear_regression(temp, cups)    # slope, intercept
r = st.correlation(temp, cups)
```

`r` is the average of `z_x * z_y`; `slope = r * SD(y) / SD(x)`; `r squared` is the share of the squared miss the line removes. Draw the scatter first.

**Trap:** not causation, not curves, one outlier can swing `r`, no prediction beyond the range of `x` you saw.

## Symptoms

| What you see | Likely cause | Fix |
|---|---|---|
| Tight interval, wrong answer | Biased sample | Fix how you choose, not how many |
| Interval too narrow for small `n` | Used 1.96 | Use t |
| "Significant" but tiny gap | Huge sample | Report effect size |
| One hit in twenty tries | Many tests | Count the tries |
| Strong `r`, odd scatter | Curve or outlier | Draw it first |

> [!WARNING]
> Narrow is not right, small p is not proof, and a line is not a law. Check the sample and the picture before the number.

## Try it

### Sampling and intervals lab

[Sampling and intervals lab](/fields/data-science/probability-statistics/labs/sampling.html#embed ':ignore')

### Permutation test lab

[Permutation test lab](/fields/data-science/probability-statistics/labs/permutation.html#embed ':ignore')

### Correlation lab

[Correlation lab](/fields/data-science/probability-statistics/labs/regression.html#embed ':ignore')

**Why it works:** the three story pages above (parts 12 to 15). Back to [the map of the series](/fields/data-science/probability-statistics/the-map-of-leaf-and-kettle.md).

<!-- related-block -->
<div class="see-also">

**See also**

- [Averages and Intervals: Why Averages Behave and How Sure You Can Be](/fields/data-science/probability-statistics/inference/averages-and-intervals.md) — An average is itself random: its spread shrinks as sigma over root n and its shape tends to a bell. A confidence interval turns that wobble into a give-or-take, and bias is invisible to it.
- [Inference, Technically: Sampling Distributions, Intervals, Tests and Regression](/fields/data-science/probability-statistics/inference/technical-reference.md) — The formal layer under parts 12 to 15: the sampling distribution of the mean, intervals and the t distribution, p-values and permutation tests, multiple testing, and least-squares regression.
- [The Courtroom for Numbers: Could Plain Luck Do This?](/fields/data-science/probability-statistics/inference/the-courtroom-for-numbers.md) — A hypothesis test asks one question: could plain luck have produced a difference this big? Shuffle the labels and count. What the p-value is, what it is not, and how testing twenty things fools you.
- [Two Things Moving Together: Correlation and the Line](/fields/data-science/probability-statistics/inference/two-things-moving-together.md) — Correlation is the average product of paired z-scores, a number about straight-line togetherness only. The regression line is least squared walking applied to a line. Graph first, always.

</div>
<!-- related-block -->
<div class="mentioned-in">

**Mentioned in**

- [Inference, Technically: Sampling Distributions, Intervals, Tests and Regression](/fields/data-science/probability-statistics/inference/technical-reference.md) — The formal layer under parts 12 to 15: the sampling distribution of the mean, intervals and the t distribution, p-values and permutation tests, multiple testing, and least-squares regression.

</div>
