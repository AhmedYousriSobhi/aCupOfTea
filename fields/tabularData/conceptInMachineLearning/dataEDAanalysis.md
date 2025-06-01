# Tabular Data - Concepts in Machine Learning - Data EDA and Analysis

# Table of Content
- [Tabular Data - Concepts in Machine Learning - Data EDA and Analysis](#tabular-data---concepts-in-machine-learning---data-eda-and-analysis)
- [Table of Content](#table-of-content)
- [1. Machine Learning Workflow](#1-machine-learning-workflow)
- [2. Decisions in analytics are increasingly driven by data and models, and key aspects of our Machine Learning Workflow are getting depend on cleaning data](#2-decisions-in-analytics-are-increasingly-driven-by-data-and-models-and-key-aspects-of-our-machine-learning-workflow-are-getting-depend-on-cleaning-data)
- [3. How data can be messy:](#3-how-data-can-be-messy)
- [4- Dealing with missing data:](#4--dealing-with-missing-data)
- [5- Dealing with outliers](#5--dealing-with-outliers)
- [6. Exploratory Data Analysis (EDA):](#6-exploratory-data-analysis-eda)
- [7- EDA techniques:](#7--eda-techniques)
- [8- Feature Engineering and Variable Transformation:](#8--feature-engineering-and-variable-transformation)
- [9- Transformations](#9--transformations)
- [25- Correlation vs Causation:](#25--correlation-vs-causation)
- [Credits:](#credits)

# 1. Machine Learning Workflow
|Step|Description|
|--|--|
|Problem Statement|What problem are we trying to solve.</br></br>“A problem well-stated is a problem half-solved" by Charles Kettering, the head of research at General Motors 
|Data Collection|What data do we need to solve that problem
|Data Exploration and Preprocessing|Expolre and analysis the collected data.</br></br>How should we clean our data so our model can use it
|Modeling|Build a model to solve our problem
|Validation|Did that model solve the problem
|Decision Making and Deployment|Putting the model into production

# 2. Decisions in analytics are increasingly driven by data and models, and key aspects of our Machine Learning Workflow are getting depend on cleaning data
|Aspect|Description|
|--|--|
|Ovservations| An instance of the data (usually a row of the dataset), if a row "an obsevation" is not clean, we are misrepresenting, to our model, the relationship between our features and our targets.
|Labels| They have to be labeled correctly.
|Algorithms| Which is the computer programs that estimate models based on avaliable data, we need to recognize that our algorithms are going to be learned assuming the data accurately represents a real world.
|Features| The information we have for each observation, if the recording of certain features are out, such as transaction amounts or locations with fraud, think about how easily that can throw off fraud detection.
|Model| The hypothesized relationship between observations and data, the model itself is going to be assuming that this is actual data representing real world.

# 3. How data can be messy:
__Duplicate or unnecessary data__
- It bring extra weight to observations to our model or bring unnecessary noise.
- Pay attention to duplicate values and research why there are multiple values, it's a good idea to look at the features you bringing in and filter the data as necessary; be carful not to filter too much if you may use features later.

__Inconsistent text and typos__
- data will often depend on correct spelling, you have to have no extra spaces, capitalized vs non-capitalized letters, this will all lead to the same feature, the same value for a feature being categorized as different value within the same feature set, even though they should be categorized as the same.

__Missing data__
- Missing data is something that should be delt with to some degree no matter what, but too much in the wrong fields can lead to an inability to use certain features which otherwise may have been powerful predictors.

__Outliers__
- When outliers occur they can skew a feature disproportionately and make it difficult to find the (true/best fit) underlying model.
  
__Data sourcing issues__
- Multiple systems
- Different database types
- Combining data from on-premises and on-the-cloud

# 4- Dealing with missing data:
Remove the missing data, it'll quickly clean our data without having to guess an appropriate replacement value, on the other hand we may end up losing too much information, or biasing our dataset to some reason that the data is not collected for a particular field.

We can impute our data, and that means that we would be replacing our null values with either the mean, or the median, or even a more complex estimation of the value, the pro to this is that we don't lose full rows or columns that may be important to our model, but on the other hand we add another level of uncertainty to our model as this is now based on estimates of what we think that true value for that missing value should have been, and reduce variability.

We can mask the data, so that all of our missing values are their own category, this would be under the assumption that missing values are actually indicative of useful infromation, also the cons here is we add another level of uncertainty to our model.

Check markdown note regarding missing data in 'tabularData/dataProcessing/handlingMissingData'.

# 5- Dealing with outliers
An outlier is an observation in data that is distinct from most other observations, typically these observations are aberrations, and do not accurately represent the phenomenon we are trying to explain through to our model.

Residuals: differences between actual and predicted values given your model, and they are going to represent model failure approaches that we can use in order to leverage residuals (detecting outliers):

- Standaradized Residual: which it's going to take our residual and divided by the standard error, the idea being here, if you have an outcome variables between 10 million and 100 million versus between 0 and 5, being off by 4 means much different thing given those different outcome ranges, so we want to standardized it according to those ranges.

- Deleted Residual: what we can do here is you remove that observation from the dataframe, and once you do that, you see what the new model will predict and see if there's a big difference between the original model and the model with deleted observation.

- Studentized Residual (Externally Studentized Residual): This is essentially just going to take our deleted residuals and standardize them.

Polices for outliers (what should we do):
- Remove them altogether; you don't need to worry about their effects, but you may have lost not only an important value, but the entire row related to that value.

- Assign; you can assign a different value to the outlier (mean, median, etc), again then you don't have to worry about the effects of this outlier on your model, but again you lose what may have been an important value, but here you won't lose the remainder of the row.

- Transform; we can transform the column that actually had the outlier something like the log transformation then that outlier given the new range, may no longer be an outlier.

- Predict; we can predict what that value would have been, we can do that:
  - By using similar observations.
  - By using regression and that can do a good job of predicting what that value would have been given the other features
  - Or we can just keep that value; the idea here that you will probably want to use a model that is resistant to outliers.

Check markdown note regarding missing data in 'tabularData/dataProcessing/handlingOutliers'.

# 6. Exploratory Data Analysis (EDA):
EDA is going to be the approach to analyzing datasets to summarize their main characteristics, often with visual methods and statistical summary as well.

EDA is useful as it's like the initial conversation with data before getting started, this will determine if the data that we are looking at actually makes sense, or if we need further cleaning, or if more data is actually needed.

EDA will help us identify patterns and trends in the actual dataset, sometimes this can be as important if not more important than the actual findings from the modeling.

# 7- EDA techniques:
__Summary statistics__
- Average, Mean, Median, Min, Max, Correlations, etc.

__Visualization__
- Histograms, Scatter Plots, Box Plots, etc.

__EDA tools__
- Pandas; data wrangling or summary statistics
- Matplotlib, Seaborn for visualization

# 8- Feature Engineering and Variable Transformation:
Before we move to modeling, we'll most likely need to adjust the raw data coming in, to optimize model performance.

Models used in Machine Learning Workflows will often be based off of some assumptions about the data, a common example is a linear regression models where it's going to assume a linear relationship between the observations and the target (outcome) variable.

The mathematical theory behind a linear regression is going to assume that our residuals from our model are going to be normally distributed Often the raw data that we get both the features and the target (outcome) variable can be negatively or positively skewed, and in real life that data can come in all shapes and sizes and data transformations can help the algorithm find a better solution that will end up having residuals that are actually normally distributed.

# 9- Transformations 
__Log transformation__
- Log transformation can be a useful way to find a linear relationship when the underlying raw data, which may not actually have a linear relationship. So the resulting algorithm will still be a linear regression, as the features now have been transformed, feature engineered, so that we can input those into the linear regression model.
- ```python
	y = a + b * log(x) # example a box office budget with diminishing returns.
  ```

__Polynomial features__
- We can estiamte higher-order relationships in this data by adding polynomial features, for example instead of only incorporating budget, we can incorporate budget squared as a feature and add more flexibility to our model and fit a linear model using these polynomial features, and again we will end up with a linear model even though we've included new features.

# 10- Variable Selection: 
Variable selection involves choosing the set of features to include in the model; variables must often transformed before they can be included in models, in addition to log and polynomial transformations, this can involve:

- __Encoding__
  - Converting non-numeric features to numeric features.
    - __Nominal__: Categorical variables take values in unordered categories (Red, Blue, Green; True, False).
    - __Ordinal__: Categorical variables take values in ordered categories (High, Medium, Low; Cold, Warm, Hot)
  
  - There are several common approaches to encode variables:
  	- __Binary Encoding__: Converts variables to either 0 or 1 and it's suitable for variables that take two possible values for example (True, False; Male, Female; Married, Not Married)
	- __One-hot Encoding__: Converts variables that take multiple values into binary (0, 1) variables, one for each category, this will create several new variables. (using one-hot will result to lose ordering)
	- __Ordinal Encoding__: Involves converting ordered categories to numerical values, for example (0, 1, 2, 3, ...), for this, we would have to take into account whether that ordering or the separation of categories is more important, as you are assigning a set distance between for example low and medium and high that may not actually exist.

- __Scaling__: 
  - Convert the scale of numeric data so they are on a comparable scale.
  - There are several approaches to scale features:

    - __Standard Scale__: Converts features to standard normal variables (by subtracting the mean and dividing by standard error), note this method slightly affected by outliers
    - __Min-Max Scale__: Converts variables to continuous variable in the (0, 1) interval by mapping maximum value to 1 and minimum value to 0, beware that this type of scaling is sensitive to outliers.
    - __Robust Scale__: It's similar to min-max scaling, but instead maps the interquartile range (75th percentile - 25th percentile) to (0, 1). This means the variable itself takes values outside of the (0, 1) interval.
  - The appropiate method of scaling or encoding depends on the type of feature.

# 11- Notes:
If you have a columns consists of all/mostly unique values eg: ID, that's not going to give us any predictive value for tying to run  a machine learning model, it can't learn anything if every single value for that column is a unique value.

We want to ensure that there's not too heavy of a multi-collinearity between each one of our features, as that can throw off our interpretation of something like linear regression (use pair plot to see that).

A side note: It's ok to have 'some' multi-collinearity when your doing multiple regressions.
- Check markdown note regarding missing data in 'tabularData/dataEda/correlation'.

# 12- Estimation vs Inference:
__Estimation__: Is the application of an algorithm, for example taking the average; keep in mind that estimate is just going to give us an estimate of a certian parameter, such as the mean.

__Inference__: Invovles putting an accuracy on the estimate, for example standard error of the average; when performing statistical inference, we are trying to understand the underlying distribution of the population including our estimate of the mean.

# 13- Machine Learning and Statistical Inference:
Machine Learning and Statistical Inference are similar, in both cases, we're using some sample data in order to infer qualities of the  actual underlying population distribution in the real world and the models that would have generated that data. When we say here our data-generating process, we can think of the linear model as an example of a data-generating process representing the actual joint distribution between our x and the y variable.

We may care about the whole distribution when doing machine learning, or just some features of our distribution, such as just getting the point estimate of for example our mean.

Machine Learning that focuses on understanding the underlying parameters and individual effects of all of our parameters require tools pulled from statistical inference. On the other hand, some machine learning models tend to only mildly focus on all these different parameters of the underlying parameters of our distribution, and just focus instead on prediction results, or just those estimates.

# 14- Parametric vs. Non-parametric;
A parametric model is a particular type of statistical model: it's also a set of distributions or regressions, but they have a finite number of parameters. 

So we can think here with ordinary least squares (OLS) with our linear models, where what we saw is that we had to predefine the number of coefficients according to the features or transformed features, that we were working with, and we had to assume also a linear distribution.

So that's going to be parametric and having the constraints that come along with it, so sometimes those will be a bit easier and quicker to solve, but on the other hand, they're going to be constrained compared to non-parametric models which won't have similar constraints

Examples of parametric models: 
- __Normal Distribution__: We see that there is a set equation for the normal distribution, and it's going to depend on a set number of parameters, namely the mean and the standard deviation, and that essentially going to be the parameters that will define what our normal distribution actually look like with the assumption that we were using the normal distribution.

- __Maximum Likelihood__: 
  - The most common way of estimating parameters in a parametric model is through Maximum Likelihood Estimation (MLE), the likelihood function is related to probability and is a function of the parameters of the model; for example, in the normal distribution those parameters were the mean and standard deviation.
  - The idea here is that our likelihood function is going to be a function of the parameters, to make this clear, think about the likelihood function as taking all of your data and saying, "What is the most likely value for the mean and standard deviation given the sample data that we see?". 
  - In general, what is the most likely parameters given our sample? And that's going to be your maximum likelihood estimation, then we choose the value of each of those parameters that's going to maximize that likelihood function, that's going to maximize what is most likely to occur given the data we have.

In non-parameteric statistics, we make fewer assumptions (our inference will not rely on as many assumptions); in particular, we don't assume that the data belong to any particular distribution (aka, distribution-free inference) This doesn't mean we don't know anything, we will be using insights from the data we have available.

Example non-parametric models: 
- Creating a distribution of the data (CDF; cumulative distribution function) using a histogram as the probability of where a certain value will fall according to the actual data, so we're not assuming a normal distribution or exponential distribution, but a distribution defined by the actual data that you've pulled from your sample.
- In this case, we wouldn't be specifying any of the parameters that we need for let's say a normal distribution.

# 15- Common Distributions:
__Uniform Distribution__
- Uniform because it is a uniformly equal chance that you'll get any value within our range, you can think here, the chances of rolling a dice where a 1 is equally likely to 6 versus 3 versus 4, every single value is equally likely.

__Gaussian/Normal Distribution__
- The idea that the guassian/normal distribution being that common, being that the most likely value is going to be those values that are closest to the mean and those that are further out on either side are going to be equally unlikely the further away we move form the mean.

- With differnet means, define where the distribution will be on the graph, as well as the different standard deviations defining how spread out or pointed that curve is, where lower standard deviations means a tighter distribution.

- One of the major claims to fame that makes the normal distribution so popular is the Central Limit Theorem (CLT); the idea behind the CLT is that if you take the average value from a bunch of samples, so you have a bunch of random samples and you take the average value of each one of those random samples, the distribution of those averages is going to a normal distribution if we have enough values.

- Also in the real world you see this in examples such as height, where most people are going to be close to the average height and it's very unlikely to be at the extremes of the average.

__Log Normal Distribution__
- The idea being that if you took the log of this variable, then you have the normal distribution, we can see that in dealing with skewed data take the log transformation about data and end up with a more normally distributed dataset. Now if we see, the tighter we are around the mean values in regards to the standard deviation, the closer it looks to the normal curve.
	  
- If you think about there being large outliers, then we'll have a larger tail, and we'll have a bigger standard deviation, because it's more spread out and therefore you'll be further away from normal.

- A common place that you'll see this distribution in the real world is most times when dealing with money, such as household income where most people are averaging around, lets say the left side of the distribution (eg, 60000 of a median income) and then you have large outliers out to the right (billionaires and so on)

__Exponential Distribution__
- Where most of the values closer to the left side and the idea is that it'll often be used to say what is going to be the amount of time before the next event.
- For example, the time between when you and someone else ends up watching a youtube video, so the time will be, let's say 1 minute and then assume someone else watches, then you restart and most people are around 1 minute whereas at some point there's this long spread out, some type of break that's less likely to happen where it takes 10~15 minutes before the next person watching this video.

__Poisson Distribution__
- A good way to think about this in the real-world is the number of events that happened during a certian amount of time, an example for it is how many people are going to watch a youtube video in the next 10 minutes? If the Lambda parameter is 1, then we'd say most of the time there's only 1 person that watches this video every 10 minutes, and it's tight around that 1, but if it's something like lambda = 10, then 10 people watch it every 10 minutes, and you'd probably have more of a spread of your standard deviation (covered under lambda) because it could be closer to 5 or 15 when you have a larger value of lambda.

# 16- Frequentist vs. Bayesian Statistics:
__Frequentist Statistics__
- Frequentist statistics is concerned with repeated observations to the limit, for a frequentist statistics, the idea is that we start without any idea for the probabilities we're trying to estimate.
- Let's start thinking about how it works in regards to queuing theory, queuing theory is an important concept to keep in mind for many businesses, and that idea is that it's the study of working with queues or lines and how many servers we need to match the size of that queue, so you can think about a grocery store and how many cashiers will need to check out customers in a timely fashion.
- So what we need in the frequentist approach is to estimate the probabilities of a certian number of customers coming over a fixed time period, and when we think about how many will come in over a fixed time period that we'll be working with a Poisson Distribution.
- Processes may have true frequencies in their real population eg, mean, but we're interested in modeling probabilities as many, many repeats of an experiment. So we assume no prior knowledge of the true frequencies, instead we rely on the fact that if our sample is large enough, if we've seen enough cues or lines, we can have a strong estimate of the probabilities of a certian number of people that will come in given a fixed time period and the parameters of our Poisson Distribution.
- And then we can infer an estimate of our probabilities given that sample, so we're going to want many repeats of our experiment together as much data as possible in our frequentist approach.

__Frequentist approach__
- 1- __Derive__: there is a fixed value for a given probability in the population of our sample, and we DERIVE the estimate directly from the data with no external influence, we give our level of confidence of our estimate on how likely our size sample actually covered the true population parameter. In other words, the more data we have, the more confident we can be that the data that we sampled actually covered the population parameter."Drive the probabilistic property of a procedure"

- 2- __Apply__:  Once we have that estimate, we can then apply that to that derived value to our observed data. "Apply the probability directly to the observed data"

__Bayesian Statistics__
- For Bayesian statistics, the parameters themselves can have a probability distribution, so rather than having a direct guess for the probability distribution and our uncertainty being around whather their sample covered that population parameter, we provide probability distributions to the parameters themselves. In other words, the more data we have, the tighter that probability distribution will be around the parameter estimate that we have.

- Bayesian also allows for experimenters to incorporate their prior beliefs of the distribution, for Frequentists, it's going to be solely based on the data available, for the probability of seeing X amount of people in line during a certain time period, we can have actually an educated guess to start off with, and Bayesian allows us to incorporate this into our prior distribution.

- This prior distribution is then updated after seeing the data, so we had our initial guess and after seeing more and more data, we can change what the distribution of our parameter estimate is. Then after updating, the distribution is now called the posterior distribution which has now incorporated the data to update our guess of what that estimate will be.

- We use much of the same math and the same formulas in both Frequentist and Bayesian Statistics, the main element that's going to differs is essentially the interpretation as: are we estimating how likely we are to cover the actual population mean? (Frequentist) Or we coming up with a distribution for that population mean (Bayesian).

To summerize: 
- If you have certain beliefs or knowledge about your area of research, a Bayesian approach might be better.
- Frequentist statiscs never uses or calculate the probability of the hypothesis, while Bayesian uses probabilities of data and probabilities of both hypothesis.

# 17- Recap:
Machine Learning may only focus on the estimation, whereas statistical inference will look to the underlying data generating process.

Parametric modeling will rely on assumptions of distributions and number of parameters of that distribution.

Non-parameteric models will not have as strong assumption as parametric.

# 18- Hypothesis Testing:
Hypothesis is a statement about a population parameter such as mean of our Poisson Distribution and our estimate of the number of people that will come into the line for our grocery store example in the next hour.

We create two hypotheses:
- The Null Hypothesis (H0)
- The Alternative Hypothesis (H1 or Ha)

And we decide which one to call the null depending on how the problem is set up.

Given the data from the sample we use, a hypothesis testing procedure gives us a rule to decide:
- For which values of the test statistic do we accept H0
- For which values of the test statistic do we reject H0 and accept H1

Now it's often said that you can reject the null H0 but never accept the alternative H1, here this doesn't matter very much, since we are using hypothesis testing in order to decide which of two paths to take in the project.

__Hypothesis Testing: Bayesian Approach__
- In the Bayesian interpretation, we won't get a decision boundary, rather we'll get posterior probabilities of the null and alternative hypotheses, and see which one is more likely.

- Example: Imagine you have two coins, Coin1 has 70% probability of coming up heads, and Coin2 has 50:50 chance of coming up heads, so we want to pick one without looking between these two, toss that coin 10 times and see how many times heads comes up. Then given the number of heads that come up, you will say which one is more likely between the two coins?

- As we know in the Bayesian interpretation, we need priors for each hypothesis, in this case we randomly chose the coin that we're going to flip, whether it was 0.5 or 0.7, so we're going to say that our prior estimate of each one of these values of the chances of choosing either 0.5 or 0.7 are each going to be half.

- Since we have no way before seeing the data to determine the coin that was actually chosen, we say it's a 50/50 chance Updating priors after seeing the data 3 heads with Bayes' Rule. We can write out the ratio: 
```
    P(H0.5 | Data) / P(H0.7 | Data)
```

- The priors are multiplied by the likelihood ratio, which does not depend on the priors. The likelihood ratio tells us how we should update the priors in reaction to seeing a given set of data and that will give us our posterior distribution.

# 19- Type1 and Type2 Errors:
Let's think of an example; we're going to imagine we're tossing a coin, and our null hypothesis H0 is that we are working with a fair coin, and the alternative hypothesis H1 is that it's not a fair coin.

__Type1 Error__ in this case is going to be incorectly rejecting the null H0, so this would mean we are indeed working with a fair coin, but we make the error given our sample data that we should decide to reject the null.

__Type2 Error__ on the other hand, is going to incorrectly accept the null H0, so this would mean we are working with a biased coin, but instead we accepted that we are working with a fair coin given our data (fail to reject that it is a fair coin given our data)

```
Power of a test = 1 - P(Type2 Error)	
			    = 1 - the probability of incorrectly accepting the null
```

# 20- Hypothesis Terminologies:
__The Likelihood Ratio__; is called a Test Statistic; we use it to decide wether to accept/reject the null hypothesis H0.

__The Rejection Region__; is the set of values of the test statistic that lead to rejecting null hypothesis H0.

__The Acceptance Region__; is the set of values of the test statistic that lead to accept the null hypothesis H0.

__The Null Distribution__; is the test statistic's distribution when the null hypothesis is true.

# 21- Business Examples:
__Testing marketing intervention effectiveness__
- For a new direct mail marketing compaign to existing customers, the null hypothesis (H0) would be that our campaign does not actually impact purchasing.
The alternative hypothesis (H1) would suggest that it does indeed have an impact.

__Website Layout__
- For a proposed change to a website layout, we may test the null hypothesis (H0) that the change had no impact on traffic.
- Or we would look for evidence to reject the null hypothesis in favor of an alternative hypothesis (H1), that there is indeed an impact of the website layout on traffic.

# 22- Significance Level and p-value:
We know the distribution of the null hypothesis, such as the odds the coin is fair or the distribution of marketing intervention effectiveness.

To get a rejection reason, we have to calculate the test statistic. We will choose before testing the data, the level at which we're going to actually reject our null hypothesis.

To make this clear, we have to choose the Significance level (alpha) beforehand, which is the probability threshold which the null hypothesis will be rejected. the significance level should tie closely with how important to you. It is to avoid Type1 or Type2 Error.

The idea of being a lower significance level, means that we would only reject the null if the probability of the data that we see is extremely low, assuming the null hypothesis.

We must choose (alpha) before computing the test statistic, if we don't we might be accused of p-hacking, which is changing the p-value for which we will accept or reject the null.

If you need to be absolutely certain that you can reject the null, (aka, avoid Type1 Error of incorrectly reject the null) you choose
- a very low (alpha),  # common values for p-value 0.01,0.05; for extreme safty maybe 0.001

Example
- If a medication has dangerous side effects, and the null is that it will not aid in recovery from a disease, while the alternative is that it will aid in the recovery from the desease, you want to be very cetain that you can reject the null (there is no effect).

- On the other hand, it may not be as strict for deciding wheter to increase the font size for ads, and seeing whether that would effect, where the null being no effect and alternative has effect; here a Type2 error a failure to reject the null (falsly accept the null) is not as dangerous as the medicaton one.

__p-value__: The smallest significance level at which the null hypothesis would be rejected The probability under the null distribution of result as or more extreme than what was actually observed.
- p-value measures the probability of getting a more extreme values than the one you got from the experiment.
- If the p-value is greater than alpha, you accept the null hypothesis.

__Confidence Interval__: the values for which we accept the null hypothesis, essentially the other side of the p-value.

# 23- F-Statistic:
The null hypothesis (H0) for the F-Statistic, which is just a test statistic for regression, is that the data can be modeled by setting all (weights) to zero. So that you can ask yourself: does adding the features actually give us an extra indicator of what the target will actually be compared to just taking the mean of that target variable?

You reject the null hypothesis, which means that you are not getting any better than the mean value if your p-value is small enough for your F-Statistic.

F-Statistic value is a number that relate to some probability, if that probability being very low, it means that the probability of coming up with the data given that the coefficients are not actually going to have any effect (so you reject the H0)

In other words, the probability of just using the mean and coming up with values that you did is going to be very low, so you reject the null hypothesis and assume that those coefficients actually do have an effect on the target variable.

# 24- Power and Sample size:
Probability of at least one Type1 Error is approximately:
```python
probability = 1 - (1 - 0.05)^num_tests	 # for 5% significance p-value = 0.05
```

__Bonferroni Correction__
- The Bonferroni Correction says choose p_threshold so that the probability of making a Type1 Error (assuming no effect) is 5%
- Typically choose p_threshold = 0.05/(#tests)
- Bonferroni Correction allows the probability of Type1 Error to be controlled but at the cost of power.
- Effects either need to be larger or the tests need larger samples to be detected.
- Best practice is to limit the number of comparisons done to a few well-motivated cases.

# 25- Correlation vs Causation:
__Does it rain more on cooler days?__

Maybe it depend on where you are, some places have summer monsoons, so maybe as it gets warmer there it rains more.
- Warmer wether increases evaporation, which can increase humidity, in warmer wether, there is water in the air to form precipitation. This mechanism would suggest warmer wether -> more rain
- Cooler wether decreases dew point (i.e. air can hold less water), this suggests if humid air enters the air and cools, it will turn into rain. This mechanism would suggest cooler wether -> more rain

The idea here that we want to think about the underlying mechanism when we are talking about cause and effect

__How correlations are important?__

If two variables X and Y are correlated, then X is useful for predicting Y, not necessarily going to tell you the cause and effects, but it may be good at predicting another value.

If we are trying to model Y, and we find things that correlate with Y, we may be able to improve our modeling, so it worth knowing that even if there's no casual factor, if the correlation is strong and we are not trying to directly manipulate our X 'features' as a casual factor, it can still prove useful to make predictions.

But note that; it just might be slightly more dangerous as this relationship, if we don't understand the underlying factors, it may not hold in the future. Also, we definitely want to make sure to weigh against ever using it as a feature that we can tweak in order to adjust the target variable

We should be careful about changing X with the hope of changing Y, X and Y can be correlated for different reasons:
- X causes Y (what we want, causation = correlation)
- Y causes X (mixing up cause-and-effect)
- X and Y are both caused by something else (confounding, external variable)
- X and Y are not related at all, we just got unlucky in the sample (spurious)

# Credits: 
- IBM Coursera Specialization