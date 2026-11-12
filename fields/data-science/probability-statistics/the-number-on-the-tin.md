---
id: the-number-on-the-tin
title: "The Number on the Tin: Mean, Median and Mode"
sidebar_label: The number on the tin
summary: 'Why a perfectly computed average can describe nobody: the mean as a balance point, the median, the mode, how outliers pull them apart, and how to choose.'
level: beginner
type: concept
domains:
  - statistics
tags:
  - statistics
relations:
  related:
    - probability-statistics-series
    - draw-it-before-you-describe-it
    - data-types-and-frequency-tables
---

# The Number on the Tin: Mean, Median and Mode

> **Part of the [Probability & Statistics](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/data-science/probability-statistics/README.md) series.** It continues from [Draw It Before You Describe It](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/data-science/probability-statistics/draw-it-before-you-describe-it.md), where Ravi asked for "one number" for a typical day. The scenario is invented, and every figure can be checked by hand.

## Table of Contents

- [Prologue: the number on the tin](#prologue-the-number-on-the-tin)
- [Three ways to say "typical"](#three-ways-to-say-typical)
- [The mean: the balance point](#the-mean-the-balance-point)
- [The mean of a table](#the-mean-of-a-table)
- [The median: the middle value](#the-median-the-middle-value)
- [The median of a grouped table](#the-median-of-a-grouped-table)
- [The mode: the most common value](#the-mode-the-most-common-value)
- [When the three disagree](#when-the-three-disagree)
- [What grouping costs you](#what-grouping-costs-you)
- [Choosing the right middle](#choosing-the-right-middle)
- [Check yourself](#check-yourself)
- [Back to the story](#back-to-the-story)
- [Cheat sheet](#cheat-sheet)
- [Answers](#answers)

* * *

## Prologue: the number on the tin

Mira is about to print the labels for her new smoky blend. The tins will carry a line she has always wanted: **"Typical taster score: __."**

She has the 20 tasting scores from earlier (on a 0 to 120 scale), and she knows how to find the average: add them up and divide.

```
52, 55, 55, 58, 58, 58, 62, 62, 62, 71, 71, 89, 89, 89, 93, 93, 94, 94, 95, 104
```

The sum is 1,504, and 1,504 divided by 20 is **75.2**. She sends "Typical taster score: 75" to the printer.

Then she remembers the table she built a few days ago. Scores in the range 74 to 84 had a frequency of zero. **Not one taster gave the blend anything close to 75.** The "typical" score printed on every tin is a score nobody gave.

The arithmetic was right. The question she asked was not the question she meant. The rest of this page is about what "typical" can mean, and why there are three answers.

* * *

## Three ways to say "typical"

| Measure | Plain-language idea | Symbol |
|---|---|---|
| **Mean** (arithmetic mean, the "average") | The balance point of the data | `x̄` for a sample, `μ` for a population |
| **Median** | The middle value when the data are sorted | `m` or `M_D` |
| **Mode** | The most frequent value | |

They are all **measures of central tendency**: single numbers that try to stand in for the center of a data set. They sometimes agree, and the interesting cases are the ones where they do not.

* * *

## The mean: the balance point

For a list of values, add them up and divide by how many there are:

```
x̄ = Σx / n
```

Take eight tasting scores: 70, 65, 69, 85, 94, 62, 79, 100. The sum is 624, so `x̄ = 624 / 8 = 78`.

Here is the picture to keep. Imagine each value as a weight on a seesaw at its position on a number line. The mean is the point where the seesaw **balances**. You can check this with the **deviations**, how far each value sits from the mean:

| Score | Deviation `x − 78` |
|---|---|
| 70 | −8 |
| 65 | −13 |
| 69 | −9 |
| 85 | +7 |
| 94 | +16 |
| 62 | −16 |
| 79 | +1 |
| 100 | +22 |
| **Sum** | **0** |

The deviations always add to zero. The pull from the values below the mean equals the pull from the values above it. That is what "balance point" means, and it also explains why a single far-away value drags the mean so strongly: it is a heavy weight on a long arm.

* * *

## The mean of a table

When the data come as a frequency table, you do not need the raw list. Each value counts as many times as its frequency, so the mean is a **weighted average**.

For a **grouped** table, you do not know the exact values inside a class, so each class stands in for all of its values with its **midpoint** `M`:

```
x̄ = Σ(f × M) / Σf
```

An example: 50 visits to the shop, grouped by minutes spent inside.

| Class boundaries | Frequency `f` | Midpoint `M` | `f × M` |
|---|---|---|---|
| 9.5 to 12.5 | 4 | 11 | 44 |
| 12.5 to 15.5 | 12 | 14 | 168 |
| 15.5 to 18.5 | 20 | 17 | 340 |
| 18.5 to 21.5 | 14 | 20 | 280 |
| **Total** | **50** | | **832** |

`x̄ = 832 / 50 = 16.64` minutes.

Think of each class as casting `f` votes, all for its midpoint. The classes with more visits get more say. Because the midpoint is a stand-in for the unknown values, this mean is an **estimate**, a point returned to in "What grouping costs you".

* * *

## The median: the middle value

Sort the data. The **median** is the value with half of the data on each side.

For `n` values in ascending order:

```
n odd  :  median = the value at position (n + 1) / 2
n even :  median = the average of the values at positions n/2 and n/2 + 1
```

Two small cases:

- **Odd:** {3, 2, 6, 2, 7}. Sorted: 2, 2, 3, 6, 7. With `n = 5`, the position is `(5 + 1) / 2 = 3`, so the median is **3**.
- **Even:** add an 8: 2, 2, 3, 6, 7, 8. With `n = 6`, average the 3rd and 4th values: `(3 + 6) / 2 =` **4.5**. With an even count the median need not be one of the data values.

Back to the eight tasting scores. Sorted: 62, 65, 69, 70, 79, 85, 94, 100. The 4th and 5th values are 70 and 79, so the median is `(70 + 79) / 2 = 74.5`. The mean was 78. They are close but not equal.

**Now the experiment that explains why the median exists.** Change the 100 into a 1,000, as if one taster had hit the wrong key:

| | Original | With the typo |
|---|---|---|
| Mean | 78 | `1,524 / 8 =` **190.5** |
| Median | 74.5 | **74.5** (the 4th and 5th values are still 70 and 79) |

One wrong entry moved the mean by more than 110 points and did not move the median at all. The median depends only on the **order** of the values, not on how far out the extremes are. That makes it **resistant** to outliers.

* * *

## The median of a grouped table

With a grouped table, the raw values are gone, so the median is found in three steps.

An example: quality scores of 21 batches.

| Class limits | Class boundaries | Frequency `f` | Cumulative `CF` |
|---|---|---|---|
| 51 to 55 | 50.5 to 55.5 | 2 | 2 |
| 56 to 60 | 55.5 to 60.5 | 7 | 9 |
| 61 to 65 | 60.5 to 65.5 | 8 | 17 |
| 66 to 70 | 65.5 to 70.5 | 4 | 21 |

1. **Find the target position:** `N / 2 = 21 / 2 = 10.5`.
2. **Find the median class:** the first class whose cumulative frequency reaches the target. The cumulative counts are 2, 9, **17**, so it is the class **60.5 to 65.5**.
3. **Interpolate inside it:**

```
median = L + ((N/2 − cf) / f) × h
```

| Symbol | Meaning | Value here |
|---|---|---|
| `L` | Lower boundary of the median class | 60.5 |
| `N/2` | Half the total frequency | 10.5 |
| `cf` | Cumulative frequency of the class **before** the median class | 9 |
| `f` | Frequency of the median class | 8 |
| `h` | Class width | 5 |

```
median = 60.5 + ((10.5 − 9) / 8) × 5 = 60.5 + 0.1875 × 5 = 60.5 + 0.9375 = 61.4375
```

**Why this formula works.** Nine values lie below the class. The median is the 10.5th, so it needs `10.5 − 9 = 1.5` more values. The median class holds 8 values spread across a width of 5. If they are spread evenly, 1.5 values out of 8 means going `1.5 / 8 = 18.75%` of the way across, which is 0.9375 units above the lower boundary of 60.5.

That is exactly the ogive reading from the previous page, written as a formula. Reading the median from the cumulative frequency curve and applying this formula are **the same calculation**: both draw a straight line across the class. For the 50 days of customers, `N/2 = 25` falls in the class 109.5 to 114.5 with `cf = 10`, `f = 18` and `h = 5`:

```
median = 109.5 + ((25 − 10) / 18) × 5 ≈ 113.7
```

This matches the value read from the ogive, as it must.

* * *

## The mode: the most common value

The **mode** is the value that occurs most often. Consider 2, 2, 2, 3, 3, 3, 4, 7, 7, 8, 10. Both 2 and 3 appear three times, and nothing appears more often, so there are **two modes**: the data are **bimodal**. With more than two, the data are **multimodal**.

What the mode can do that the others cannot:

- **It works for any kind of data.** Among the 20 customers' favorite blends, Green was chosen by 6, more than any other. The mean and median of a list of blend names do not exist, but the mode does.
- **It may not exist.** In the eight scores (70, 65, 69, 85, 94, 62, 79, 100), every value appears once, so there is no mode.
- **It may not be unique.** The 20 tasting scores have three values that tie at three appearances each: 58, 62 and 89.
- **For a grouped table, use the modal class:** the class with the highest frequency. In the 50 days it is 109.5 to 114.5, with 18 days.

* * *

## When the three disagree

Here are the three measures for three data sets from this series:

| Data | Mean | Median | Mode |
|---|---|---|---|
| 2, 2, 2, 3, 3, 3, 4, 7, 7, 8, 10 | 4.64 | 3 | 2 and 3 |
| 50 days of customers (grouped) | 114.2 | 113.7 | modal class 109.5 to 114.5 |
| The 20 tasting scores | 75.2 | 71 | 58, 62 and 89 |

(The mean of the 50 days is `5,710 / 50 = 114.2`, using the midpoints from the previous page.)

Look at the first two rows. In both, `mean > median`, and in both there is a **tail on the right**: the 10 in the first set, and the thin run of busy days stretching toward 134 in the second. The mean is the balance point, so a long tail on one side drags it toward that side. The median only counts positions, so it hardly moves.

A rule of thumb that follows from this:

| Pattern | What it suggests |
|---|---|
| `mean > median` | A tail to the **right** (a few large values) |
| `mean < median` | A tail to the **left** (a few small values) |
| `mean ≈ median` | Roughly symmetric |

It is a rule of thumb, not a law. Odd shapes can break it.

The third row is Mira's tin. Here the mean (75.2) and median (71) are not far apart, and yet **both** are misleading, for a different reason: the data have **two clumps**. Nine tasters scored 62 or less, nine scored 89 or more, and only two sit in between. No single "middle" can describe a data set with two separate centers.

* * *

## What grouping costs you

The grouped formulas are estimates. Mira can check how good they are, because she has both the raw scores and a grouped version of the same 20 scores:

| Class boundaries | `f` | Midpoint `M` | `f × M` | `CF` |
|---|---|---|---|---|
| 51.5 to 62.5 | 9 | 57 | 513 | 9 |
| 62.5 to 73.5 | 2 | 68 | 136 | 11 |
| 73.5 to 84.5 | 0 | 79 | 0 | 11 |
| 84.5 to 95.5 | 8 | 90 | 720 | 19 |
| 95.5 to 106.5 | 1 | 101 | 101 | 20 |

- **Grouped mean:** `1,470 / 20 = 73.5`, against the true 75.2.
- **Grouped median:** `N/2 = 10` falls in the second class, so `62.5 + ((10 − 9) / 2) × 11 = 62.5 + 5.5 = 68.0`, against the true 71.

Both are off, because the formulas assume the values sit at the midpoint (for the mean) or are spread evenly (for the median), and Mira's values do neither. The more clumped the real data are inside a class, the larger the error. The error is the price of having only the table, and if you still hold the raw data, use it.

* * *

## Choosing the right middle

| Your data | Best choice | Reason |
|---|---|---|
| Nominal (blend names) | **Mode** | No order and no arithmetic, so it is the only one that exists |
| Ordinal (mild, medium, strong) | **Median** (and mode) | Order exists, but distances between levels are not measured |
| Quantitative, roughly symmetric | **Mean** | Uses every value, and is the natural balance point |
| Quantitative, skewed or with outliers | **Median** | It does not chase the extremes |
| Two or more clumps | **None alone.** Describe the clumps | A single center hides the structure |

* * *

## Check yourself

1. Find the mean and median of 4, 8, 6, 5, 3, 200. Which one describes a typical value, and why?
2. For 20 visits, a grouped table has boundaries 0.5 to 5.5 (frequency 3), 5.5 to 10.5 (9), 10.5 to 15.5 (6) and 15.5 to 20.5 (2). Estimate the mean and the median, and name the modal class.
3. Find the modes, the median and the mean of 5, 5, 7, 9, 9, 12.
4. Which measure of center works for the favorite-blend column, and why?
5. True or false: the mean computed from a grouped table is exact.
6. A café reports an average order of 12.40 but a median order of 8.10. What does the gap tell you?

* * *

## Back to the story

Mira calls the printer before the labels go out.

She has a better question now. The tin is supposed to tell a customer what to expect, and "75" does not tell anyone what to expect, because nobody scored the blend 75. The data were never one group with a typical member. They were two groups: nine tasters who scored the blend low and nine who scored it high, with two in between.

So she changes the line. The new label says: **"Divides opinion: about half of our tasters loved it, about half did not."** Underneath, in small print, she adds the median, 71, for the customers who like a number.

Customers pick up the tin, read the line, and decide which half they are. The "typical" score was never missing from the data. It was hiding in the assumption that there was one.

Which raises the next question. Her 20 scores run from 52 to 104, and Ravi's customer counts run from 100 to 134. Both have a center, but they are not equally *spread out*, and the spread matters just as much as the center. That is the next cup.

* * *

## Cheat sheet

```
Mean    x̄ = Σx / n                         balance point; deviations add to 0; pulled by outliers/tails
Grouped mean   x̄ = Σ(f × M) / Σf           weighted average of midpoints (an estimate)

Median  sort first
  n odd : value at position (n+1)/2
  n even: average of positions n/2 and n/2 + 1
  grouped: median class = first class with CF >= N/2
           median = L + ((N/2 − cf) / f) × h        (= reading the ogive with a ruler)

Mode    most frequent value; may be absent or multiple; modal class for grouped data

mean > median -> right tail      mean < median -> left tail      two clumps -> describe both
Nominal: mode   Ordinal: median   Symmetric numbers: mean   Skewed or outliers: median
```

* * *

## Answers

1. The sum is 226, so the **mean is `226 / 6 ≈ 37.7`**. Sorted: 3, 4, 5, 6, 8, 200. The median is the average of the 3rd and 4th values, `(5 + 6) / 2 =` **5.5**. The median describes a typical value. The mean is dominated by the 200, and five of the six values are below 9.
2. Midpoints are 3, 8, 13 and 18, so `Σ f×M = 9 + 72 + 78 + 36 = 195`, and the **mean ≈ 195 / 20 = 9.75**. For the median, `N/2 = 10`. Cumulative frequencies are 3, 12, 18, 20, so the median class is 5.5 to 10.5 with `cf = 3`, `f = 9`, `h = 5`. Then `5.5 + ((10 − 3) / 9) × 5 = 5.5 + 3.89 ≈` **9.39**. The **modal class** is 5.5 to 10.5 (frequency 9).
3. The values 5 and 9 each appear twice, so the **modes are 5 and 9** (bimodal). The sorted list has `n = 6`, so the median is `(7 + 9) / 2 =` **8**. The sum is 47, so the **mean is `47 / 6 ≈ 7.83`**.
4. The **mode**. Blend names are nominal: they have no order and cannot be added, so only "which one appears most" is meaningful.
5. **False.** It is an estimate, because the formula replaces every value in a class with that class's midpoint.
6. The mean is much higher than the median, which points to a **tail on the right**: a few very large orders pull the average up while most orders are small. The median describes the typical order better.
