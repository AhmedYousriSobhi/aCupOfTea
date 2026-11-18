# nb_OOP.ipynb

<div class="code-file">

Notebook from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/programming/oop/nb_OOP.ipynb)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/programming/oop/nb_OOP.ipynb)  ·  [Open in Colab](https://colab.research.google.com/github/AhmedYousriSobhi/aCupOfTea/blob/main/programming/oop/nb_OOP.ipynb)

</div>


Author of this notebook: [Ahmed Sobhi](ahmedyousrisobhi@gmail.com)

Creation Date: 2023-07-09

Objective: Illustrate chapter #2 the Objected Oriented Programming (OOP) in Python from book: __Data Structures & Algorithms in Python__

# Chapter #2: Object Oriented Programming
## Abstract:

What does Object Oriented Mean?!
- The word object-oriented is a combination of two terms, object and oriented. The dictionary meaning of an object is "an entity that exists in the real world", and oriented means "interested in a particular kind of thing or entity".
- Object oriented referes to a programming language, system, or software methadology that is built on the concepts of logical objects
- An object-oriented programming technique that combines data and instructions for processing that data into an object that can be used within the program.

## 2.1. Goals, Principles, and Patterns
- The main “actors” in the object-oriented paradigm are called objects. Each object is an instance of a class. Each class presents to the outside world a concise and consistent view of the objects that are instances of this class, without going into too much unnecessary detail or giving others access to the inner workings of the objects. 
- The class definition typically specifies instance variables, also known as data members, that the object contains, as well as the methods, also
known as member functions, that the object can execute. 
- This view of computing is intended to fulfill several goals and incorporate several design principles, which we discuss in this chapter.

### 2.1.1. Object-Oriented Design Goals
Software implementation should achieve three main goals:
- __Robustness__:
  - Something to be robust means that is capable of handling unexpected inputs that are not explicitly defined for its application.
  - Example: if a prgram is expecting a positive integer (price of item), and instead is given a negative integer, then the program should be able to recover gracefully from this error.
  - Real-life critical applications, where a software error can lead to injury of loss of life. This point was driven home in late 1980s in accidents involving __Therac-25__, a radiation-therapy machine, which severely overdosed six patients between 1985 & 1987, some of whom died from complications resulting from their radiation overdose.
- __Adaptability__:
  - Software needs to be able to evolve over time in response to cahnging conditions in its environment. 
  - Example for this, Modern software application, shuch as Web Browsers & Internet search engines, typically involve large programs that are used for many years.
  - Another calling, Evolvability. Related to portability, which is the ability of software to run with minimal change on different hardware and os platforms.
  - Writing a software in Python is the portability provided by the language itself.
- __Reusability__:
  - Means the same code should be usable as a component of different systems in various applications.
  - Developing a quality software can be an expensive enterprise, and its cost can be offset somewhat if the software is designed in a way that makes it easily reusable in the future applications.
  - Such resure should be done with care, however, for one of the major sources of software error in Therac-25, came from inappropriate reuse of Therac-20 software, which was not object-oriented and not designed for the hardware platform used with the Therac-25.

## 2.1.2. Object-Oriented Design Principles
To facilitate the goals outlined above, some chief principles of the object-oriented approach:
- Modularity:
  - Modern software systems typically consist of several different components that must interact correctly in order for the entire system to work properly. Keeping these interactions straight requires that these different components be well organized. Modularity refers to an organizing principle in which different components of a software system are divided into separate functional units.
  - In Python, we have already seen that a module is a collection of closely related functions and classes that are defined together in a single file of source code. Python’s standard libraries include, for example, the math module, which provides definitions for key mathematical constants and functions, and the os module, which provides support for interacting with the operating system.
  - The use of modularity helps support the goals listed in Section 2.1.1. Robustness is greatly increased because it is easier to test and debug separate components before they are integrated into a larger software system. Furthermore, bugs that persist in a complete system might be traced to a particular component, which can be fixed in relative isolation. The structure imposed by modularity also helps enable software reusability. If software modules are written in a general way, the modules can be reused when related need arises in other contexts.
- Abstraction:
- Encapsulation:


