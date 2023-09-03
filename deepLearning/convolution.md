# Deep Learning - Convolution
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/a575c47c-e668-4d54-b856-833480582ae1)

## Table of Content
- [Deep Learning - Convolution](#deep-learning---convolution)
  - [Table of Content](#table-of-content)
  - [Abstract](#abstract)
  - [What made the jump to use deep learning in computer vision field?](#what-made-the-jump-to-use-deep-learning-in-computer-vision-field)
  - [Motivation to Introduce Conveolution Concept](#motivation-to-introduce-conveolution-concept)
  - [Convolution](#convolution)
    - [What does convolution mean in math?](#what-does-convolution-mean-in-math)
    - [What is the different between correlation and convolution?](#what-is-the-different-between-correlation-and-convolution)
    - [What does 'slid' mean in convolution?](#what-does-slid-mean-in-convolution)
    - [Technical Note](#technical-note)
  - [Filter/Kernel](#filterkernel)
    - [Vertical Edge Detector](#vertical-edge-detector)
      - [How to calculate the convolution ?](#how-to-calculate-the-convolution-)
      - [Examples](#examples)
      - [Learning to Detect Edges](#learning-to-detect-edges)
      - [Other Common Used Filters for Vertical Edge Detection](#other-common-used-filters-for-vertical-edge-detection)
  - [Padding](#padding)
    - [Problem statement](#problem-statement)
    - [Padding Definition](#padding-definition)
    - [Why to Use Padding?](#why-to-use-padding)
    - [Output Shape After Padding](#output-shape-after-padding)
    - [Types of Padding \[Valid vs Same\]](#types-of-padding-valid-vs-same)
    - [Importants of Padding](#importants-of-padding)
    - [Technical Note: Odd-Sized Filters in 'SAME' Convolution](#technical-note-odd-sized-filters-in-same-convolution)
  - [Strided Convolution](#strided-convolution)
    - [How does it work?](#how-does-it-work)
    - [Effect of Stide](#effect-of-stide)
    - [Why to use Stride?](#why-to-use-stride)
    - [Important Note](#important-note)
  - [Volume Convolution](#volume-convolution)
    - [Dealing with Three channels Image](#dealing-with-three-channels-image)
    - [Dealing with multiple Filters](#dealing-with-multiple-filters)
    - [Output Dimentions](#output-dimentions)
    - [Convolution on RGB image](#convolution-on-rgb-image)
    - [One Layer Convolution Neural Network](#one-layer-convolution-neural-network)
    - [Summary of Notation](#summary-of-notation)
    - [Number of Parameters Calculation](#number-of-parameters-calculation)
    - [One Layer Convolution - Multiple Filters](#one-layer-convolution---multiple-filters)
    - [Convolution Multiplication Visuale Example](#convolution-multiplication-visuale-example)
  - [Pooling Layer](#pooling-layer)
    - [HyperParameters](#hyperparameters)
    - [Types of Pooling](#types-of-pooling)
  - [CNN Example](#cnn-example)
  - [Why Convolution](#why-convolution)
  - [Transponsed Convolution](#transponsed-convolution)
    - [Upsampling: Nearest Neighbors](#upsampling-nearest-neighbors)
    - [Checkboard Pattern](#checkboard-pattern)
  - [Multiple Input](#multiple-input)
  - [Case Studies: Classic Networks](#case-studies-classic-networks)
    - [LeNet-5](#lenet-5)
      - [Architecture](#architecture)
      - [Pros \& Cons](#pros--cons)
    - [AlexNet](#alexnet)
      - [Architecture](#architecture-1)
      - [Pros \& Cons](#pros--cons-1)
      - [ILSVRC](#ilsvrc)
      - [Local Response Normalization "LRN"](#local-response-normalization-lrn)
    - [VGG-16](#vgg-16)
      - [Architecture](#architecture-2)
      - [Pros \& Cons](#pros--cons-2)
  - [Comparison between Classic Networks](#comparison-between-classic-networks)
  - [Case Studies: Residual Neural Networks](#case-studies-residual-neural-networks)
    - [Vanishing Gradient in CNN](#vanishing-gradient-in-cnn)
    - [Residual Block](#residual-block)
    - [Architecture](#architecture-3)
    - [Why do residuals networks work?](#why-do-residuals-networks-work)
    - [Identiy Function](#identiy-function)
    - [Pros \& Cons](#pros--cons-3)
    - [Popular Models](#popular-models)
  - [Case Studies: Inception Networks](#case-studies-inception-networks)
  - [Case Studies: Mobile Net](#case-studies-mobile-net)
    - [Motivation](#motivation)
  - [Practical Advices using ConvNet](#practical-advices-using-convnet)
    - [Data Augmentation](#data-augmentation)
    - [State of Computer Vision](#state-of-computer-vision)
  - [Detection Algorithms](#detection-algorithms)
    - [Object Localization](#object-localization)
    - [Landmark Detection](#landmark-detection)
    - [Object Detection](#object-detection)
  - [Detection Algorithms - YOLO Algorithm](#detection-algorithms---yolo-algorithm)
  - [Detection Algorithms - Semantic Segmentation](#detection-algorithms---semantic-segmentation)
  - [Face Recognition](#face-recognition)
    - [One Shot Learning](#one-shot-learning)
    - [Siamese Network - Deep Face](#siamese-network---deep-face)
  - [Neural Style Transfer](#neural-style-transfer)
  - [Credits](#credits)

## Abstract
Computer vision is a field of artificial intelligence (AI) that enables computers and systems to derive meaningful information from digital images, videos, and other visual inputs, then take actions or make recommendations based on that information.

Our focus here is using deep learning to help in computer vision field.

![video](https://miro.medium.com/v2/resize:fit:640/1*NLnnf_M4Nlm4p1GAWrWUCQ.gif)

## What made the jump to use deep learning in computer vision field?
1. __Feature Learning__: Traditional computer vision methods often required manual engineering of features to represent patterns in images. Deep learning automates this process by learning features directly from data, eliminating the need for hand-crafted features and making the learning process more data-driven.
  
2. __Hierarchical Representations__: Deep learning models can learn hierarchical representations of data. This mimics the hierarchical nature of visual information processing in the human brain, allowing models to learn intricate patterns and abstractions at different levels.

3. __End-to-End Learning__: Deep learning enables end-to-end learning, where a model learns to perform a task directly from raw input to output. This contrasts with traditional pipelines that involved multiple steps, potentially leading to loss of information.

4. __Data Availability__: The growth of digital data and the availability of large labeled datasets (e.g., ImageNet) provided the necessary resources to train deep neural networks effectively.

5. __Hardware Advances__: The advancement of hardware, including GPUs (Graphics Processing Units), made it feasible to train and run deep neural networks efficiently, allowing researchers to tackle complex problems.

6. __Representation Power__: Deep neural networks have the capacity to represent highly complex functions. This enables them to capture intricate patterns and relationships in images.

7. __Transfer Learning__: Pretrained deep learning models can be fine-tuned for specific tasks, allowing researchers to leverage learned features from one task to another, even with limited data.

8. __Breakthroughs in Other Domains__: Deep learning showed remarkable success in domains like speech recognition and natural language processing, motivating researchers to explore its potential in computer vision.

9.  __Breakthrough Results__: Deep learning models consistently achieved state-of-the-art performance in benchmark computer vision tasks, such as image classification, object detection, and segmentation.

10. __Flexibility and Adaptability__: Deep learning models are highly adaptable and can be customized for different tasks without redesigning the entire pipeline.

11. __Neural Network Architectures__: The development of novel neural network architectures, such as convolutional neural networks (CNNs), recurrent neural networks (RNNs), and transformers, specifically designed for handling structured data like images, played a significant role in driving the shift.

12. __Open Research and Collaboration__: The open sharing of research, code, and models within the deep learning community facilitated rapid advancements and widespread adoption.

In essence, the combination of improved performance, increased availability of data, advances in hardware, and the emergence of innovative deep learning architectures converged to create a compelling case for researchers to embrace deep learning as a game-changing approach in computer vision

## Motivation to Introduce Conveolution Concept
In real life, we deal with images with high resolution like 1000x1000 from a 1 Mega pixles camera, So that would be 3M vector of features for a deep neaural network to learn. So it is not optimal solution to use classic traditional neural network with images.

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/faafa5c4-7b33-4338-a059-7a9e86ab28c5)

## Convolution
### What does convolution mean in math?
In mathematics, convolution is an operation that combines two functions to produce a third funcrion. It's mathematical concept often used in various fields, including signal processing, image processing, probability theory, and more.

The convolution operation involces integrating the product of two funcrions as one funcrion "slides" over the other. It's represneted by the symbol "*".

Mathematically, the convolution of two functions f and g is denoted as (f∗g)(f∗g) and is defined as:

![image](https://www.gstatic.com/education/formulas2/553212783/en/convolution.svg)

Here's a breakdown of the terms in this formula:
- f and g are the two functions being convolved.
- t is the variable representing the output of the convolution.
- τ is a dummy variable used for integration.
- g(t−τ)g(t−τ) represents the second function gg shifted by τ units to the right. This effectively flips g and slides it over f.
- The integration is performed over all possible values of τ, which in the case of continuous functions, ranges from −∞ to +∞.

__In practical terms, convolution helps in understanding how two functions interact when one is "slid" over the other, taking into account their overlapping values__. 

### What is the different between correlation and convolution?
Correlation is measurement of the similarity between two signals/sequences. Convolution is measurement of effect of one signal on the other signal.

Convolution is to preserve the __spatial relationship__ between pixels by learning image features in small lttle pathces of image data, like describing a nose in human face; That's why we don't enter the image as a vector, instead we enter it as a __2D matrix__.

So To do, we need element multiplication between filtter & patch data.

### What does 'slid' mean in convolution?
In the context of convolution operation, 'sliding' refers to the process of moving a filter (also known as kernal) across an input signal or image. This filter is usually a small matrix that represents a certain pattern or feature. As the filter slides or moves accross the input, it computes element-wise products with the overlapping portions of the input, and then sums up these products to produce an output value.

![convolution](https://miro.medium.com/v2/resize:fit:679/1*Fw-ehcNBR9byHtho-Rxbtw.gif)

Imagine the input signal or image as a grid, and the filter as a smaller grid that you're placing on top of the input grid. When you slide the filter across the input grid, you align its elements with different portions of the input at each position. At each position, the element-wise products of the filter and the overlapping input values are computed and summed to produce a single value in the output grid.

Sliding the filter allows the convolution operation to capture local patterns, features, and relationships within the input. The distance by which you slide the filter at each step is called the "stride." The stride determines how much the filter moves between positions. A smaller stride means the filter moves in smaller steps, capturing finer details, while a larger stride skips more positions, capturing more general features.

### Technical Note
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/25ce48ed-5d41-407f-91e0-0f4cba668a56)

- In Math, Cross-correlation just a name they love to say for convolution.
- In math, convolution is just __slip: “Flip Vertical then Flip Horizontal”__ the filter then do the element wise multiplication.
- A Funny fact, this slip is just to achieve the property of Association, but in convolution neural network, they do not this property.
- That’s why we don’t slip our filter in CNN.

## Filter/Kernel
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/7ae94cf6-dd3d-457c-8d11-9e288908bb78)

Let's explore more about the first function which slid over the input function, we call the slid function a "Filter/Kernel", and the other function which will be our input image. They both are metrics, which could have a variety of dimensions.

The filter is a specific feature extraction, some of them are designed to detect the edges in images, nose in face, or special shape in the image. As these filter are just a numeric matrix, so the value of the matrix defines the extracted feature after computing the convolution with the image.

Deep learning help in training and defining the matrix value of the filter to detect certain feature.

### Vertical Edge Detector
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/8e758e67-da67-4219-b88c-c536a906918f)
 It is a convolution kernel that is used to detect vertical edges in an image. It is a 3x3 kernel that has all zeros except for the center element, which is 1. The kernel is applied to the image by multiplying each pixel in the image with the corresponding element in the kernel and then summing the results. The output of the convolution operation is a new image that highlights the vertical edges in the original image.

Vertocal Edge filter must be have Bright Pixels in the left, and Dark Pixels in the right. We don't really care about the middle pixels

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/4017fca3-9760-4e6a-b486-ee7b55fc385a)

#### How to calculate the convolution ?
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/caca5bcd-8615-43f8-bc97-b9943c2a555a)

#### Examples
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/af0063e8-0cff-48e9-b6a0-41fccb42fc5f)

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/b3696ca6-685e-4d95-96c5-01dbb6346c18)

#### Learning to Detect Edges
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/e68a1ba2-87fa-4441-9871-b4915c845a41)

1. There are other types of vertical edges filters; the advantage of this is it puts a little bit more weight to the central row, the central pixel, and this makes it maybe a little bit more robust.
2. Use Neural Network to learn filter value for vertical filter using forward & backward propagation.
3. Can even train the Neural Network to make filter that detect edges with line angle like 45, 70, or even 73 degrees.
   
#### Other Common Used Filters for Vertical Edge Detection
|Kernel|	Matrix|	Advantages|	Disadvantages|	When to Use|
|--|--|--|--|--|
|Sobel Vertical|	-1 0 1<br>-2 0 2<br>-1 0 1|	- Emphasizes edges effectively<br>- Computationally efficient|	- Sensitive to noise|	General edge detection, real-time applications|
|Scharr Vertical|	-3 0 3<br>-10 0 10<br>-3 0 3|	- Better edge preservation than Sobel<br>- More accurate gradients	|- Similar to Sobel (some cases)|	When accurate edges are crucial|
|Prewitt Vertical|	-1 0 1<br>-1 0 1<br>-1 0 1|	- Simple and computationally efficient<br>- Detects edges well|	- Some edge blurring	|Quick edge detection with simple setup|
|Roberts Cross Vertical|	0 1<br>-1 0|	- Simple and computationally efficient<br>- Diagonal edge detection	|- Limited accuracy in all directions|	Limited space or quick edge detection
|Canny (Directional Derivative)	|Various	|- High-quality edges with non-max suppression<br>- Performs well at low thresholds	|- Computationally more intensive	|High-quality edge detection, fine-tuning required

Keep in mind that the Canny edge detector involves more than just a single kernel; it includes multiple steps such as Gaussian smoothing, gradient computation, non-maximum suppression, and hysteresis thresholding. The table provides a concise overview of these edge detection kernels' characteristics, but the choice of kernel should be based on the specific requirements and characteristics of the image data and the desired results

## Padding
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/00bced76-5184-4c39-a570-0689f0f786c4)

### Problem statement
During the convolution process, the sliding filter does not actually visit all the pixels the same number of times, so not all the pixels in the images are treated the same by the filter, specially the pixels in the boundaries. This leads to a reduction in the spatial dimensions of the output.
What if there is a whole dog in the pixels in the edge? So we want to make sure our model deals with every pixel equally.

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/e63bad77-948f-47fd-9b1e-88443be72562)

### Padding Definition
So to solve this, w'll use padding; to make sure each pixel is visited same number of times.

Padding in the context of image processing and convolutional neural networks (CNNs) refers to the practice of adding extra pixels around the boundary of an image or feature map. Padding is used to control the spatial dimensions of the output after performing convolution or pooling operations.

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/75902d71-39f3-4ba4-bd12-de06fec13de7)

### Why to Use Padding?
There are two problems happen to image:
1. Doing convolution of image with a filter, the image shrinks in size.
   1. But we don't want the image to be shrinked every time we do edge detection or feature extraction.
   2. Assume we have 1000 layers, so we don't want the image to be shrinked in each layer.
2. Pixels in the __corner__ are less used compared to the ones in the __center__, where filter overlap that pixels multiple times.

That's why we use padding to solve this problems.

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/4f3ca3b5-034d-4b40-805a-0de72f0c5ff5)

### Output Shape After Padding
size of the image after convolution with a filter:
- Without Padding: __n - f + 1__
- With Padding: __N + 2*p - f + 1__

### Types of Padding [Valid vs Same]
__Valid (No Padding)__
- The output shape of the image is shrinked, padding is not used.
- In valid padding, no extra pixels are added to the image or feature map before convolution. As a result, the spatial dimensions of the output feature map are smaller than those of the input. This can lead to a loss of information at the image boundaries

__Same Padding__
- The output shape is the same as the input shape, padding is used.
- In same padding, extra pixels are added around the input image or feature map so that the spatial dimensions of the output feature map remain the same as those of the input. This helps in retaining spatial information and makes it easier to stack multiple layers without significant loss of dimensionality.

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/9af88ed9-7df8-4078-83c3-e6021bae8831)

### Importants of Padding
- It helps preserve spatial dimensions, which can be important for retaining contextual information and preventing information loss.
- It assists in centering the convolutional filter on the input pixels, which can improve feature extraction.
- It ensures that pixels at the image boundaries receive the same treatment as central pixels, reducing edge artifacts.

In the context of CNNs, padding is typically specified as a parameter when defining the architecture. The amount of padding added to each side of the input depends on the size of the filter and the chosen padding strategy

### Technical Note: Odd-Sized Filters in 'SAME' Convolution
Filters are usually odd-sized, and Two reasons for that:
1. __Asymetric Padding__:
   1. If filter is even, "f" is even, so you need to give asymmetric padding, which is not reasonable.
   2. More explaining: When applying a filter to an image, padding is often added to the image to maintain its spatial dimensions. If the filter size ('f') is an even number, applying symmetric padding would cause the filter to be centered directly on a pixel, leading to uneven padding on both sides. This is not reasonable because it would introduce an asymmetry that could affect the interpretation of the output. Therefore, using an odd-sized filter helps to ensure that symmetric padding can be applied, maintaining balance and consistency in the operation.
2. __Central Position and Distinguisher__:
   1. Then it has a central position and sometimes in computer vision it's nice to have a distinguisher.
   2. More explaining: An odd-sized filter has a central position, which means there is a single pixel at the center of the filter. This central pixel helps in capturing the essence of the local information within the filter's receptive field. In computer vision tasks, having a central pixel aids in capturing symmetry and patterns in images. Additionally, using an odd-sized filter provides a clear distinguisher, making it easier to define a focal point and understand the structure of the filter.

## Strided Convolution
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/f0d01d5c-4a3f-4df0-b1e3-a58a6172922d)

In a standard convolution, a filter is applied to an input image by sliding it over the image with a fixed step size. Strided convolutions introduce the concept of a "Stride", which determines the step size at which the filter moves accros the input image.

### How does it work?
In a traditional convolution operation:
- The filter is placed at the top-left corner of the image.
- The filter slides horizontally and vertically across the image pixel by pixel.
- At each position, the element-wise multiplication of the filter and the overlapping image region is computed, and the results are summed to form a single value in the output feature map.

With strided convolution:
- The filter is still placed at the top-left corner of the image.
- However, the filter slides across the image with a defined step size called the "Stride".
- At each stride position, the element-wise multiplication and summation occur as usual, producing an output value in the feature map.

Stride is represented by division in the equation; because it is the number of pixels that the kernel skips over when it is applied to the input image. For example, if the stride is 2, then the kernel will skip over 1 pixel in the input image for every 2 pixels that it scans.

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/df1e3d41-a1e1-4e89-9d03-b8a430a26f0f)

Remember that Striding is in Horizontal and Vertical axises.

### Effect of Stide
The main effect of using a strode larger than 1 is a reduction in the spatial dimentions of the output feature map. A larger stride means the filter "Skips" over more pixels, leading to fewer output values. This reduction is spatial dimensions can be useful for downsampling or reducing computational complexity.

### Why to use Stride?
For varous reasons:
1. __Downsampling__: Using a larger stride reduces the spatial resolution of the feature map, which can be useful for downsampling and dimensionality reduction in the networks.
2. __Reduced Computational Complexity__: Larger strides results in fewer computations, making the process faster and less memory-intense.
3. __Feature Reduciotn__: Strided convolutions can help reduce overfitting by forcing the network to capture more important features due to the reduced number of computations.
4. __Pooling Replacement__: Strided convolutions can replace pooling layers in some architectures, offering more control over feature extraction.

### Important Note
However, using larger strides can also lead to information loss, as some spatial details might be skipped over the filter.

Strided convolutions are often combined with other techniques like dilation, padding, and skip connections to mitigate these issues and maintain the network's ability to capture important features.

## Volume Convolution
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/f9bd227f-71d1-43d0-bd8f-92cdf478d6e8)

### Dealing with Three channels Image
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/5db78db8-7597-4d7c-8694-4b80286a5104)

In this case, we will use filter that has same number of channels like the input image, and the output will be a single channel feature image.

### Dealing with multiple Filters
What if we need to detect vertical & horizontal edges?, In this case we will use two filters:
- Yellow: Vertical Edge Detector -> Output is 1 channel.
- Orange: Horizontal Edge Detector -> Output is 1 channel.
  
Then Combine both outputs of the two filters together to make a two channel output.
- __So Number of Channels in the output image = #Filters used__.

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/474b05cc-37bf-4705-98b3-994b07aad563)

But remember that we are dealing with RGB image, which is a 3 channels image like in the image above (6 x 6 x 3), So in this case, each of the filters [yellow: vertical, orange: horizontal] will be also a 3 dimentional filter, so each channel of R, B, & G will have an applied filter on it.

### Output Dimentions
To summarize the dimention like in the image:
```
  n x n x n_c * f x f x n_c  -> n-f+1 x n-f+1 x n_c` 
  6 x 6 x 3     3 x 3 x 3         4   x   4   x  2

  Where:
    n : input image shape dimention.
    n_c : the number of channels.
    * : Convolution operation.
    f : filter shape dimention.
    n_c` : Number of used filters.
  
  Assuming padding = 0, stride = 1
```
### Convolution on RGB image
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/cf461885-c9f3-4b9e-a5d5-4ec441c119a6)

In this case, we will have a filter with three channels n_c = 3, as each channel will be will be convolutioned with its correponding image color channel, and the output will be a single channel.

For example illustrated above, we just need a red channel edge detector, then all other results from the convolution of the G, & B channels will be zeros.

### One Layer Convolution Neural Network
When you convolute a filter with shape (3x3x3) with RBG image with shape (6x6x3), the output feature map image will be with shape (4x4x1), as we have only one filter applied to the image. 

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/6080c854-4d7f-48f3-a59a-bfacae2d0bb0)

Let's see how this actually happens under the hood:
- The filter applied has a three channels, so each channel will be applied to each channel of the RGB image indevidually, each of the multiplication is element-wise, resulting in three separate feature maps (one for each channel). These feature maps represent the response of the filter to each color channel.
- Each of these features map are summed together into a single featuere map which will have a shape of (4x4x1).
- Adding a bias term to the output.
- Applying activation function like Relu, to have a final output feature map.

### Summary of Notation
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/e8731001-aedb-4d57-8d22-4922698285d7)

Where:
- M: Number of activation layers.

### Number of Parameters Calculation
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/8729ab7b-26e8-4b53-8c7c-a9b47bdde759)

To calculate the total paratmeters required for training in the convolution neural network:
- Weights paramters = 3 * 3 * 3 = 27 paramters.
- Bias Term = 1

So the total number of parameters will = 27 + 1 = 28 

### One Layer Convolution - Multiple Filters
If we have two filters, how the convolutions work between an input image, and the two filters?
- The same approach to calculate the output feature image (n_H, n_W), for each filter individually, where each filter has shape (f, f, n_C_prev).
- Then stacking the filter outputs into one single output volume (n_H, n_W, n_C), where n_C is the number of filters which in this case will be equal to 2.

The figures below illustrate how the process works:

1- Calculating the ouptut of the first applied filter.
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/e624607e-8238-4e8a-9047-e3429c3ab860)

2- Calculating the second output from the second filter.
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/0e9a118e-cd7a-44f9-88ee-8783782748d3)

3- Stacking the two outputs together into single output volume with shape (n_H, n_W, n_C).
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/d1fe037e-14ae-4b64-9499-1e5b01801a77)

Numerical Example:

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/07816791-09cf-463c-a4ef-93465b0769d2)

Note: As we go deep in CNN
- Image dimentions decrease.
- Number of filters increase.
  
### Convolution Multiplication Visuale Example
A great guide for [visuale illustration](https://cs231n.github.io/assets/conv-demo/index.html) descripted in the [CS231n: Convolutional Neural Networks for Visual Recognition](https://cs231n.github.io/convolutional-networks/#conv)

## Pooling Layer
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/21ee794c-9d0d-40d7-bcb9-53ffbdd6e427)

Pooling operates on individual feature maps produced by the convolutional layers. It replaces a group of adjacent pixels with a single value, thus reducing the spatial resolution of the feature map. The general idea is to capture the most important information while reducing the computational complexity and the risk of overfitting
So it is a technique to reduce the information in an image while maintaining features.

 ConvNets often also use pooling layers to: 
- reduce the size of the representation, to speed the computation.
- make some of the features that detects a bit more robust.

### HyperParameters
Pooling layer has a set of hyperparameters:
- f : filter size.
- s : Stride size.

__Pooling Layer has Hyperparameters to set, but don’t have a parameter to learn. (for ex. Nothing for gradient descent to learn)__

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/afbc5b3d-e699-453e-a644-e87239f84436)

### Types of Pooling
Max Pooling:
- In max pooling, each output value of the pooled feature map is the maximum value within the corresponding region of the input feature map. 
- Max pooling helps preserve the most prominent features in a given region, making it effective for identifying spatial patterns regardless of their precise location.

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/df11f6fd-c8d7-47b6-988d-e847dfdc7afc)

Average Pooling:
- In average pooling, each output value is the average of all values in the corresponding region of the input feature map. 
- Average pooling can help mitigate noise and provide a more generalized representation.

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/8603e90c-d9e9-421d-994f-abd4b0293e64)

## CNN Example
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/43872116-9cd0-41e0-b107-a23535dbbf5d)

Let's take a fully CNN example which consists of a input of a RGB image, passing through the following architecture, which consists of [Convolution layer, pooling layer, a second convolution layer, a second pooling layer, a three fully conected layers, one final activation softmax function].

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/895fa879-acf0-4436-ae41-87a002fcc76b)

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/e9e63f06-c566-4337-aeb3-1732695235a6)

Remember: Each image (3 channels) go through each filter individually.
Here are the 5 typos:
1. (5 * 5 * 3 + 1) * 8 = 608; This "8" because the activation shape has 8 channels.
2. (5 * 5 * 8 + 1) * 16 = 3216; This "16" because the activation shape has 16 channels.
3. In the FC3, 400*120 + 120 (not 1) = 48120, since the bias should have 120 parameters, not 1.
4. Similarly, in the FC4, 120*84 + 84 (not 1) = 10164
5. Finally, in the softmax, 84*10 + 10 = 850

Note: Here, the bias is for the fully connected layer.  In fully connected layers, there will be one bias for each neuron, so the bias become In FC3 there were 120 neurons so 120 biases.

## Why Convolution
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/309d9bc8-2a0f-47f6-8c2e-cd2b832cd39e)

Compared to fully conceted layer where if we pass an image, so all pixels are converted to a single vector, where each pixel has a neuron for it (assuming that), so for example if we have an image with shape [32 * 32 * 3] which equals to 3072 parameters + 3072 bias.
So the convolution neuron network have in contrast a low number of parameters, which reduce the complexity of comuptation process, and also reduce overfitting.

There are two most common reasons for why convolutions:

1- __Parameters Sharing__: means that the same set of learnable weights (paramters) is used for multiple positions within the input data. This concept is valuable in computer vision & image processing for the following task:
- __Local Feature Detection__: in images, local patters, such as edges, textures, and corners, often occure repeateally in different regions. For instance, a feature detector (such as vertical edge detector) that's usefull in one part of the image is problably usefull in another part of the image. Parameter sharing allows a single set of weights to be applied across different parts of the image, making in possible for the network to learn to detect these local features more efficiently.
- __Reduced Model Complexity__: without parameter sharing, a fully connected layer would require a large number of unique parameters, especially when dealling with high-resolution images. This leads to a high computational & memory burden. Convolution layers alleviate this issue by resuing the same weights across the input, resulting in a much more compact model.
- __Translation Invariance__: parameters sharing contributes to a property called translation invariance. This means that the network can recognize the same feature or pattern regardless of its exact location in the input. For example, if an edge detector filter detects a vertical edge in one part of the image, it can also recognize the same vertical edge in a different location.

2- __Sparsity of Connections__: Convolutional layers enforce a sparsity of connections, which means that each output value depends only on a small, local subset of input values, unlike in a fully conected layer where each output node is connected to all input nodes. 

The idea of sparsity of connections is that only the input nodes that are relevant to the output node need to be connected. By sparsifying the connections, the model can learn more efficiently

This sparsity has several advantages:
- __Efficient Computation__: With fully connected layers, every neuron in a layer is connected to every neuron in the preceding layer, resulting in a dense and computationally expensive architecture. In contrast, convolutional layers have sparse connections, which significantly reduce the number of computations required. This is especially important for processing large images efficiently.
- __Local Receptive Fields__: Convolutional layers use small, local receptive fields (the filter size) to extract features. This local receptive field ensures that each neuron in the feature map focuses on a specific region of the input, allowing it to capture local patterns and details. This property aligns well with the hierarchical nature of visual information processing.
- __Feature Hierarchies__: By stacking multiple convolutional layers, CNNs create a hierarchy of features. Lower layers detect basic features like edges and textures, while higher layers learn to recognize more complex patterns and objects. This hierarchical structure is crucial for representing visual information effectively.
  
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/65ccb2f6-bd97-4b67-bbad-01f484a0e0e1)

From the image above: 
- Green circle - This value (zero) is only depend on the green square (convolution between filter and this part of image) only. So the rest of the image pixels don’t have effect.
- Red circle - Same thing happens to this value (30).

## Transponsed Convolution
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/9db9f00b-d0a2-40c5-9fd9-dd031c1db353)

Transposed convolution is a type of convolution that is used to upsample an image. It is also known as deconvolution or fractionally strided convolution.

In a __regular convolution__, a kernel is used to scan an input image and produce an output image. The kernel is a small matrix of weights that is used to calculate the output value at each pixel in the output image. In a __transposed convolution__, the kernel is used to scan an output image and produce an input image. The kernel is used to upsample the output image by adding zeros in between the pixels.

Transposed convolution can be used for a variety of tasks, including image upsampling, image denoising, and image super-resolution.

Note: There is no learnable parameters here.

### Upsampling: Nearest Neighbors
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/02bf6142-f41f-4c52-b94f-a930702374dc)

We have a feature map of shape 2 * 2, and require to be converted to  4 * 4 output matrix, in case of upsampling using nearest Neighbors, in the input matrix, each pixel is converted to a 2 * 2 matrix with same pixel value.

### Checkboard Pattern
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/19b56e8c-c6a3-4f26-b48b-87200da5aeff)

When doing the upsampling of an image, like the one above, the image looks like it is pixlated, which can be described by "Checkboard pattern", this is one of the problem of transposed convolution.

This problem happenes because some pixels are influenced much more heavily by other pixels, while the one around it are not. Let's dig into the image below, assume we have in image of 2 * 2 pixels, and using a filter of shape 2 * 2, and stride = 1, we want to output an image of shape 3 * 3.

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/f9cc71c0-f8b7-49e3-80c8-3a7d0c938a6c)

In this case, while calculating, output pixels are affected by various of the filter pixels, unsymetric effect, for example, the pixel in the left up corner is only affected by the value 2 in left ip corner of the filter, compared to the output centered pixel which is affected by all pixels of the filter.

## Multiple Input
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/9af37e76-f531-4617-9413-a7ac7f36c268)

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/fbde6876-cd35-4375-8384-2edbdf80a0da)

The image shows a diagram of a system with multiple inputs. The system takes in three types of data: text, numerics, and images. The image data is processed by a convolutional neural network (CNN), the text data is processed by a recurrent neural network (RNN), and the numeric data is fed directly into the fully connected layer. The outputs of the three networks are then combined to produce a final output.

Multiple input is a type of input that allows a computer to process multiple types of data at the same time. This can be useful for tasks that require the processing of different types of data, such as natural language processing, machine translation, and image recognition.

In the case of the system shown in the image, the multiple input allows the system to process text, numerics, and images data at the same time. This can be useful for tasks such as sentiment analysis, which involves understanding the sentiment of text, or image classification, which involves classifying images into different categories.

Multiple input can be implemented in a variety of ways. One way is to use a single neural network that has multiple inputs and outputs. Another way is to use multiple neural networks, each of which is specialized in processing a single type of data.

The choice of implementation depends on the specific task and the available resources.

## Case Studies: Classic Networks
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/8748e5f1-a40a-4037-9e36-2c26993d1e8a)
### LeNet-5

LeNet-5 is a convolutional neural network (CNN) architecture developed by Yann LeCun et al. in 1998. It is a simple and efficient CNN that has been used for a variety of tasks, including handwritten digit recognition and face detection.

Paper: [Gradient-Based Learning applied to document recognition](http://vision.stanford.edu/cs598_spring07/papers/Lecun98.pdf), was released in 1998, by LeCun.

#### Architecture
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/b22b76a5-aed1-4f53-9fa7-d94469da0c38)


The LeNet-5 architecture consists of seven layers:
- __Input layer__: This layer takes in the input image. The input image is a 32x32 grayscale image.
- __Convolutional layer__: This layer applies a convolution operation to the input image. The convolution operation uses a filter to extract features from the input image.
- __Avg pooling layer__: This layer downsamples the output of the convolutional layer. The average pooling operation takes the average value from each patch of the output of the convolutional layer.
- __Convolutional layer__: This layer applies another convolution operation to the output of the ReLU layer.
- __Avg pooling layer__: This layer downsamples the output of the second convolutional layer.
- __Fully connected layer__: This layer connects all of the neurons in the previous layer to a single neuron. The output of the fully connected layer is the classification of the input image.

#### Pros & Cons
Lenet-5 is a simple and efficient CNN that has been used for a variety of tasks. It is a good starting point for understanding CNNs and for developing your own CNN architectures.

Here are some of the advantages of LeNet-5:
- It is simple and efficient.
- It has been used for a variety of tasks.
- It is a good starting point for understanding CNNs.

Here are some of the disadvantages of LeNet-5:
- It is not as powerful as some of the newer CNN architectures.
- It is not as well-suited for large-scale image classification tasks.

Overall, LeNet-5 is a good choice for simple image classification tasks. It is easy to understand and implement, and it has been used successfully for a variety of tasks.

### AlexNet
AlexNet is a convolutional neural network (CNN) architecture developed by Alex Krizhevsky, Ilya Sutskever, and Geoffrey Hinton in 2012. It is a deep CNN, with eight layers, and it was the first CNN to achieve state-of-the-art results on the ImageNet Large Scale Visual Recognition Challenge (ILSVRC) in 2012.

Paper: [ImageNet Classification with Deep Convolutional Neural Networks](https://proceedings.neurips.cc/paper_files/paper/2012/file/c399862d3b9d6b76c8436e924a68c45b-Paper.pdf)

#### Architecture

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/95103a11-78b7-445b-9727-6ab0755dec07)

AlexNet is a convolutional neural network (CNN) architecture developed by Alex Krizhevsky, Ilya Sutskever, and Geoffrey Hinton in 2012. It is a deep CNN, with eight layers, and it was the first CNN to achieve state-of-the-art results on the ImageNet Large Scale Visual Recognition Challenge (ILSVRC) in 2012.

The AlexNet architecture consists of the following layers:
- __Input layer__: This layer takes in the input image. The input image is a 224x224 RGB image.
- __Convolutional layer__: This layer applies a convolution operation to the input image. The convolution operation uses a filter to extract features from the input image.
- __Max pooling layer__: This layer downsamples the output of the convolutional layer. The max pooling operation takes the maximum value from each patch of the output of the convolutional layer.
- __ReLU layer__: This layer applies the rectified linear unit (ReLU) activation function to the output of the max pooling layer. The ReLU activation function is a non-linear function that helps to improve the learning of the CNN.
- __Convolutional layer__: This layer applies another convolution operation to the output of the ReLU layer.
- __Max pooling layer__: This layer downsamples the output of the second convolutional layer.
- __Fully connected layer__: This layer connects all of the neurons in the previous layer to a single neuron. The output of the fully connected layer is the classification of the input image.
- __Dropout layer__: This layer randomly sets a fraction of the neurons to zero. This helps to prevent overfitting.

AlexNet is a deep CNN, and it is more powerful than LeNet-5. It was the first CNN to achieve state-of-the-art results on the __ILSVRC__ (explained below), and it has been used as a baseline for many other CNN architectures.

Some notes to highlight:
- Similar to LeNet, but much bigger.
- Adding Relu Activation function layer.
- Require Multiple GPU for training.
- __Local Response Normalization "LRN"__, explained below.

#### Pros & Cons
Here are some of the advantages of AlexNet:
- It is deep and powerful.
- It achieved state-of-the-art results on the ILSVRC.
- It has been used as a baseline for many other CNN architectures.

Here are some of the disadvantages of AlexNet:
- It is computationally expensive to train and deploy.
- It is not as well-suited for small-scale image classification tasks.

Overall, AlexNet is a powerful CNN architecture that has been used for a variety of tasks. It is a good starting point for understanding deep CNNs and for developing your own CNN architectures.

#### ILSVRC
The ImageNet Large Scale Visual Recognition Challenge (ILSVRC) is an annual competition in image classification and object detection. The competition is held by the ImageNet project, which is a large-scale dataset of images with human-annotated labels.

![ImageNet](https://deargen.blog/wp-content/uploads/2019/09/1.-ec9db4ebafb8eca780eb84b7.jpg)

The ILSVRC was founded in 2010, and it has been held annually since then. The competition has been instrumental in the development of deep learning, as many of the most successful deep learning models have been developed for the ILSVRC.

The ILSVRC has two main tracks: image classification and object detection. The image classification track involves classifying images into one of 1,000 object categories. The object detection track involves detecting and classifying objects in images.

The ILSVRC is a challenging competition, and the accuracy of the winning entries has improved significantly over the years. The first winner of the image classification track achieved an accuracy of 74.8%, while the winner of the 2021 competition achieved an accuracy of 96.2%.

The ILSVRC is a valuable resource for the development of deep learning models. The competition provides a benchmark for evaluating the performance of new models, and it has helped to drive the development of more accurate and efficient models.

#### Local Response Normalization "LRN"
Local Response Normalization (LRN) is a technique used in convolutional neural networks (CNNs) to normalize the responses of neurons within a local region of the network. This helps to prevent the network from learning features that are too localized and to improve the generalization of the network.
-  It's a contrast enhancement process for feature maps in convNets.
  
LRN is used in the AlexNet CNN architecture. It is applied after each convolution layer in the network. The LRN operation takes the output of the convolution layer and divides it by a normalized sum of the outputs of the neurons in a local region. The local region is defined by a window size and a stride. The window size is the number of neurons that are considered in the local region, and the stride is the number of neurons that are skipped when moving from one local region to the next.

The formula for LRN is:
```
output = input / (k * sum(input^2) + eps)

where:
  - input is the output of the convolution layer
  - k is a constant
  - sum(input^2) is the sum of the squared outputs of the neurons in the local region
  - eps is a small constant to prevent division by zero
```
The LRN operation has two main effects:
- It reduces the activations of neurons that are responding to similar inputs. This helps to prevent the network from learning features that are too localized.
- It increases the activations of neurons that are responding to different inputs. This helps to improve the generalization of the network.

LRN has been shown to be effective in improving the performance of CNNs on a variety of tasks, including image classification and object detection. However, it has also been shown to be computationally expensive, and it can sometimes lead to overfitting.

In recent years, LRN has been replaced by other normalization techniques, such as batch normalization and layer normalization. These techniques are more computationally efficient and have been shown to be more effective in improving the performance of CNNs.

### VGG-16
Vgg-16 is a convolution neural network (CNN) architecture developed by Karen Simonyan and Andrew Zisserman at the University of Oxford in 2014. It is a deep CNN, with 16 layers, and it was the runner-up in the ImageNet Large Scale Visual Recognition Challenge (ILSVRC) in 2014.

Paper: [Very Deep Convolution Networks for Large-Scale Image Recognition](https://arxiv.org/pdf/1409.1556.pdf), by Simonyan & Zisserman in 2015.
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/54fe8100-bda5-4a2c-a27b-2e3c12dbbdf3)

#### Architecture
- __Input layer__: This layer takes in the input image. The input image is a 224x224 RGB image.
- __Convolutional layer__: This layer applies a convolution operation to the input image. The convolution operation uses a filter to extract features from the input image.
- __Max pooling layer__: This layer downsamples the output of the convolutional layer. The max pooling operation takes the maximum value from each patch of the output of the convolutional layer.
- __ReLU layer__: This layer applies the rectified linear unit (ReLU) activation function to the output of the max pooling layer. The ReLU activation function is a non-linear function that helps to improve the learning of the CNN.
- __Convolutional layer__: This layer applies another convolution operation to the output of the ReLU layer.
- __Max pooling layer__: This layer downsamples the output of the second convolutional layer.
- __Repeat steps 4-6__: This is repeated five more times.
- __Fully connected layer__: This layer connects all of the neurons in the previous layer to a single neuron. The output of the fully connected layer is the classification of the input image.

Insigts: 
- Has more learnable parameters around 138M.

#### Pros & Cons
Here are some of the advantages of VGG-16:
- It is deep and powerful.
- It achieved second place in the ILSVRC.
- It has been used as a baseline for many other CNN architectures.

Here are some of the disadvantages of VGG-16:
- It is computationally expensive to train and deploy.
- It is not as well-suited for small-scale image classification tasks.

## Comparison between Classic Networks
|Characteristic|	LeNet|	AlexNet|	VGG-16|
|--|--|--|--|
Year|	1998|	2012|	2014|
Depth (Number of Layers)|	Shallow (7 layers)|	Deeper (8 layers)|	Deep (16 layers)|
Convolutional Layers	|Yes	|Yes	|Yes|
Max-Pooling Layers|	Yes|	Yes|	Yes|
Activation Function|	Sigmoid & Tanh|	ReLU|	ReLU|
Fully Connected Layers|	Yes (2 FC layers)|	Yes (3 FC layers)|	Yes (3 FC layers)|
Local Receptive Fields|	Smaller|	Larger|	Smaller|
Convolutional Filters|	Smaller (5x5, 3x3)|	Larger (11x11, 5x5)|	Smaller (3x3)|
Pooling Type	|Average Pooling	|Max-Pooling	|Max-Pooling|
Regularization|	Dropout	|Dropout|	Dropout|
Batch Normalization	|No	|No	|Yes|
|Achievements|	Handwritten Digits|	ImageNet Competition|	ImageNet Competition|

Key takeaways:
- __Depth__: LeNet is relatively shallow compared to AlexNet and VGG-16. AlexNet has more layers than LeNet, while VGG-16 is even deeper, with 16 weight layers.
- __Activation Function__: LeNet uses Sigmoid and Tanh activation functions, while AlexNet and VGG-16 use Rectified Linear Unit (ReLU) activations.
- __Convolutional Filters__: LeNet and VGG-16 use smaller 3x3 filters, while AlexNet employs larger 11x11 and 5x5 filters.
- __Pooling Type__: LeNet uses average pooling, AlexNet uses max-pooling, and VGG-16 also employs max-pooling.
- __Regularization__: All three models use dropout as a regularization technique to prevent overfitting.
- __Receptive fields__: represent the region of the input data that each neuron in a layer is sensitive to.
- __Batch Normalization__: VGG-16 incorporates batch normalization to stabilize training and improve convergence.
- __Achievements__: LeNet pioneered CNNs for handwritten digit recognition. AlexNet won the ImageNet competition and popularized deep learning. VGG-16 further improved ImageNet classification accuracy, establishing deeper networks as a standard in computer vision.

Each of these models contributed to the advancement of deep learning in computer vision, and their characteristics highlight the evolution of neural network architectures over time.

## Case Studies: Residual Neural Networks
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/22fe1dfe-c789-483d-a0c4-3acf9f8123bd)

Residual Network (ResNet) is a type of convolutional neural network (CNN) that uses residual connections to allow the network to learn deeper architectures without the risk of vanishing gradients.

Residual connections are connections that skip over one or more layers in the network. These connections allow the output of a layer to be added directly to the input of the next layer. This helps to prevent the gradients from vanishing as the network becomes deeper.

ResNet was the first CNN architecture introduced the "Residual Block" (explained below), after that other CNN architectures started using this blocks like: DenseNet and InceptionNet.

ResNet was introduced by He et al. in 2015. It won the ImageNet Large Scale Visual Recognition Challenge (ILSVRC) in 2015 and 2016.

Paper: [Deep Residual Learning for Image Recognition](https://arxiv.org/pdf/1512.03385.pdf), by He et al, in 2015.

### Vanishing Gradient in CNN
The vanishing gradient is a problem that occur in deep learning when the gradient, of the loss function with respect to the parameters of the network, become very small as the network becomes deeper. This can make it difficult for the network to learn, as the updates to the parameters become very small.

The vanishing gradient problem occurs in CNNs because of the way that convolutions are performed. Convolutions involve multiplying the input image by a filter, and then summing the results. This operation can be thought of as a weighted sum of the input pixels.

The weights of the filter are learned during the training. However, as the network becomes deeper, the weights of the filter become smaller. This is because the filter is applied to a smaller and smaller patch of the input image.

As the weights of the filter become smaller, the gradients of the loss function with respect to the weights also become smaller. This can lead to the vanishing gradient problem.

### Residual Block
A residual block consists of two convolution layers, followed by a ReLU activation function. The output of the first convolution layer is added to the output of the second convolution layer. This is called the residual connection.

The residual connection helps to prevent the vanishing gradient problem by adding a shortcut from the input of a layer to the output of the layer. This shortcut allows the gradients to flow through the network even if the weights of the filters become very small.

Note: in the image below, Andrew was explaining the residual block on two fully connected layers instead of ConvNet, for just explaining the connection for simplicity.

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/4105bc7c-5a05-4bb9-aef7-d0e2bdb3dfc6)

During calculating the weights, the equations become the follwoing:
```
z[l+1] = W[l+1] a[l] + b[l+1]
a[l+1] = g(z[l+1]) -> this is the plain cnn network.

z[l+2] = W[l+2] a[l+1] + b[l+2]
a[l+2] = g(z[l+2] + a[l])

Where:
- z[l+1]: the output before the activation function.
- W[l+1]: The weight of the next layer.
- a[l]: Input activation function of the current layer.
- b[l+1]: Bias of the next layer.
- a[l+1]: Activation function of the next layer.
```

### Architecture

The ResNet architecture consists of a stack of residual blocks. Each residual block consists of two convolution layers, followed by a ReLU activation function. The output of the first convolution layer is added to the output of the second convolution layer.

This has a better performance in the training error compared to the plain cnn network without a residual block.

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/f76aec72-6ec9-4ff6-94c0-75c039c34f7d)

The ResNet architecture can be made deeper by stacking more residual blocks. The deeper the network, the more features it can learn. However, a deeper network is also more difficult to train.

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/db15182c-2c2b-47e8-8c48-0d49171e1c8a)

The basic architecture of ResNet as follows:
```
Input layer
Residual block 1
Residual block 2
...
Residual block n
Output layer
```
The number of residual blocks can vary depending on the specific ResNet model. For example, ResNet-50 has 34 residual blocks, while ResNet-101 has 101 residual blocks.

### Why do residuals networks work?
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/d5777f39-117a-4730-b843-339973b954df)

In the last line in the image above, when the weigth & bias of the next layer are zeros, the the value of the output of activation function is still not zero, as there is another input which is the activation function of the first layer.
  - Weights --> zero, if using regularization.
  - Bias --> zero, if using decaying bias.

So The ResNet skip connection makes the network to work like a normal big NN above. This even can improve the performance; if we traied to make the hidden layers learn something helpful like feature extractions and not just doing identity function (explained below).
- As the residual connection allows the output of the first convolution layer to be added directly to the output of the second convolution layer. This means that the second convolution layer can learn to do something helpful, such as feature extraction, without having to learn to undo the work of the first convolution layer.
- For example, the first convolution layer might learn to extract edges from an image. The second convolution layer could then learn to combine these edges to form more complex features, such as shapes or objects. The residual connection ensures that the second convolution layer does not have to learn to undo the work of the first convolution layer, and can focus on learning more complex features.
  
### Identiy Function
An identity function is a function that takes an input and returns the same input. In other words, f(x) = x for all values of x.

In the context of ResNet, the identity function refers to a residual block that does not perform any convolution operations. The output of the first convolution layer is simply added to the output of the second convolution layer. This means that the second convolution layer does not have to learn to do anything, and simply passes the input through unchanged.

### Pros & Cons
Here are some of the advantages of ResNet:
- It is able to learn deeper architectures without the risk of vanishing gradients.
- It has achieved state-of-the-art results on a variety of tasks, including image classification, object detection, and segmentation.

Here are some of the disadvantages of ResNet:
- It is computationally expensive to train and deploy.
- It is not as well-suited for small-scale image classification tasks.

### Popular Models
Here are some of the popular ResNet models:
- ResNet-18: This is the smallest ResNet model. It has 18 layers.
- ResNet-34: This is a slightly deeper ResNet model. It has 34 layers.
- ResNet-50: This is a popular ResNet model. It has 50 layers.
- ResNet-101: This is a deeper ResNet model. It has 101 layers.
- ResNet-152: This is the deepest ResNet model. It has 152 layers.

These are just a few of the many ResNet models that have been developed. The choice of model depends on the specific task and the available resources.

## Case Studies: Inception Networks
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/b0fb668d-035f-473e-bac1-d421ad1da19a)

## Case Studies: Mobile Net
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/3fd46de6-6f85-4dab-bf97-db5758defb46)
### Motivation

## Practical Advices using ConvNet
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/1b9c67fb-74ec-431c-8ba4-4e162f2abe58)

### Data Augmentation

### State of Computer Vision

## Detection Algorithms
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/1e39d010-20a2-457f-b221-a005842e0482)

### Object Localization

### Landmark Detection

### Object Detection

## Detection Algorithms - YOLO Algorithm
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/8c0def3e-73bf-4bcc-9ce5-45bd58e551f3)

## Detection Algorithms - Semantic Segmentation
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/494a0eb9-4274-422b-862d-4607b9514077)

## Face Recognition
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/3950d138-4fb8-41d8-88f3-715ff469041d)

### One Shot Learning
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/1f2b1c09-b0b5-4924-8aff-840fb3d509c7)

One-shot learning is a machine learning task where the model is only given one example of each class to learn from.

### Siamese Network - Deep Face
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/6e209283-61c3-4d8d-8642-57da036d04c7)

Siamese networks are a type of neural network that are used for one-shot learning. 

Siamese networks consist of two identical neural networks that are trained together. The two networks are fed with two images, and the goal is to train the networks to output a similarity score that indicates whether the two images are of the same object or not.

Siamese networks are often used for face recognition, object recognition, and other tasks that require one-shot learning.

Here is an example of how Siamese networks can be used for face recognition:

Let's say we have a Siamese network that is trained on a dataset of faces. We want to use the network to recognize a new face. We can do this by feeding the network two images, one of the new face and one of a known face. The network will then output a similarity score that indicates how similar the two faces are. If the similarity score is high, then the network will predict that the two faces are of the same person.

Here is a diagram of a Siamese network for face recognition:

Input 1: Image of new face
Input 2: Image of known face

Network 1: Neural network that takes in the input image and outputs a similarity score
Network 2: Neural network that takes in the input image and outputs a similarity score

As you can see, the two networks are identical. They both take in an image and output a similarity score. The similarity scores from the two networks are then combined to produce a final similarity score.

Siamese networks are a powerful tool for one-shot learning. They have been used for a variety of tasks, including face recognition, object recognition, and other tasks that require one-shot learning.

## Neural Style Transfer
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/8686dc3d-026e-42b0-a093-7163cad8de15)


## Credits
[CS231n: Convolutional Neural Networks for Visual Recognition](https://cs231n.github.io/convolutional-networks/).