# Machine Learning Concept: Unsupervisied Learning

## 1- There can be two cases of unsupervised learning:
One popularly use case is called __clustering__, where we use our unlabeled data to identify an unknown structure and an example of this may be segmenting our customers into different groups.

The other major use case for unsupervised algorithms is for __dimensionality reduction__. Namely using structural characteristics to reduce the size of our dataset without losing much information contained in that original dataset.

## 2- The Curse of dimensionality:
The dimensionality refers to the number of features in our dataset, and theortically the more features we have the better the model should perform, since models will have more features to learn from, however in real life there are several reasons why too many features may end up leading to worse performance in practice.

If we have several features, things can go wrong; 
- Maybe some of those features are spurios correlations (meaning they correlate within your dataset, but with new data outside form our training dataset)

- Too many features may create more noise and signal.

- Algorithms find it harder to sort through non-meaningful features.

- The number of training examples required will increase exponentially with the dimensionality

- On top of that, higher dimensions will often lead to slower performance as dealing with more columns is going to be more computationally expensive.

- Also it will lead to the incidence of outliers increasing as the dimensionality increases

## 3- K-mean:
The process is to take k centroids, find the nearest points, then take the average of each one of those points that are closer to that centroid than any other centroid, and set that average that we have as the new centroid and view the closest points to that new centroid.

This movement towards that average as we keep reinitiating that centroid after every iteration, is going to stop once that centroid no longer moves and this can happen at different points depending on where we initiate our centroids. 

## Credits
- IBM Coursera Specialization