# Used to determine the number of clusters

from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from yellowbrick.cluster import KElbowVisualizer

def elbow_method(df_pca):
    inertias = []
    K_range = range(1, 10)  # Try different values of K
    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(df_pca)  # X_pca is your PCA-transformed data
        inertias.append(kmeans.inertia_)

    plt.plot(K_range, inertias, marker='o')
    plt.xlabel('Number of Clusters (K)')
    plt.ylabel('Inertia')
    plt.title('Elbow Method for Optimal K')
    plt.show()

def elbow_method_yellowbrick(df_pca):
    Elbow_M = KElbowVisualizer(KMeans(), k=10)
    Elbow_M.fit(df_pca)
    Elbow_M.show()