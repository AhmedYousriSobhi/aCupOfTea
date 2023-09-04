# Accuracy Paradox

## Table of Content
- [Accuracy Paradox](#accuracy-paradox)
  - [Table of Content](#table-of-content)
  - [Accuracy Fails for Imbalanced Classification](#accuracy-fails-for-imbalanced-classification)
  - [Accuracy Paradox](#accuracy-paradox-1)
  - [Credits](#credits)

In a Classification machine learning problem, one of the common most-used evaluation metric is __Accuracy__.

```
Accuracy = Number of correct predictions / Total number of predictions
```

The reason for its wide use is because it is easy to calculate, easy to interpret, and is a single number to summarize the model’s capability.

## Accuracy Fails for Imbalanced Classification

As such, it is natural to use it on imbalanced classification problems, where the distribution of examples in the training dataset across the classes is not equal.

This is the most common mistake made by beginners to imbalanced classification.

When the class distribution is slightly skewed, accuracy can still be a useful metric. When the skew in the class distributions are severe, accuracy can become an unreliable measure of model performance.

The reason for this unreliability is centered around the average machine learning practitioner and the intuitions for classification accuracy.

Typically, classification predictive modeling is practiced with small datasets where the class distribution is equal or very close to equal. Therefore, most practitioners develop an intuition that large accuracy score (or conversely small error rate scores) are good, and values above 90 percent are great.

Achieving 90 percent classification accuracy, or even 99 percent classification accuracy, may be trivial on an imbalanced classification problem.

This means that intuitions for classification accuracy developed on balanced class distributions will be applied and will be wrong, misleading the practitioner into thinking that a model has good or even excellent performance when it, in fact, does not.

## Accuracy Paradox
Consider the case of an imbalanced dataset with a 1:100 class imbalance.

In this problem, each example of the minority class (class 1) will have a corresponding 100 examples for the majority class (class 0).

In problems of this type, the majority class represents “normal” and the minority class represents “abnormal,” such as a fault, a diagnosis, or a fraud. Good performance on the minority class will be preferred over good performance on both classes.

"""
Considering a user preference bias towards the minority (positive) class examples, accuracy is not suitable because the impact of the least represented, but more important examples, is reduced when compared to that of the majority class."""
- A Survey of Predictive Modelling under Imbalanced Distributions, 2015.

On this problem, a model that predicts the majority class (class 0) for all examples in the test set will have a classification accuracy of 99 percent, mirroring the distribution of major and minor examples expected in the test set on average.

Many machine learning models are designed around the assumption of balanced class distribution, and often learn simple rules (explicit or otherwise) like always predict the majority class, causing them to achieve an accuracy of 99 percent, although in practice performing no better than an unskilled majority class classifier.

A beginner will see the performance of a sophisticated model achieving 99 percent on an imbalanced dataset of this type and believe their work is done, when in fact, they have been misled.

This situation is so common that it has a name, referred to as the “__accuracy paradox__”.

"""in the framework of imbalanced data-sets, accuracy is no longer a proper measure, since it does not distinguish between the numbers of correctly classified examples of different classes. Hence, it may lead to erroneous conclusions """
- A Review on Ensembles for the Class Imbalance Problem: Bagging-, Boosting-, and Hybrid-Based Approaches, 2011.

Strictly speaking, accuracy does report a correct result; it is only the practitioner’s intuition of high accuracy scores that is the point of failure. Instead of correcting faulty intuitions, it is common to use alternative metrics to summarize model performance for imbalanced classification problems.

## Credits
- [Machine Learning Mastery](https://machinelearningmastery.com/failure-of-accuracy-for-imbalanced-class-distributions/).