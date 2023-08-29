# Deep Learning - Convolution
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/eb553081-876c-4157-ba69-d68864745470)

## Table of Content
- [Deep Learning - Convolution](#deep-learning---convolution)
  - [Table of Content](#table-of-content)
  - [Abstract](#abstract)
  - [Motivation](#motivation)
  - [Convolution](#convolution)
    - [What does convolution mean in math?](#what-does-convolution-mean-in-math)
    - [What is the different between correlation and convolution?](#what-is-the-different-between-correlation-and-convolution)
    - [What does 'slid' mean in convolution?](#what-does-slid-mean-in-convolution)

## Abstract
Computer vision is a field of artificial intelligence (AI) that enables computers and systems to derive meaningful information from digital images, videos, and other visual inputs, then take actions or make recommendations based on that information.

Our focus here is using deep learning to help in computer vision field.

![video](https://miro.medium.com/v2/resize:fit:640/1*NLnnf_M4Nlm4p1GAWrWUCQ.gif)

## Motivation
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

In practical terms, convolution helps in understanding how two functions interact when one is "slid" over the other, taking into account their overlapping values. 

### What is the different between correlation and convolution?
Correlation is measurement of the similarity between two signals/sequences. Convolution is measurement of effect of one signal on the other signal.

Convolution is to preserve the __spatial relationship__ between pixels by learning image features in small lttle pathces of image data, like describing a nose in human face; That's why we don't enter the image as a vector, instead we enter it as a __2D matrix__.

So To do, we need element multiplication between filtter & patch data.

### What does 'slid' mean in convolution?
