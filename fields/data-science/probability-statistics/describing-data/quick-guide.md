---
id: describing-data-quick-guide
title: "Summarise a Data Set: Which Number, Which Picture"
sidebar_label: "Quick guide: describing data"
order: 5
summary: A cheat sheet for parts 1 to 6 - choose a sampling method, classify the data, pick the picture, pick the middle and the spread, and place one value in its crowd.
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
    - samples-data-types-and-tables
    - pictures-and-the-middle
    - spread-and-position
    - describing-data-technical-reference
---

# Summarise a Data Set: Which Number, Which Picture

> **Quick guide for** [Samples, Data Types and Tables](/fields/data-science/probability-statistics/describing-data/samples-data-types-and-tables.md) (parts 1 and 2), [Pictures and the Middle](/fields/data-science/probability-statistics/describing-data/pictures-and-the-middle.md) (parts 3 and 4) and [Spread and Position](/fields/data-science/probability-statistics/describing-data/spread-and-position.md) (parts 5 and 6).
> Python 3, standard library only. Formal statements: [technical reference](/fields/data-science/probability-statistics/describing-data/technical-reference.md).

## 1. Sample

| Two questions | Method |
|---|---|
| No groups, by chance | simple random |
| No groups, by pattern | systematic: `k = N / n`, random start |
| Groups, every group, some people | stratified: `n_h = n * N_h / N` |
| Groups, some groups, every person | cluster |

Bias does not shrink with `n`.

## 2. Classify and count

Same or different: nominal. Which first: ordinal. How far apart: discrete (counted) or continuous (measured). Digits used as labels are nominal.

Checks: `sum of f = n`, `sum of f/n = 1`, last cumulative frequency `= n`. Grouped: `h = Range / k`, rounded up.

## 3. Draw

| Question | Picture |
|---|---|
| How much lives here? | histogram (area = count) |
| How do two crowds compare? | frequency polygon |
| How many at or below here? | ogive: `(upper boundary, CF)` |

## 4. Middle and spread

| Data | Middle | Spread |
|---|---|---|
| Nominal | mode | none |
| Ordinal | median | IQR |
| Symmetric numbers | mean | SD |
| Skewed or outliers | median | IQR |

`mean > median` means a right tail. Grouped mean: `sum of (f * M) / sum of f`.

```python
import statistics as st
data = [2, 4, 9]
st.pvariance(data)   # divides by n: "this is everyone"
st.variance(data)    # divides by n - 1: "this is a sample" -> 13
```

## 5. Place one value

`percentile rank = (below + 0.5 * equal) / n * 100`; `z = (x - mean) / SD`.

```python
d = list(range(1, 10))
st.quantiles(d, n=4)                        # [2.5, 5.0, 7.5]
st.quantiles(d, n=4, method='inclusive')    # [3.0, 5.0, 7.0]
```

Box plot fences: `Q1 - 1.5 * IQR` and `Q3 + 1.5 * IQR`. Say which quartile method you used.

## Symptoms

| What you see | Likely cause | Fix |
|---|---|---|
| Average describes nobody | Two clumps | Histogram first, describe both |
| Mean and median far apart | Long tail or outlier | Report the median |
| Bigger sample, same wrong answer | Biased frame | Fix how you choose, not how many |
| Quartiles differ between tools | Different method | Pick one and say which |

> [!WARNING]
> Divide by `n` only if the data are everyone; divide by `n - 1` for a sample. Look at the picture before you trust any summary number.

## Try it

[Describing data lab](/fields/data-science/probability-statistics/labs/describing.html#embed ':ignore')

**Why it works:** the six story pages above. Next: [Probability](/fields/data-science/probability-statistics/probability/README.md).
