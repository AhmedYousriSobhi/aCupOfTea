# XGBOOST

## Abstract
XGBoost (eXtreme Gradient Boosting) is a popular machine learning algorithm that belongs to the gradient boosting framework. It is known for its efficiency, accuracy, and flexibility in handling a variety of data types and problem domains. XGBoost is widely used for both regression and classification tasks.

## Historical Defenitions
__Ensemble__: "Combining multiple models together"
- Referes to the process of combining multiple individual models, called base learners, to form a stronger and more accurate model.
- The idea behind the ensemble learning is that the collective knowledge of multiple models can often outperform a single model.
- Ensemble methods can be applied to various machine learning algorithms, such as decision trees, neural networks, or support vector machines.
- The models that form the ensemble, also known as base learners, could be either from the same learning algorithm or different learning algorithms. 
- Bagging and boosting are two widely used ensemble learners. Though these two techniques can be used with several statistical models, the most predominant usage has been with decision trees

__Bagging__: 'Ensemble but the models are in parallel'
- While decision trees are one of the most easily interpretable models, they exhibit highly variable behavior. Consider a single training dataset that we randomly split into two parts. Now, let’s use each part to train a decision tree in order to obtain two models.
- When we fit both these models, they would yield different results. Decision trees are said to be associated with high variance due to this behavior. 
- Bagging or boosting aggregation helps to reduce the variance in any learner. Several decision trees which are generated in parallel, form the base learners of bagging technique. Data sampled with replacement is fed to these learners for training. The final prediction is the averaged output from all the learners

![bagging image](https://lh3.googleusercontent.com/4svO7UdzXj-JxFwU-_SyrMWMqxp8Al3pVpQYr5A-nzCDXdEqVL_CHeqbeVVW8Kivsq76q5sozAKwGsQuy5qnk5wVYfqWb5LHxhknBm9DSLBjg0ViSRTVjZ3gFQPwiGxJ8wP2usOH)

__Boosting__: 'Ensemble but the models are sequentials'
- Boosting is a specific technique within ensemble learning that focuses on sequentially building an ensemble of models in an iterative manner. 
- The key idea of boosting is to train each model in the ensemble to correct the mistakes or misclassifications made by the previous models. 
- Boosting algorithms, such as AdaBoost and Gradient Boosting, iteratively build an ensemble of models, with each model giving more weight to the misclassified or difficult instances.
- In other words, each subsequent model in the boosting process is designed to improve upon the weaknesses of the previous models, thereby gradually reducing the overall error.
- Boosting algorithms can be used either for classification or regression.
  
![boosting image](https://i0.wp.com/neptune.ai/wp-content/uploads/2022/10/Ensemble-algorithms-boosting.png?ssl=1)

### Two well-known boosting algorithms
### 1- AdaBoost
AdaBoost stands for Adaptive Boosting. The logic implemented in the algorithm is: 
- First-round classifiers (learners) are all trained using weighted coefficients that are equal,
- In subsequent boosting rounds the adaptive process __increasingly weighs data points that were misclassified__ by the learners in previous rounds and decrease the weights for correctly classified ones. 

### 2- Gradient Boosting Framework
It is a boosting algorithm, so the base learners are connected sequentially. The word 'gradient' is based on the principle of __gradient descent optimization__, which means the model is fitted to the resuduals or errors of the previous models.

So: it is a special implementation of the boosting.

Gradient Boosting framework is a machine learning technique that combine multiple weak predictive models to create a strong predictive model. It is a type of ensemble learning where the models are trained sequentailly, each one correcting the mistakes made by the previous one.

The key idea behind gradient boosting is to iteratively fit the models to the residuals or errors of the previous models. In each iteration, a new model is trained to minimize the loss function by reducing the errors of the ensemble. This process is typically done using gradient descent optimization, where the model is updated in the direction of the steepest descent of the loss function.

Summary: Gradient Boosting uses differentiable function losses from the weak learners to generalize. At each boosting stage, the learners are used to minimize the loss function given the current model.

## XGboost Methadology
The key idea behind XGBoost is to build an ensemble of weak predictive models, typically decision trees, and iteratively improve their performance. It trains these models in a sequential manner, where each new model is trained to correct the mistakes made by the previous models. This iterative process allows XGBoost to learn complex patterns and make accurate predictions.

## XGboost Architecture
XGBoost stands for Extreme Gradient Boosting. It’s a parallelized and carefully optimized version of the gradient boosting algorithm. __Parallelizing the whole boosting process__ hugely improves the training time. 

Instead of training the best possible model on the data (like in traditional methods), we train thousands of models on various subsets of the training dataset and then vote for the best-performing model.

For many cases, XGBoost is better than usual gradient boosting algorithms. The Python implementation gives access to a vast number of inner parameters to tweak for better precision and accuracy.

## XGboost Advantages
Some key features and advantages of XGBoost include:

- Regularization: XGBoost incorporates regularization techniques to prevent overfitting and improve generalization. It includes regularization terms in the objective function that control model complexity.
- Gradient-based optimization: XGBoost uses gradient descent optimization to minimize the loss function, allowing it to efficiently handle large datasets.
- Handling missing values: XGBoost has built-in capabilities to handle missing values in the data, reducing the need for preprocessing or imputation techniques.
- Feature importance: XGBoost provides a measure of feature importance, allowing users to understand which features have the most impact on the model's predictions.
- Parallel processing: XGBoost can utilize parallel processing capabilities, making it faster than traditional gradient boosting implementations.
- Flexibility: XGBoost supports a wide range of objective functions and evaluation metrics, allowing users to customize the model for different problem types.
- Parallelization: The model is implemented to train with multiple CPU cores.
- Non-linearity: XGBoost can detect and learn from non-linear data patterns.
- Cross-validation: Built-in and comes out-of-the-box.
- Scalability: XGBoost can run distributed thanks to distributed servers and clusters like Hadoop and Spark, so you can process enormous amounts of data. It’s also available for many programming languages like C++, JAVA, Python, and Julia. 

### Resources:
- [simplilearn](https://www.simplilearn.com/what-is-xgboost-algorithm-in-machine-learning-article)
- [analyticsvidhya](https://www.analyticsvidhya.com/blog/2018/09/an-end-to-end-guide-to-understand-the-math-behind-xgboost/#h-why-ensemble-learning)
- [neptune](https://neptune.ai/blog/xgboost-everything-you-need-to-know)