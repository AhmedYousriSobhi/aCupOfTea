# pca-ncomponent.py

<div class="code-file">

Code file from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/tabular-data/data-feature-engineering/pca-ncomponent.py)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/tabular-data/data-feature-engineering/pca-ncomponent.py)

</div>

```python
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

pca = PCA()
pca.fit(X)  # Fit PCA to your data
explained_variance = pca.explained_variance_ratio_

plt.plot(range(1, len(explained_variance) + 1), explained_variance.cumsum(), marker='o', linestyle='--')
plt.xlabel('Number of Components')
plt.ylabel('Cumulative Explained Variance')
plt.show()
```
