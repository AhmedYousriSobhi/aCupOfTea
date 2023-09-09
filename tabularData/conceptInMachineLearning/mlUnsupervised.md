# Machine Learning Concept - Unsupervisied Learning

# Table of Content
- [Machine Learning Concept - Unsupervisied Learning](#machine-learning-concept---unsupervisied-learning)
- [Table of Content](#table-of-content)
- [There can be two cases of unsupervised learning:](#there-can-be-two-cases-of-unsupervised-learning)
- [The Curse of dimensionality:](#the-curse-of-dimensionality)
- [K-means](#k-means)
- [Choosing the right Clustering ALgorithm](#choosing-the-right-clustering-algorithm)
- [Clustering Algorithms Comparison](#clustering-algorithms-comparison)
- [Determining The Number of Clusters](#determining-the-number-of-clusters)
- [Credits](#credits)
  
# There can be two cases of unsupervised learning:
One popularly use case is called __clustering__, where we use our unlabeled data to identify an unknown structure and an example of this may be segmenting our customers into different groups.

The other major use case for unsupervised algorithms is for __dimensionality reduction__. Namely using structural characteristics to reduce the size of our dataset without losing much information contained in that original dataset.

# The Curse of dimensionality:
The dimensionality refers to the number of features in our dataset, and theortically the more features we have the better the model should perform, since models will have more features to learn from, however in real life there are several reasons why too many features may end up leading to worse performance in practice.

If we have several features, things can go wrong; 
- Maybe some of those features are spurios correlations (meaning they correlate within your dataset, but with new data outside form our training dataset)

- Too many features may create more noise and signal.

- Algorithms find it harder to sort through non-meaningful features.

- The number of training examples required will increase exponentially with the dimensionality

- On top of that, higher dimensions will often lead to slower performance as dealing with more columns is going to be more computationally expensive.

- Also it will lead to the incidence of outliers increasing as the dimensionality increases

# K-means
The process is to take k centroids, find the nearest points, then take the average of each one of those points that are closer to that centroid than any other centroid, and set that average that we have as the new centroid and view the closest points to that new centroid.

This movement towards that average as we keep reinitiating that centroid after every iteration, is going to stop once that centroid no longer moves and this can happen at different points depending on where we initiate our centroids. 

# Choosing the right Clustering ALgorithm
Choosing the right clustering algorithm depends on the nature of your data, your objectives, and the characteristics you want in your clusters. Here are some considerations to help you choose a clustering algorithm:

|Factor|Description|
|--|--|
Data Characteristics|Data Distribution: Consider the distribution of your data. K-Means and Gaussian Mixture Models (GMM) assume that clusters have a spherical shape and follow a Gaussian distribution. If your data doesn't meet these assumptions, other algorithms like DBSCAN or hierarchical clustering might be more suitable.</br>Density: DBSCAN and related algorithms are effective when dealing with clusters of varying shapes and densities.
Number of Clusters|K-Means: If you have a good estimate of the number of clusters (K), K-Means can work well. You can use techniques like the Elbow Method or Silhouette Score to help determine the optimal K.</br>Hierarchical Clustering: If you want to explore clusters at different granularities, hierarchical clustering can be useful as it produces a hierarchy of clusters.
Scalability|Consider the size of your dataset. K-Means and GMM can handle large datasets efficiently. DBSCAN, on the other hand, can be slow for very large datasets due to its density-based nature.
Interpretability|Think about how interpretable you want the clusters to be. K-Means and GMM often provide clusters that are easy to understand, while hierarchical clustering produces a hierarchy that may require more interpretation.
|Outliers|If you expect outliers in your data and want to exclude them from clusters, consider algorithms like DBSCAN, which can identify noise points.
|Robustness to Noise|DBSCAN and other density-based algorithms are robust to noise and can handle datasets with outliers effectively.
|Non-Euclidean Distances|Some algorithms like K-Means and GMM assume Euclidean distances between data points. If your data requires a different distance metric (e.g., cosine similarity for text data), consider algorithms that support custom distance metrics.
|Cluster Shape|Consider whether your clusters are expected to have arbitrary shapes. Algorithms like DBSCAN, Mean-Shift, or Spectral Clustering can handle non-convex clusters.
|Hierarchical vs. Partitional|Decide if you prefer hierarchical clustering (which produces a tree of clusters) or partitional clustering (which assigns each data point to a single cluster).
|Domain Knowledge|Your domain expertise and understanding of the problem can also influence the choice of clustering algorithm. Sometimes, a specific algorithm may be known to work well in your domain.
Experimentation|It's often a good practice to experiment with multiple clustering algorithms and compare their results in terms of cluster quality and interpretability.
Evaluation Metrics|Consider the evaluation metrics you plan to use to assess the quality of clusters. Different algorithms may perform differently in terms of metrics like silhouette score, Davies-Bouldin index, or within-cluster sum of squares (for K-Means).
Software and Library Support|Ensure that the algorithm you choose is available in your preferred programming language and has good library support (e.g., scikit-learn, scipy).

In practice, it's common to try several clustering algorithms and evaluate their performance based on your specific objectives and data characteristics. No single algorithm is best for all scenarios, so it's essential to choose the one that best suits your needs and produces meaningful clusters for your analysis or applications.

# Clustering Algorithms Comparison
Algorithm|	Data Distribution|	Number of Clusters|	Scalability|	Interpretability|	Outlier Handling|	Robustness to Noise|	Cluster Shape|	Non-Euclidean Distances|	Hierarchical vs. Partitional|	Domain Knowledge|	Evaluation Metrics|	Software Support|
|--|--|--|--|--|--|--|--|--|--|--|--|--|
|K-Means|	Assumes spherical|	Requires pre-defined K|	Scalable|	Easy to interpret|	Sensitive to outliers|	Not robust|	Assumes convex|	Supports custom distances|	Partitional|	Widely used| Silhouette Score, Within-cluster SSE|	scikit-learn, R|
|Gaussian Mixture Models|	Assumes Gaussian|	Requires pre-defined K|	Scalable|	Easy to interpret|	Sensitive to outliers|	Not robust|	Assumes convex|	Supports custom distances|	Partitional|	Gaussian data|	Silhouette Score, BIC|	scikit-learn, R
|DBSCAN|	Does not assume specific shape|	Adapts to density|	Limited| scalability for large datasets|	Less interpretable|	Identifies noise points|	Robust to noise|	Handles non-convex|	Customizable distance metric|	Partitional|	Effective for noisy data| Silhouette Score|	scikit-learn, R|
|Mean-Shift|	Does not assume specific shape|	Adapts to density|	Moderate scalability|	Moderate interpretability|	Identifies modes|	Robust to noise|	Handles non-convex|	Supports custom distances|	Partitional|	Mode-seeking| Silhouette Score|	scikit-learn, R|
|Agglomerative Hierarchical|	Does not assume specific shape|	Hierarchical hierarchy|	Moderate scalability|	Hierarchical structure|	No explicit outlier handling|	Moderate robustness|	Handles non-convex|	Supports custom distances|	Hierarchical|	Hierarchical clustering| Silhouette Score, Cophenetic Correlation|	scikit-learn, scipy|
|Spectral Clustering|	Does not assume specific shape|	Requires pre-defined K|	Limited scalability for large datasets|	Moderate interpretability|	No explicit outlier handling|	Robust to noise|	Handles non-convex|	Supports custom distances|	Partitional|	Spectral techniques|	Silhouette Score|	scikit-learn|

# Determining The Number of Clusters
Choosing the appropriate number of clusters (K) is a crucial step in clustering analysis. Several methods can help you determine the optimal K:
|Method|Details|
|--|--|
|Elbow Method|Plot the within-cluster sum of squares (inertia) against different values of K.</br>Look for an "elbow" point in the plot where the inertia starts to level off. This can be a good choice for K.
|Silhouette Score|Calculate the silhouette score for different values of K.The silhouette score measures the quality of clustering, and higher values indicate better separation between clusters.Choose the K that maximizes the silhouette score.</br>You can use the silhouette_score function from scikit-learn.
|Gap Statistics|Gap statistics compare the performance of your clustering to a reference (e.g., random data) and can help identify the optimal K.</br>The larger the gap statistic, the better the clustering.</br>You can use libraries like scikit-learn or external packages for gap statistics.
|Domain Knowledge|In some cases, domain knowledge or business requirements may guide your choice of K.
|Visual Inspection|Visualize the results of different K values and choose the one that makes the most sense based on the distribution of data points.

After determining the optimal number of clusters (K), you can proceed with clustering your data using the chosen algorithm and K value within your pipeline.

Note: python code provided for Elbow Method locatted at "tabularData/dataModeling/cluster_elbow_method.py"

Example of Elbow Method:
![Elbow Method for Optimal K](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/f8ed701c-f5ff-4181-ab6c-3e873ed7bd01)

# Credits
- IBM Coursera Specialization