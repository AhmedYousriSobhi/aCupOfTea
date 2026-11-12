---
id: probability-statistics-series
title: "Probability & Statistics, One Sip at a Time"
sidebar_label: Probability & Statistics
summary: 'A slow-brewed series on the ideas in probability and statistics that make people say "wait, why?", each one told as a small story in a tea shop.'
level: beginner
type: guide
domains:
  - statistics
tags:
  - statistics
relations:
  related:
    - stir-the-pot-population-and-sampling
    - data-types-and-frequency-tables
    - draw-it-before-you-describe-it
    - the-number-on-the-tin
---

# Probability & Statistics, One Sip at a Time

Most people do not struggle with statistics because the formulas are hard. They struggle because the **ideas** arrive before the reason for them. Why divide by `n − 1`? Why does a p-value not mean what it sounds like? Why is a 99% accurate test often wrong?

This series goes the other way. Every page starts with something that **goes wrong** for a small, invented tea shop, and the idea shows up as the fix. The formulas come last, when you already know what they are for.

## How each page is built

1. **A scene.** Mira, who runs a tea shop called Leaf & Kettle, runs into a problem.
2. **The wrong instinct.** What most of us would do, and why it fails.
3. **One mental model.** The idea that repairs the story.
4. **The mechanics.** Definitions, formulas and worked tables, with numbers you can check by hand.
5. **Check yourself.** A few questions, with answers at the bottom.
6. **Back to the story.** The page returns to the opening scene and resolves it with what you have just learned, usually by handing the next question to the next page.
7. **A cheat sheet** you can read in thirty seconds before you need it.

## The pots on the shelf

| # | Page | The question it answers | Status |
|---|---|---|---|
| 1 | [Stir the Pot First](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/data-science/probability-statistics/stir-the-pot-population-and-sampling.md) | Why can a small, well-chosen sample beat a huge careless one? | Written |
| 2 | [Mira's Notebook](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/data-science/probability-statistics/data-types-and-frequency-tables.md) | What kind of data is this, and how do I count it honestly? | Written |
| 3 | [Draw It Before You Describe It](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/data-science/probability-statistics/draw-it-before-you-describe-it.md) | Which picture answers which question: histogram, polygon or ogive? | Written |
| 4 | [The Number on the Tin](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/data-science/probability-statistics/the-number-on-the-tin.md) | What does "typical" mean: mean, median or mode? | Written |
| 5 | How Far From the Middle? | Variance, standard deviation, IQR, and the mystery of `n − 1` | Planned |
| 6 | Where Do You Stand? | Percentiles, z-scores and box plots | Planned |
| 7 | Counting the Ways | Sample spaces, events and the rules of probability | Planned |
| 8 | The Test That Was 99% Accurate | Conditional probability and Bayes' rule | Planned |
| 9 | What to Expect | Random variables, expected value and variance | Planned |
| 10 | Coins, Calls and Bell Curves | Binomial, Poisson and normal distributions | Planned |
| 11 | Why Averages Behave | Sampling distributions and the central limit theorem | Planned |
| 12 | How Sure Are You? | Confidence intervals | Planned |
| 13 | The Courtroom for Numbers | Hypothesis tests, p-values and how they get misused | Planned |

The order is deliberate. Pages 1 to 6 are about **describing what you have**: where the data came from, what kind it is, what it looks like, where its middle is, how spread out it is, and where one value sits within it. Pages 7 to 10 build the language of **chance**. Pages 11 to 13 join the two: using a sample to make an honest statement about something you cannot fully see.

## Conventions

- Characters are invented. The numbers in the stories are chosen so you can do the arithmetic yourself.
- Where a story borrows a real event, the sources are listed at the bottom of that page.
- `x̄` is a sample mean, `μ` is a population mean, `n` is a sample size, `N` is a population size, `f` is a frequency and `M` is a class midpoint.
- The same small data sets come back from page to page, so a table you met earlier may turn out to have a surprise in it later.