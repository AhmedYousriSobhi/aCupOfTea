
<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/fields/">Fields</a> / <a href="#/fields/data-science/">Data Science</a></nav>

# Probability & Statistics, One Sip at a Time

<!-- related-block -->
<div class="reading-time">Beginner · Guide · 6 min read · Updated 24 Nov 2026</div>
<!-- related-block -->
<div class="tag-chips"><a class="chip" href="#/.docs/generated/explore/tags/statistics">statistics</a></div>


Most people do not struggle with statistics because the formulas are hard. They struggle because the **ideas** arrive before the reason for them. Why divide by `n − 1`? Why does a p-value not mean what it sounds like? Why is a 99% accurate test often wrong?

This series goes the other way. Every page starts with something that **goes wrong** for a small, invented tea shop, and the idea shows up as the fix. The formulas come last, when you already know what they are for.

## Feeling lost? Start here

If the series feels like too many numbers, too many graphs and too many steps, hold on to three ideas. Everything else is built from them.

1. **A summary is a stand-in for a crowd.** Mean, median and mode are not rival formulas. They are one question, *how much should a long walk hurt?*, asked three ways. Spread is how badly the stand-in still misses. ([Part 5](/fields/data-science/probability-statistics/describing-data/spread-and-position.md))
2. **Graphs are one table seen three ways.** The histogram shows how much lives where. The ogive shows how many are at or below. The box plot is the ogive keeping only its landmarks. Look first, with the histogram. ([Part 6](/fields/data-science/probability-statistics/describing-data/spread-and-position.md))
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
| 1-2 | [Samples, Data Types and Tables](/fields/data-science/probability-statistics/describing-data/samples-data-types-and-tables.md) | Who did you ask, what kind of column is it, and how do you count it? Sampling, data types, frequency and grouped tables | Written |
| 3-4 | [Pictures and the Middle](/fields/data-science/probability-statistics/describing-data/pictures-and-the-middle.md) | What does the table look like, and what is "typical"? Histogram, polygon, ogive, mean, median and mode | Written |
| 5-6 | [Spread and Position](/fields/data-science/probability-statistics/describing-data/spread-and-position.md) | How far from the middle, and where does one value stand? Variance, `n − 1`, percentiles, z-scores, box plot | Written |
| 7-8 | [Counting and Conditioning](/fields/data-science/probability-statistics/probability/counting-and-conditioning.md) | What is a probability, and why is an accurate test so often wrong? "Or", "and", conditional probability and Bayes' rule | Written |
| 9-10 | [Expectation and the Two Count Recipes](/fields/data-science/probability-statistics/probability/expectation-binomial-poisson.md) | What does "expected" mean, and which recipe fits which count? Expected value, variance, the binomial and Poisson distributions | Written |
| 11 | [The Bell Curve](/fields/data-science/probability-statistics/probability/the-bell-curve.md) | Where does the bell come from, and what is probability as area? The normal distribution | Written |
| 12-13 | [Averages and Intervals](/fields/data-science/probability-statistics/inference/averages-and-intervals.md) | Why does an average wobble less than a value, and how sure can you be? Sampling distributions, the central limit theorem, confidence intervals | Written |
| 14 | [The Courtroom for Numbers](/fields/data-science/probability-statistics/inference/the-courtroom-for-numbers.md) | Could plain luck have done this? Hypothesis tests, p-values and how they get misused | Written |
| 15 | [Two Things Moving Together](/fields/data-science/probability-statistics/inference/two-things-moving-together.md) | Do two columns rise and fall together, and what does that not prove? Correlation and regression | Written |
| Ref | [The Map of Leaf & Kettle](/fields/data-science/probability-statistics/the-map-of-leaf-and-kettle.md) | Every idea so far as a memory palace, a decision chart and a definitions sheet | Grows with the series |

The order is deliberate. Pages 1 to 6 are about **describing what you have**: where the data came from, what kind it is, what it looks like, where its middle is, how spread out it is, and where one value sits within it. Pages 7 to 11 build the language of **chance**: counting the ways, updating on evidence, what to expect, the common distributions and the bell curve. Pages 12 to 14 join the two: using a sample to make an honest statement about something you cannot fully see. Page 15 puts two columns side by side. Each chance page reuses an idea from the first half (the expected value is the mean again, the z-score finally meets the bell), so there is less new to memorize than the list suggests.

## Where things live

| Folder | Parts | Also there |
|---|---|---|
| [Describing data](/fields/data-science/probability-statistics/describing-data/README.md) | 1 to 6 | technical reference, quick guide, sampling methods, grouped tables and describing-data labs |
| [Probability](/fields/data-science/probability-statistics/probability/README.md) | 7 to 11 | technical reference, quick guide, expected value, Bayes and distributions labs |
| [Inference](/fields/data-science/probability-statistics/inference/README.md) | 12 to 15 | technical reference, quick guide, sampling, permutation and correlation labs |

Each story page shows its lab inline where it helps; the folder indexes link to each quick guide, where all of that folder's labs sit under "Try it". For a plain syllabus of the whole field, see [Statistics](/fields/statistics/README.md).

## Conventions

- Characters are invented. The numbers in the stories are chosen so you can do the arithmetic yourself.
- Where a story borrows a real event, the sources are listed at the bottom of that page.
- `x̄` is a sample mean, `μ` is a population mean, `n` is a sample size, `N` is a population size, `f` is a frequency and `M` is a class midpoint.
- The same small data sets come back from page to page, so a table you met earlier may turn out to have a surprise in it later.

<!-- related-block -->
<div class="see-also">

**See also**

- [Averages and Intervals: Why Averages Behave and How Sure You Can Be](/fields/data-science/probability-statistics/inference/averages-and-intervals.md) — An average is itself random: its spread shrinks as sigma over root n and its shape tends to a bell. A confidence interval turns that wobble into a give-or-take, and bias is invisible to it.
- [Counting and Conditioning: Why a 99% Accurate Test Is Usually Wrong](/fields/data-science/probability-statistics/probability/counting-and-conditioning.md) — Probability is a share of the equally likely ways, so "or" adds, "and" multiplies and "at least one" is 1 minus none. Conditioning shrinks the crowd, and Bayes' rule reads that count backwards.
- [Expectation and the Two Count Recipes: Binomial and Poisson](/fields/data-science/probability-statistics/probability/expectation-binomial-poisson.md) — Expected value is the data's seesaw with probability as the weight, not the likeliest outcome. Binomial and Poisson are recipes for a count; each is right only as far as its assumptions hold.
- [Pictures and the Middle: Histogram, Polygon, Ogive, and What 'Typical' Means](/fields/data-science/probability-statistics/describing-data/pictures-and-the-middle.md) — Draw the table before you summarise it: histogram for amount, polygon for comparison, ogive for up to here. Then "typical" is three questions, mean, median and mode, and none answers two clumps.
- [Samples, Data Types and Tables: Who You Asked, What Kind of Column, How to Count It](/fields/data-science/probability-statistics/describing-data/samples-data-types-and-tables.md) — A sample speaks for a crowd only if you chose it fairly. The kind of column decides which arithmetic is allowed, and a frequency table counts it without losing the shape, if the drawers touch.
- [Spread and Position: Variance, n − 1, Percentiles, Z-Scores and the Box Plot](/fields/data-science/probability-statistics/describing-data/spread-and-position.md) — Mean, median and mode are three attitudes to how a long walk hurts; spread is the walking left over. A value then has a position only in its crowd: rank (percentile) or distance (z-score).
- [The Bell Curve: Probability as Area, and One Ruler for Every Bell](/fields/data-science/probability-statistics/probability/the-bell-curve.md) — Many small nudges add up to a bell. For continuous data probability is area, and the z-score makes every bell the same bell, so one table serves all of them, until the data are not a bell.
- [The Courtroom for Numbers: Could Plain Luck Do This?](/fields/data-science/probability-statistics/inference/the-courtroom-for-numbers.md) — A hypothesis test asks one question: could plain luck have produced a difference this big? Shuffle the labels and count. What the p-value is, what it is not, and how testing twenty things fools you.
- [The Map of Leaf & Kettle: Every Idea So Far in One Walk Through the Shop](/fields/data-science/probability-statistics/the-map-of-leaf-and-kettle.md) — A concept map, decision chart and definitions sheet for the whole series, as a memory palace in one tea shop: nine rooms for describing data, an upstairs for chance.
- [Two Things Moving Together: Correlation and the Line](/fields/data-science/probability-statistics/inference/two-things-moving-together.md) — Correlation is the average product of paired z-scores, a number about straight-line togetherness only. The regression line is least squared walking applied to a line. Graph first, always.

</div>
<!-- related-block -->
<div class="mentioned-in">

**Mentioned in**

- [Averages and Intervals: Why Averages Behave and How Sure You Can Be](/fields/data-science/probability-statistics/inference/averages-and-intervals.md) — An average is itself random: its spread shrinks as sigma over root n and its shape tends to a bell. A confidence interval turns that wobble into a give-or-take, and bias is invisible to it.
- [Counting and Conditioning: Why a 99% Accurate Test Is Usually Wrong](/fields/data-science/probability-statistics/probability/counting-and-conditioning.md) — Probability is a share of the equally likely ways, so "or" adds, "and" multiplies and "at least one" is 1 minus none. Conditioning shrinks the crowd, and Bayes' rule reads that count backwards.
- [Expectation and the Two Count Recipes: Binomial and Poisson](/fields/data-science/probability-statistics/probability/expectation-binomial-poisson.md) — Expected value is the data's seesaw with probability as the weight, not the likeliest outcome. Binomial and Poisson are recipes for a count; each is right only as far as its assumptions hold.
- [Pictures and the Middle: Histogram, Polygon, Ogive, and What 'Typical' Means](/fields/data-science/probability-statistics/describing-data/pictures-and-the-middle.md) — Draw the table before you summarise it: histogram for amount, polygon for comparison, ogive for up to here. Then "typical" is three questions, mean, median and mode, and none answers two clumps.
- [Samples, Data Types and Tables: Who You Asked, What Kind of Column, How to Count It](/fields/data-science/probability-statistics/describing-data/samples-data-types-and-tables.md) — A sample speaks for a crowd only if you chose it fairly. The kind of column decides which arithmetic is allowed, and a frequency table counts it without losing the shape, if the drawers touch.
- [Spread and Position: Variance, n − 1, Percentiles, Z-Scores and the Box Plot](/fields/data-science/probability-statistics/describing-data/spread-and-position.md) — Mean, median and mode are three attitudes to how a long walk hurts; spread is the walking left over. A value then has a position only in its crowd: rank (percentile) or distance (z-score).
- [Statistics](/fields/statistics/README.md)
- [The Bell Curve: Probability as Area, and One Ruler for Every Bell](/fields/data-science/probability-statistics/probability/the-bell-curve.md) — Many small nudges add up to a bell. For continuous data probability is area, and the z-score makes every bell the same bell, so one table serves all of them, until the data are not a bell.
- and 2 more

</div>
