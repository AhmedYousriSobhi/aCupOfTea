# 101 - Pytorch
This blog is mainly designed to get a start with Pytorch, and where to start, so it does not have a complete guide, but the approach I used so far to study Pytorch, also adding some notes and information to document.

# Table of Content
- [101 - Pytorch](#101---pytorch)
- [Table of Content](#table-of-content)
- [How to Start?](#how-to-start)
- [Precision in DataType](#precision-in-datatype)
- [GPU Properties](#gpu-properties)
  - [Break Down the Output](#break-down-the-output)
    - [Architectures Mentioned](#architectures-mentioned)
- [Model Saving/Loading](#model-savingloading)
  - [to Save the Model](#to-save-the-model)
  - [to Load the Model](#to-load-the-model)
- [References](#references)

# How to Start?
If you are like me love to learn from books and articles rather than watching records and videos, so one of the most recommended start in Pytorch by following up with [learnpytorch - Zero to Mastery Learn PyTorch for Deep Learning](https://github.com/mrdbourke/pytorch-deep-learning/tree/main);
- They provide a free course tutorial, explained with a great effort with many interesting notes.
- You can follow up with them on colab on their notebook to follow along with them.

There is a cheat sheet provided by the official docs, you can find [here](https://pytorch.org/tutorials/beginner/ptcheat.html)

# Precision in DataType
[Wiki](https://en.wikipedia.org/wiki/Precision_(computer_science)) for precision in Data Science.
```
Different datatypes can be confusing to begin with. But think of it like this, the lower the number (e.g. 32, 16, 8), the less precise a computer stores the value. And with a lower amount of storage, this generally results in faster computation and a smaller overall model. Mobile-based neural networks often operate with 8-bit integers, smaller and faster to run but less accurate than their float32 counterparts
```
- Reference: [learnpytorch - 00_pytorch_foundation](https://github.com/mrdbourke/pytorch-deep-learning/tree/main)

# GPU Properties
It is important to know the information about current GPUs available on the system you are using. We can check it using the pre-defined methods in pytorch:
```python
import torch

print('Is there a GPU?                                  ',torch.cuda.is_available())
print('How many GPUs do we have                         ',torch.cuda.device_count())
print('GPU properties                                   ',torch.cuda.get_device_properties(torch.cuda.current_device()))
print('Supported GPU micro-architectures                ',torch.cuda.get_arch_list())
print('Which GPU micro-architecture is this?            ',torch.cuda.get_device_capability())
print('Number of threads available on host              ',torch.get_num_threads())
```
The output of running on Colab was:

```python
Is there a GPU?                                   True
How many GPUs do we have                          1
GPU properties                                    _CudaDeviceProperties(name='Tesla T4', major=7, minor=5, total_memory=15102MB, multi_processor_count=40)
Supported GPU micro-architectures                 ['sm_50', 'sm_60', 'sm_70', 'sm_75', 'sm_80', 'sm_86', 'sm_90']
Which GPU micro-architecture is this?             (7, 5)
Number of threads available on host               1
```
## Break Down the Output
|Part|Description|
|-|-|
Is there a GPU?|torch.cuda.is_available() returns True, indicating that a GPU is available for use in your system.
How many GPUs do we have?|torch.cuda.device_count() returns 1, indicating that there is one GPU in the system.
GPU properties|torch.cuda.get_device_properties(torch.cuda.current_device()) provides information about the GPU. In this case:</br> - Name: 'Tesla T4'</br> - Major version: 7</br> - Minor version: 5</br> - Total memory: 15102MB</br> - Multi-processor count: 40
Supported GPU micro-architectures|torch.cuda.get_arch_list() returns a list of supported GPU micro-architectures. In this case, the list includes architectures like 'sm_50', 'sm_60', 'sm_70', 'sm_75', 'sm_80', 'sm_86', 'sm_90'.
Which GPU micro-architecture is this?|torch.cuda.get_device_capability() returns the micro-architecture of the current GPU. In this case, it is (7, 5), indicating a major version of 7 and a minor version of 5.
Number of threads available on host:|torch.get_num_threads() returns the number of threads available on the host. In this case, it is 1.

### Architectures Mentioned
|Architecture|Name|Example
|-|-|-|
sm_50| Maxwell (Compute Capability 5.0)| GPUs GeForce GTX 970/980, Tesla M40/M60
sm_60| Pascal (Compute Capability 6.0)| GPUs GeForce GTX 1080/1080 Ti, Tesla P100
sm_70| Volta (Compute Capability 7.0)| GPUs Titan V, Tesla V100
sm_75| Turing (Compute Capability 7.5)| GPUs GeForce RTX 20 series (e.g., RTX 2080), Tesla T4
sm_80| Ampere (Compute Capability 8.0)| GPUs GeForce RTX 30 series (e.g., RTX 3080), A100 Tensor Core GPU


# Model Saving/Loading
## to Save the Model
It is better to save trained parameters instead of saving the whole model.
```python
from pathlib import Path

# 1. Create models directory
MODEL_PATH = Path("models")
MODEL_PATH.mkdir(parents=True, exist_ok=True)

# 2. Create model save path
MODEL_NAME = "01_pytorch_workflow_model_1.pth"
MODEL_SAVE_PATH = MODEL_PATH / MODEL_NAME

# 3. Save the model state dict
print(f"Saving model to: {MODEL_SAVE_PATH}")
torch.save(obj=model_1.state_dict(), # only saving the state_dict() only saves the models learned parameters
           f=MODEL_SAVE_PATH)
```
## to Load the Model
```python
# Instantiate a fresh instance of LinearRegressionModelV2
loaded_model_1 = LinearRegressionModelV2()

# Load model state dict
loaded_model_1.load_state_dict(torch.load(MODEL_SAVE_PATH))

# Put model to target device (if your data is on GPU, model will have to be on GPU to make predictions)
loaded_model_1.to(device)

print(f"Loaded model:\n{loaded_model_1}")
print(f"Model on device:\n{next(loaded_model_1.parameters()).device}")
```
# References
- Pytorch official Documentation Tutorials: [link](https://pytorch.org/tutorials/)
    - It provides **open in colab** for more hands-on tutorial
- Pytorch official Docs BLITZ: [link](https://pytorch.org/tutorials/beginner/deep_learning_60min_blitz.html)
    - It provides **open in colab** for more hands-on tutorial
- [RECOMMENDED] learnpytorch - 
Zero to Mastery Learn PyTorch for Deep Learning : [link](https://www.learnpytorch.io/), [Github](https://github.com/mrdbourke/pytorch-deep-learning/tree/main)
    - It provides **open in colab** for more hands-on tutorial
- [RECOMMENDED] Javapoint - pytorch tutorial: [link](https://www.javatpoint.com/pytorch)
- Python Pytorch Guide: [link](https://pythonguides.com/pytorch/)
- Pytorch-ignite: [link](https://pytorch-ignite.ai/tutorials/)
  - Contains beginner, intermediate, and advanced topics, like [distribute training](https://pytorch-ignite.ai/tutorials/intermediate/01-cifar10-distributed/)
