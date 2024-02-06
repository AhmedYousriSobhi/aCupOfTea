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
- [Pytorch Training Loop Steps](#pytorch-training-loop-steps)
- [Pytorch Output Prediction](#pytorch-output-prediction)
  - [In Classification problem:](#in-classification-problem)
  - [to Load the Model](#to-load-the-model)
- [Print Model Summary](#print-model-summary)
- [Download Script to your code](#download-script-to-your-code)
- [Training on CPU is faster?](#training-on-cpu-is-faster)
- [Common Deep Learning Issues](#common-deep-learning-issues)
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

# Pytorch Training Loop Steps

PyTorch training loop steps

1. **Forward pass** - The model goes through all of the training data once, performing its forward() function calculations (model(x_train)).
2. **Calculate the loss** - The model's outputs (predictions) are compared to the ground truth and evaluated to see how wrong they are (loss = loss_fn(y_pred, y_train).
3. **Zero gradients** - The optimizers gradients are set to zero (they are accumulated by default) so they can be recalculated for the specific training step (optimizer.zero_grad()).
4. **Perform backpropagation on the loss** - Computes the gradient of the loss with respect for every model parameter to be updated (each parameter with requires_grad=True). This is known as backpropagation, hence "backwards" (loss.backward()).
5. **Step the optimizer (gradient descent)** - Update the parameters with requires_grad=True with respect to the loss gradients in order to improve them (optimizer.step()).

# Pytorch Output Prediction
The output of a neural network is called **logits**, which is the raw output without any modification/passing through the activation functions.

Example of binary class classification [0, 1]:
- Logit output prediction: The raw output (unmodified)
    ```
    tensor([[-0.4279],
            [-0.3417],
            [-0.5975],
            [-0.3801],
            [-0.5078]], device='cuda:0', grad_fn=<SliceBackward0>)
  ```
- Prediction probability (using Softmax): The output now have some kind of consistency (even though they're still random)
  ```
  tensor([[0.3946],
        [0.4154],
        [0.3549],
        [0.4061],
        [0.3757]], device='cuda:0', grad_fn=<SigmoidBackward0>)
  ```
- Predictions Labels
  ```
  tensor([0., 0., 0., 0., 0.], device='cuda:0', grad_fn=<SqueezeBackward0>)
  ```
  
These logits needs to be converted to a prediction probabilities using on of the activation functions, then converted to predictions labels;

```
Logits ----> Prediction Probabilities ----> Predictions Labels

In Classification problem:
--------------------------
- Binary Classification:

                                  torch.sigmoid()                         torch.round()
        Raw Output Predictions   ------>    Prediction Probability  ----->  Prediction Labels
              "Logits"

- Multi-Class Classification:

                                  torch.softmax()                           torch.argmax()
        Raw Output Predictions   ------>    Prediction Probability  ----->  Prediction Labels
              "Logits"

```

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
# Print Model Summary
Using torchinfo package that has a method to visualize a summary for the model.
```bash
# Install torchinfo if it's not available, import it if it is
try:
    import torchinfo
except:
    !pip install torchinfo
    import torchinfo

from torchinfo import summary
summary(model_0, input_size=[1, 3, 64, 64]) # do a test pass through of an example input size
```

The expected output would be;
```bash
==========================================================================================
Layer (type:depth-idx)                   Output Shape              Param #
==========================================================================================
TinyVGG                                  [1, 3]                    --
├─Sequential: 1-1                        [1, 10, 32, 32]           --
│    └─Conv2d: 2-1                       [1, 10, 64, 64]           280
│    └─ReLU: 2-2                         [1, 10, 64, 64]           --
│    └─Conv2d: 2-3                       [1, 10, 64, 64]           910
│    └─ReLU: 2-4                         [1, 10, 64, 64]           --
│    └─MaxPool2d: 2-5                    [1, 10, 32, 32]           --
├─Sequential: 1-2                        [1, 10, 16, 16]           --
│    └─Conv2d: 2-6                       [1, 10, 32, 32]           910
│    └─ReLU: 2-7                         [1, 10, 32, 32]           --
│    └─Conv2d: 2-8                       [1, 10, 32, 32]           910
│    └─ReLU: 2-9                         [1, 10, 32, 32]           --
│    └─MaxPool2d: 2-10                   [1, 10, 16, 16]           --
├─Sequential: 1-3                        [1, 3]                    --
│    └─Flatten: 2-11                     [1, 2560]                 --
│    └─Linear: 2-12                      [1, 3]                    7,683
==========================================================================================
Total params: 10,693
Trainable params: 10,693
Non-trainable params: 0
Total mult-adds (M): 6.75
==========================================================================================
Input size (MB): 0.05
Forward/backward pass size (MB): 0.82
Params size (MB): 0.04
Estimated Total Size (MB): 0.91
==========================================================================================
```
# Download Script to your code
Some cases, we need build-in in our code to download a python script and load it normally.
```python
import requests
from pathlib import Path

# Download helper functions from Learn PyTorch repo (if not already downloaded)
if Path("helper_functions.py").is_file():
  print("helper_functions.py already exists, skipping download")
else:
  print("Downloading helper_functions.py")
  # Note: you need the "raw" GitHub URL for this to work
  request = requests.get("https://raw.githubusercontent.com/mrdbourke/pytorch-deep-learning/main/helper_functions.py")
  with open("helper_functions.py", "wb") as f:
    f.write(request.content)

from helper_functions import accuracy_fn
```

# Training on CPU is faster?
According to [03-notebook] in pytorch deeplearning course, this question was asked as when evaluting the time used on GPU was larger it was on CPU!
```
Our model trained but the training time took longer?

Note: The training time on CUDA vs CPU will depend largely on the quality of the CPU/GPU you're using. Read on for a more explained answer.

Question: "I used a a GPU but my model didn't train faster, why might that be?"

Answer: Well, one reason could be because your dataset and model are both so small (like the dataset and model we're working with) the benefits of using a GPU are outweighed by the time it actually takes to transfer the data there.

There's a small bottleneck between copying data from the CPU memory (default) to the GPU memory.

So for smaller models and datasets, the CPU might actually be the optimal place to compute on.

But for larger datasets and models, the speed of computing the GPU can offer usually far outweighs the cost of getting the data there.

However, this is largely dependant on the hardware you're using. With practice, you will get used to where the best place to train your models is.
```

# Common Deep Learning Issues
According to the Pytorch Deep Learning course, it try to highlight the most three common issues:
```
Note: What we've just gone through are three of the classical and most common deep learning and PyTorch issues:

    Wrong datatypes - our model expects torch.float32 where our original custom image was uint8.
    Wrong device - our model was on the target device (in our case, the GPU) whereas our target data hadn't been moved to the target device yet.
    Wrong shapes - our model expected an input image of shape [N, C, H, W] or [batch_size, color_channels, height, width] whereas our custom image tensor was of shape [color_channels, height, width].

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
- [CNN explainer](https://poloclub.github.io/cnn-explainer/).
- Making machine learning models faster by horace-brr_intro, found [here](https://horace.io/brrr_intro.html).
- The Scalling Hypothesis - by gwren, found [here](https://gwern.net/scaling-hypothesis).
- Introducing Triton: Open-source GPU programming for neural networks by OpenAI, found [here](https://openai.com/research/triton).
