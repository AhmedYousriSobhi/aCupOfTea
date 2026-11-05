# Libraries, Frameworks & Containers - Overview

> The everyday toolbox of an ML engineer: environments, containers, GPU tools, data libraries and PyTorch. Short "101" pages you can read in a coffee break.

"It works on my machine" is the oldest problem in the book. Half of this folder (conda, Docker, Singularity) is about making your code run the same everywhere. The other half (CUDA, `nvidia-smi`, Pandas, Dask, PyTorch) is about doing the actual work.

## Contents

| File | Description |
|------|-------------|
| [101-conda](/fields/libraries-frameworks-containers/101-conda.md) | Conda environment management |
| [101-containers](/fields/libraries-frameworks-containers/101-containers.md) | Containerization basics |
| [101-cuda](/fields/libraries-frameworks-containers/101-cuda.md) | NVIDIA CUDA programming |
| [101-dask](/fields/libraries-frameworks-containers/101-dask.md) | Dask for parallel computing |
| [101-docker](/fields/libraries-frameworks-containers/101-docker.md) | Docker containerization |
| [101-nvidia-smi](/fields/libraries-frameworks-containers/101-nvidia-smi.md) | NVIDIA GPU monitoring |
| [101-pandas](/fields/libraries-frameworks-containers/101-pandas.md) | Pandas data manipulation |
| [101-pytorch](/fields/libraries-frameworks-containers/101-pytorch.md) | PyTorch deep learning framework |
| [101-singularity](/fields/libraries-frameworks-containers/101-singularity.md) | Singularity containers for HPC |
| [102-pytorch-ddp](/fields/libraries-frameworks-containers/102-pytorch-ddp.md) | PyTorch Distributed Data Parallel |

Covers the essential stack for ML engineering and deployment.

## The route

| If you need to... | Read |
|-------------------|------|
| Keep Python environments tidy | [101-conda](/fields/libraries-frameworks-containers/101-conda.md) |
| Package your code so it runs anywhere | [101-containers](/fields/libraries-frameworks-containers/101-containers.md), [101-docker](/fields/libraries-frameworks-containers/101-docker.md), [101-singularity](/fields/libraries-frameworks-containers/101-singularity.md) (for HPC) |
| Understand and watch the GPU | [101-cuda](/fields/libraries-frameworks-containers/101-cuda.md), [101-nvidia-smi](/fields/libraries-frameworks-containers/101-nvidia-smi.md) |
| Work with data | [101-pandas](/fields/libraries-frameworks-containers/101-pandas.md), [101-dask](/fields/libraries-frameworks-containers/101-dask.md) |
| Train with PyTorch, then on many GPUs | [101-pytorch](/fields/libraries-frameworks-containers/101-pytorch.md), [102-pytorch-ddp](/fields/libraries-frameworks-containers/102-pytorch-ddp.md) |
