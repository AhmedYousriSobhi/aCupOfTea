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
    - how-far-from-the-middle
    - where-do-you-stand
    - counting-the-ways
    - the-test-that-was-99-percent-accurate
    - what-to-expect
    - coins-and-calls
    - the-bell-curve
    - why-averages-behave
    - how-sure-are-you
    - the-courtroom-for-numbers
    - two-things-moving-together
    - the-map-of-leaf-and-kettle
---

# Probability & Statistics, One Sip at a Time

Most people do not struggle with statistics because the formulas are hard. They struggle because the **ideas** arrive before the reason for them. Why divide by `n − 1`? Why does a p-value not mean what it sounds like? Why is a 99% accurate test often wrong?

This series goes the other way. Every page starts with something that **goes wrong** for a small, invented tea shop, and the idea shows up as the fix. The formulas come last, when you already know what they are for.

## Feeling lost? Start here

If the series feels like too many numbers, too many graphs and too many steps, hold on to three ideas. Everything else is built from them.

1. **A summary is a stand-in for a crowd.** Mean, median and mode are not rival formulas. They are one question, *how much should a long walk hurt?*, asked three ways. Spread is how badly the stand-in still misses. ([Part 5](/fields/data-science/probability-statistics/how-far-from-the-middle.md))
2. **Graphs are one table seen three ways.** The histogram shows how much lives where. The ogive shows how many are at or below. The box plot is the ogive keeping only its landmarks. Look first, with the histogram. ([Part 6](/fields/data-science/probability-statistics/where-do-you-stand.md))
3. **A value has no meaning without its crowd.** Ask "better than what?", then place it with a rank (percentile) or a distance (z-score).

Then keep [The Map of Leaf & Kettle](/fields/data-science/probability-statistics/the-map-of-leaf-and-kettle.md) open as a reference. It lays every idea in the series out as rooms of one shop (nine downstairs, nine upstairs for chance), so you recall a room instead of a formula.

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
| 1 | [Stir the Pot First](/fields/data-science/probability-statistics/stir-the-pot-population-and-sampling.md) | Why can a small, well-chosen sample beat a huge careless one? | Written |
| 2 | [Mira's Notebook](/fields/data-science/probability-statistics/data-types-and-frequency-tables.md) | What kind of data is this, and how do I count it honestly? | Written |
| 3 | [Draw It Before You Describe It](/fields/data-science/probability-statistics/draw-it-before-you-describe-it.md) | Which picture answers which question: histogram, polygon or ogive? | Written |
| 4 | [The Number on the Tin](/fields/data-science/probability-statistics/the-number-on-the-tin.md) | What does "typical" mean: mean, median or mode? | Written |
| 5 | [How Far From the Middle?](/fields/data-science/probability-statistics/how-far-from-the-middle.md) | Why are there three middles and so many spreads? Variance, SD, IQR and the mystery of `n − 1` | Written |
| 6 | [Where Do You Stand?](/fields/data-science/probability-statistics/where-do-you-stand.md) | How does one value find its place in a crowd? Percentiles, z-scores and the box plot | Written |
| 7 | [Counting the Ways](/fields/data-science/probability-statistics/counting-the-ways.md) | What is a probability, and why do "or" and "and" add and multiply? | Written |
| 8 | [The Test That Was 99% Accurate](/fields/data-science/probability-statistics/the-test-that-was-99-percent-accurate.md) | Why is an accurate test so often wrong? Conditional probability and Bayes' rule | Written |
| 9 | [What to Expect](/fields/data-science/probability-statistics/what-to-expect.md) | What does "expected" mean? Random variables, expected value and variance | Written |
| 10 | [Coins and Calls](/fields/data-science/probability-statistics/coins-and-calls.md) | Which recipe fits which question? The binomial and Poisson distributions | Written |
| 11 | [The Bell Curve](/fields/data-science/probability-statistics/the-bell-curve.md) | Where does the bell come from, and what is probability as area? The normal distribution | Written |
| 12 | [Why Averages Behave](/fields/data-science/probability-statistics/why-averages-behave.md) | Why does an average wobble less than a single value? Sampling distributions and the central limit theorem | Written |
| 13 | [How Sure Are You?](/fields/data-science/probability-statistics/how-sure-are-you.md) | How do you say "about this, give or take"? Confidence intervals and the bootstrap | Written |
| 14 | [The Courtroom for Numbers](/fields/data-science/probability-statistics/the-courtroom-for-numbers.md) | Could plain luck have done this? Hypothesis tests, p-values and how they get misused | Written |
| 15 | [Two Things Moving Together](/fields/data-science/probability-statistics/two-things-moving-together.md) | Do two columns rise and fall together, and what does that not prove? Correlation and regression | Written |
| Ref | [The Map of Leaf & Kettle](/fields/data-science/probability-statistics/the-map-of-leaf-and-kettle.md) | Every idea so far as a memory palace, a decision chart and a definitions sheet | Grows with the series |

The order is deliberate. Pages 1 to 6 are about **describing what you have**: where the data came from, what kind it is, what it looks like, where its middle is, how spread out it is, and where one value sits within it. Pages 7 to 11 build the language of **chance**: counting the ways, updating on evidence, what to expect, the common distributions and the bell curve. Pages 12 to 14 join the two: using a sample to make an honest statement about something you cannot fully see. Page 15 puts two columns side by side. Each chance page reuses an idea from the first half (the expected value is the mean again, the z-score finally meets the bell), so there is less new to memorize than the list suggests.

## Conventions

- Characters are invented. The numbers in the stories are chosen so you can do the arithmetic yourself.
- Where a story borrows a real event, the sources are listed at the bottom of that page.
- `x̄` is a sample mean, `μ` is a population mean, `n` is a sample size, `N` is a population size, `f` is a frequency and `M` is a class midpoint.
- The same small data sets come back from page to page, so a table you met earlier may turn out to have a surprise in it later.