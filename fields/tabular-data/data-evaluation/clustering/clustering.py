

import pandas as pd, numpy as np

# Used for visulization
import matplotlib.pyplot as plt, seaborn as sns

sns.set()
sns.set_style("whitegrid")

from sklearn.pipeline import Pipeline

def plot_PCA_pairs(cluster_model, df):
    # Transform your training data using PCA
    X_pca = cluster_model.named_steps['processing'].transform(df)

    # Add cluster labels to the transformed data
    X_pca_with_clusters = pd.DataFrame(X_pca.copy())
    clusters_label = cluster_model.named_steps['cluster'].labels_

    X_pca_with_clusters['Cluster'] = clusters_label

    # Create a pairplot of PCA components with cluster assignments as hue
    sns.pairplot(data=X_pca_with_clusters, hue='Cluster', palette='Set1')
    plt.suptitle('Pairplot of PCA Components with Cluster Assignments')
    plt.tight_layout()
    plt.savefig('../report/plots/Pairplot of PCA Components with Cluster Assignments.jpg')
    plt.show()

    