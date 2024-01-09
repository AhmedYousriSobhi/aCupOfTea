# 101 - Python

# Table of Content
- [101 - Python](#101---python)
- [Table of Content](#table-of-content)
- [Concepts Highlights](#concepts-highlights)
  - [1. Primitive Datatypes and Operators](#1-primitive-datatypes-and-operators)
    - [Arithmetic](#arithmetic)
  - [2. Variables and Collections](#2-variables-and-collections)
    - [List](#list)
      - [None Object](#none-object)
    - [Tuple](#tuple)
      - [Default type is Tuple](#default-type-is-tuple)
      - [Extended Unpacking](#extended-unpacking)
    - [Dictionaries](#dictionaries)
      - [Immutable Type Key](#immutable-type-key)
      - [How Keys|Values are stored](#how-keysvalues-are-stored)
      - [Get Value by Key](#get-value-by-key)
      - [Add New Key](#add-new-key)
      - [Unpacking Options](#unpacking-options)
    - [Sets](#sets)
      - [Immutable Elements](#immutable-elements)
      - [Add More Items](#add-more-items)
      - [Intersection/Union/Difference/Symmetric](#intersectionuniondifferencesymmetric)
      - [Superset/Subset](#supersetsubset)
      - [Deep Copy](#deep-copy)
  - [3. Control Flow and Iterables](#3-control-flow-and-iterables)
    - [Handle Exceptions](#handle-exceptions)
    - [Reading/Writing to Files](#readingwriting-to-files)
      - [with Clause](#with-clause)
    - [Iterable](#iterable)
      - [Can't Access Elements by Index](#cant-access-elements-by-index)
      - [Iterator](#iterator)
      - [For Loop does Iteration Implicitly](#for-loop-does-iteration-implicitly)
      - [Grab Iterable's elements using list()](#grab-iterables-elements-using-list)
  - [4. Functions](#4-functions)
    - [Variable Positional Arguments](#variable-positional-arguments)
    - [Variable Keyword Arguments](#variable-keyword-arguments)
    - [Calling Function Expanding](#calling-function-expanding)
    - [Default Output Type is Tuple](#default-output-type-is-tuple)
    - [First Class Function](#first-class-function)
    - [Closure in Nested Functions](#closure-in-nested-functions)
    - [Anonymous Functions](#anonymous-functions)
    - [Built-in Higher Order Functions](#built-in-higher-order-functions)
      - [Diagram Explanation](#diagram-explanation)
    - [Comprehensions](#comprehensions)
      - [List](#list-1)
      - [Construct set and dict](#construct-set-and-dict)
  - [5. Modules](#5-modules)
    - [Note: Loading Module Priority](#note-loading-module-priority)
  - [6. Classes](#6-classes)
    - [Define a Class](#define-a-class)
    - [Create an Instance of a Class](#create-an-instance-of-a-class)
  - [6.1 Inheritance](#61-inheritance)
    - [Importing Parent Class](#importing-parent-class)
    - [Define Child Class](#define-child-class)
    - [Create an Instance of the Child](#create-an-instance-of-the-child)
  - [6.2 Multiple Inheritance](#62-multiple-inheritance)
    - [Another Parent Class](#another-parent-class)
    - [Child Class Inherit from multiple Parent Classes](#child-class-inherit-from-multiple-parent-classes)
    - [Create an Instance of the Child](#create-an-instance-of-the-child-1)
  - [7. Advanced](#7-advanced)
    - [Generator Functions - Yeild](#generator-functions---yeild)
      - [Breakdown the purpose of using **yield**](#breakdown-the-purpose-of-using-yield)
      - [Code Example](#code-example)
    - [Generators](#generators)
      - [Diagrammatic](#diagrammatic)
    - [Decorators](#decorators)
      - [Wrappers](#wrappers)
      - [Problem of this Method](#problem-of-this-method)
      - [Solution using **wraps**](#solution-using-wraps)
- [References](#references)

# Concepts Highlights
These illustrations are provided from [learnxinyminutes-python](https://learnxinyminutes.com/docs/python/), so they are copied and pasted to be able to add some of my own notes on them. So please refere to the original website for the complete wonderfull tutorial.

So in the following sections, we will not cover a full beginning illustration for the python, and we consider that you just want to wrap up and recall the important notes in python.

## 1. Primitive Datatypes and Operators
### Arithmetic
```python
# Integer division rounds down for both positive and negative numbers.
5 // 3       # => 1
-5 // 3      # => -2
```

```python
# i % j have the same sign as j, unlike C
-7 % 3  # => 2
```
## 2. Variables and Collections
### List
```python
# (is vs. ==) is checks if two variables refer to the same object, but == checks
# if the objects pointed to have the same values.
a = [1, 2, 3, 4]  # Point a at a new list, [1, 2, 3, 4]
b = a             # Point b at what a is pointing to
b is a            # => True, a and b refer to the same object
b == a            # => True, a's and b's objects are equal
b = [1, 2, 3, 4]  # Point b at a new list, [1, 2, 3, 4]
b is a            # => False, a and b do not refer to the same object
b == a            # => True, a's and b's objects are equal
```
#### None Object
```python
# Don't use the equality "==" symbol to compare objects to None
# Use "is" instead. This checks for equality of object identity.
"etc" is None  # => False
None is None   # => True
```
### Tuple
#### Default type is Tuple
```python
# Note that a tuple of length one has to have a comma after the last element but
# tuples of other lengths, even zero, do not.
type((1))   # => <class 'int'>
type((1,))  # => <class 'tuple'>
type(())    # => <class 'tuple'>
```
#### Extended Unpacking
```python
# You can also do extended unpacking
a, *b, c = (1, 2, 3, 4)  # a is now 1, b is now [2, 3] and c is now 4
```
### Dictionaries
#### Immutable Type Key
```python
# Note keys for dictionaries have to be immutable types. This is to ensure that
# the key can be converted to a constant hash value for quick look-ups.
# Immutable types include ints, floats, strings, tuples.
invalid_dict = {[1,2,3]: "123"}  # => Yield a TypeError: unhashable type: 'list'
valid_dict = {(1,2,3):[1,2,3]}   # Values can be of any type, however.
```
#### How Keys|Values are stored
```python
# Here is a prefilled dictionary
filled_dict = {"one": 1, "two": 2, "three": 3}
# Get all values as an iterable with "values()". Once again we need to wrap it
# in list() to get it out of the iterable. Note - Same as above regarding key
# ordering.
list(filled_dict.values())  # => [3, 2, 1]  in Python <3.7
list(filled_dict.values())  # => [1, 2, 3] in Python 3.7+
```
#### Get Value by Key
```python
# Use "get()" method to avoid the KeyError
filled_dict.get("one")      # => 1
filled_dict.get("four")     # => None
# The get method supports a default argument when the value is missing
filled_dict.get("one", 4)   # => 1
filled_dict.get("four", 4)  # => 4

# "setdefault()" inserts into a dictionary only if the given key isn't present
filled_dict.setdefault("five", 5)  # filled_dict["five"] is set to 5
filled_dict.setdefault("five", 6)  # filled_dict["five"] is still 5
```
#### Add New Key
```python
# Adding to a dictionary
filled_dict.update({"four":4})  # => {"one": 1, "two": 2, "three": 3, "four": 4}
filled_dict["four"] = 4         # another way to add to dict
```
#### Unpacking Options
```python
# From Python 3.5 you can also use the additional unpacking options
{'a': 1, **{'b': 2}}  # => {'a': 1, 'b': 2}
{'a': 1, **{'a': 2}}  # => {'a': 2}
```

### Sets
#### Immutable Elements
```python
# Similar to keys of a dictionary, elements of a set have to be immutable.
invalid_set = {[1], 1}  # => Raises a TypeError: unhashable type: 'list'
valid_set = {(1,), 1}
```
#### Add More Items
```python
# Initialize a set with a bunch of values.
some_set = {1, 1, 2, 2, 3, 4}  # some_set is now {1, 2, 3, 4}

# Add one more item to the set
filled_set = some_set
filled_set.add(5)  # filled_set is now {1, 2, 3, 4, 5}
# Sets do not have duplicate elements
filled_set.add(5)  # it remains as before {1, 2, 3, 4, 5}
```

#### Intersection/Union/Difference/Symmetric
```python
# Do set intersection with &
other_set = {3, 4, 5, 6}
filled_set & other_set  # => {3, 4, 5}

# Do set union with |
filled_set | other_set  # => {1, 2, 3, 4, 5, 6}


# Do set difference with -
{1, 2, 3, 4} - {2, 3, 5}  # => {1, 4}

# Do set symmetric difference with ^
{1, 2, 3, 4} ^ {2, 3, 5}  # => {1, 4, 5}
```

#### Superset/Subset
```python
# Check if set on the left is a superset of set on the right
{1, 2} >= {1, 2, 3} # => False

# Check if set on the left is a subset of set on the right
{1, 2} <= {1, 2, 3} # => True
```

#### Deep Copy
```python
# Make a one layer deep copy
filled_set = some_set.copy()  # filled_set is {1, 2, 3, 4, 5}
filled_set is some_set        # => False
```
## 3. Control Flow and Iterables
### Handle Exceptions
```python
# Handle exceptions with a try/except block
try:
    # Use "raise" to raise an error
    raise IndexError("This is an index error")
except IndexError as e:
    pass                 # Refrain from this, provide a recovery (next example).
except (TypeError, NameError):
    pass                 # Multiple exceptions can be processed jointly.
else:                    # Optional clause to the try/except block. Must follow
                         # all except blocks.
    print("All good!")   # Runs only if the code in try raises no exceptions
finally:                 # Execute under all circumstances
    print("We can clean up resources here")
```
### Reading/Writing to Files
```python
# Writing to a file
contents = {"aa": 12, "bb": 21}
with open("myfile1.txt", "w+") as file:
    file.write(str(contents))        # writes a string to a file

import json
with open("myfile2.txt", "w+") as file:
    file.write(json.dumps(contents)) # writes an object to a file

# Reading from a file
with open('myfile1.txt', "r+") as file:
    contents = file.read()           # reads a string from a file
print(contents)
# print: {"aa": 12, "bb": 21}

with open('myfile2.txt', "r+") as file:
    contents = json.load(file)       # reads a json object from a file
print(contents)
# print: {"aa": 12, "bb": 21}
```

Note: difference between 'r' and 'r+', answer [source](https://stackoverflow.com/questions/1466000/difference-between-modes-a-a-w-w-and-r-in-built-in-open-function)
```python

 ``r''   Open text file for reading.  The stream is positioned at the
         beginning of the file.

 ``r+''  Open for reading and writing.  The stream is positioned at the
         beginning of the file.
```

#### with Clause
```python
# Instead of try/finally to cleanup resources you can use a with statement
with open("myfile.txt") as f:
    for line in f:
        print(line)
```

### Iterable
```python
# Python offers a fundamental abstraction called the Iterable.
# An iterable is an object that can be treated as a sequence.
# The object returned by the range function, is an iterable.

filled_dict = {"one": 1, "two": 2, "three": 3}
our_iterable = filled_dict.keys()
print(our_iterable)  # => dict_keys(['one', 'two', 'three']). This is an object
                     # that implements our Iterable interface.

# We can loop over it.
for i in our_iterable:
    print(i)  # Prints one, two, three
```
#### Can't Access Elements by Index
```python
# However we cannot address elements by index.
our_iterable[1]  # Raises a TypeError
```
#### Iterator
```python
# An iterable is an object that knows how to create an iterator.
our_iterator = iter(our_iterable)

# Our iterator is an object that can remember the state as we traverse through
# it. We get the next object with "next()".
next(our_iterator)  # => "one"

# It maintains state as we iterate.
next(our_iterator)  # => "two"
next(our_iterator)  # => "three"

# After the iterator has returned all of its data, it raises a
# StopIteration exception
next(our_iterator)  # Raises StopIteration
```
#### For Loop does Iteration Implicitly
```python
# We can also loop over it, in fact, "for" does this implicitly!
our_iterator = iter(our_iterable)
for i in our_iterator:
    print(i)  # Prints one, two, three

```
#### Grab Iterable's elements using list()
```python
# You can grab all the elements of an iterable or iterator by call of list().
list(our_iterable)  # => Returns ["one", "two", "three"]
list(our_iterator)  # => Returns [] because state is saved
```
Note: the iterator of the iterable saves its state, so it will return the remaining elements that it doesn't iter over yet.

## 4. Functions
### Variable Positional Arguments
```python
# You can define functions that take a variable number of
# positional arguments
def varargs(*args):
    return args

varargs(1, 2, 3)  # => (1, 2, 3)
```
### Variable Keyword Arguments
```python
# You can define functions that take a variable number of
# keyword arguments, as well
def keyword_args(**kwargs):
    return kwargs


# Let's call it to see what happens
keyword_args(big="foot", loch="ness")  # => {"big": "foot", "loch": "ness"}
```

```python
# You can do both at once, if you like
def all_the_args(*args, **kwargs):
    print(args)
    print(kwargs)
"""
all_the_args(1, 2, a=3, b=4) prints:
    (1, 2)
    {"a": 3, "b": 4}
"""
```
### Calling Function Expanding
```python
# When calling functions, you can do the opposite of args/kwargs!
# Use * to expand args (tuples) and use ** to expand kwargs (dictionaries).
args = (1, 2, 3, 4)
kwargs = {"a": 3, "b": 4}
all_the_args(*args)            # equivalent: all_the_args(1, 2, 3, 4)
all_the_args(**kwargs)         # equivalent: all_the_args(a=3, b=4)
all_the_args(*args, **kwargs)  # equivalent: all_the_args(1, 2, 3, 4, a=3, b=4)
```
### Default Output Type is Tuple
```python
# Returning multiple values (with tuple assignments)
def swap(x, y):
    return y, x  # Return multiple values as a tuple without the parenthesis.
                 # (Note: parenthesis have been excluded but can be included)

x = 1
y = 2
x, y = swap(x, y)     # => x = 2, y = 1
# (x, y) = swap(x,y)  # Again the use of parenthesis is optional.
```
### First Class Function
```python
# Python has first class functions
def create_adder(x):
    def adder(y):
        return x + y
    return adder

add_10 = create_adder(10)
add_10(3)   # => 13
```
### Closure in Nested Functions
- Allowing inner functions to "remember" the environment in which they were created
- We will have to use **nonlocal**: The nonlocal keyword in Python is used within nested functions to modify variables that are defined in the nearest enclosing scope, excluding the global scope.
```python
# Closures in nested functions:
# We can use the nonlocal keyword to work with variables in nested scope which shouldn't be declared in the inner functions.
def create_avg():
    total = 0
    count = 0
    def avg(n):
        nonlocal total, count
        total += n
        count += 1
        return total/count
    return avg
avg = create_avg()
avg(3) # => 3.0
avg(5) # (3+5)/2 => 4.0
avg(7) # (8+7)/3 => 5.0
```
### Anonymous Functions
```python
# There are also anonymous functions
(lambda x: x > 2)(3)                  # => True
(lambda x, y: x ** 2 + y ** 2)(2, 1)  # => 5
```
### Built-in Higher Order Functions
```python
# There are built-in higher order functions
list(map(add_10, [1, 2, 3]))          # => [11, 12, 13]
list(map(max, [1, 2, 3], [4, 2, 1]))  # => [4, 2, 3]

list(filter(lambda x: x > 5, [3, 4, 5, 6, 7]))  # => [6, 7]
```
#### Diagram Explanation
- list(map(max, [1, 2, 3], [4, 2, 1]))
    ```sql
    Lists: [1, 2, 3]   [4, 2, 1]

                +------+      +------+
                |  1   |      |  4   |
                +------+      +------+
                |  2   |      |  2   |
                +------+      +------+
                |  3   |      |  1   |
                +------+      +------+
                  |            |
                  V            V

         map(max, [1, 2, 3], [4, 2, 1])

                  |            |
                  V            V

           [max(1, 4), max(2, 2), max(3, 1)]

                  |            |
                  V            V

                 [4, 2, 3]

                  |            |
                  V            V

    list(map(max, [1, 2, 3], [4, 2, 1]))

                  |            |
                  V            V

                [4, 2, 3] (Final Result as a List)

    ```
- list(filter(lambda x: x > 5, [3, 4, 5, 6, 7]))
    ```sql
    Initial List: [3, 4, 5, 6, 7]

                +-------+
                |  3    |
                +-------+
                |  4    |
                +-------+
                |  5    |
                +-------+
                |  6    |
                +-------+
                |  7    |
                +-------+
                    |
                    V

        filter(lambda x: x > 5)

                    |
                    V

        [6, 7] (Filtered Result)

                    |
                    V

        list(filter(lambda x: x > 5))

                    |
                    V

        [6, 7] (Final Result as a List)

    ```
### Comprehensions
In Python, comprehension refers to a concise and efficient way to create new sequences, such as lists, sets, or dictionaries, based on existing ones. It enables developers to generate these sequences using a compact syntax within a single line of code.
#### List
```python
# List comprehension stores the output as a list (which itself may be nested).
[add_10(i) for i in [1, 2, 3]]         # => [11, 12, 13]
[x for x in [3, 4, 5, 6, 7] if x > 5]  # => [6, 7]
```
#### Construct set and dict
```python
# You can construct set and dict comprehensions as well.
{x for x in 'abcddeef' if x not in 'abc'}  # => {'d', 'e', 'f'}
{x: x**2 for x in range(5)}  # => {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}
```

## 5. Modules
```python
# Import Modules
import math

# Get Specific function from a module
from math import floor

# Import all functions from a module, but not recommended
from math import *

# Shorten module name
import math as m

# To find out which functions and attributes are defined in a module
dir(math)
```
### Note: Loading Module Priority
If you have a Python script named math.py in the same folder as your current script, the file math.py will be loaded instead of the built-in Python module. This happens because the local folder has priority over Python's built-in libraries.

## 6. Classes
### Define a Class
```python
# We use the "class" statement to create a class
class Human:

    # A class attribute. It is shared by all instances of this class
    species = "H. sapiens"

    # Basic initializer, this is called when this class is instantiated.
    # Note that the double leading and trailing underscores denote objects
    # or attributes that are used by Python but that live in user-controlled
    # namespaces. Methods(or objects or attributes) like: __init__, __str__,
    # __repr__ etc. are called special methods (or sometimes called dunder
    # methods). You should not invent such names on your own.
    def __init__(self, name):
        # Assign the argument to the instance's name attribute
        self.name = name

        # Initialize property
        self._age = 0   # the leading underscore indicates the "age" property is 
                        # intended to be used internally
                        # do not rely on this to be enforced: it's a hint to other devs

    # An instance method. All methods take "self" as the first argument
    def say(self, msg):
        print("{name}: {message}".format(name=self.name, message=msg))

    # Another instance method
    def sing(self):
        return 'yo... yo... microphone check... one two... one two...'

    # A class method is shared among all instances
    # They are called with the calling class as the first argument
    @classmethod
    def get_species(cls):
        return cls.species

    # A static method is called without a class or instance reference
    @staticmethod
    def grunt():
        return "*grunt*"

    # A property is just like a getter.
    # It turns the method age() into a read-only attribute of the same name.
    # There's no need to write trivial getters and setters in Python, though.
    @property
    def age(self):
        return self._age

    # This allows the property to be set
    @age.setter
    def age(self, age):
        self._age = age

    # This allows the property to be deleted
    @age.deleter
    def age(self):
        del self._age
```
### Create an Instance of a Class
```python
# When a Python interpreter reads a source file it executes all its code.
# This __name__ check makes sure this code block is only executed when this
# module is the main program.
if __name__ == '__main__':
    # Instantiate a class
    i = Human(name="Ian")
    i.say("hi")                     # "Ian: hi"
    j = Human("Joel")
    j.say("hello")                  # "Joel: hello"
    # i and j are instances of type Human; i.e., they are Human objects.

    # Call our class method
    i.say(i.get_species())          # "Ian: H. sapiens"
    # Change the shared attribute
    Human.species = "H. neanderthalensis"
    i.say(i.get_species())          # => "Ian: H. neanderthalensis"
    j.say(j.get_species())          # => "Joel: H. neanderthalensis"

    # Call the static method
    print(Human.grunt())            # => "*grunt*"

    # Static methods can be called by instances too
    print(i.grunt())                # => "*grunt*"

    # Update the property for this instance
    i.age = 42
    # Get the property
    i.say(i.age)                    # => "Ian: 42"
    j.say(j.age)                    # => "Joel: 0"
    # Delete the property
    del i.age
    # i.age                         # => this would raise an AttributeError
```

## 6.1 Inheritance

Inheritance allows new child classes to be defined that inherit methods and variables from their parent class.

Using the Human class defined above as the base or parent class, we can define a child class, Superhero, which inherits the class variables like "species", "name", and "age", as well as methods, like "sing" and "grunt" from the Human class, but can also have its own unique properties.

To take advantage of modularization by file you could place the classes above in their own files, say, human.py

### Importing Parent Class
```python
# To import functions from other files use the following format
# from "filename-without-extension" import "function-or-class"

from human import Human
```
### Define Child Class
```python
# Specify the parent class(es) as parameters to the class definition
class Superhero(Human):

    # If the child class should inherit all of the parent's definitions without
    # any modifications, you can just use the "pass" keyword (and nothing else)
    # but in this case it is commented out to allow for a unique child class:
    # pass

    # Child classes can override their parents' attributes
    species = 'Superhuman'

    # Children automatically inherit their parent class's constructor including
    # its arguments, but can also define additional arguments or definitions
    # and override its methods such as the class constructor.
    # This constructor inherits the "name" argument from the "Human" class and
    # adds the "superpower" and "movie" arguments:
    def __init__(self, name, movie=False,
                 superpowers=["super strength", "bulletproofing"]):

        # add additional class attributes:
        self.fictional = True
        self.movie = movie
        # be aware of mutable default values, since defaults are shared
        self.superpowers = superpowers

        # The "super" function lets you access the parent class's methods
        # that are overridden by the child, in this case, the __init__ method.
        # This calls the parent class constructor:
        super().__init__(name)

    # override the sing method
    def sing(self):
        return 'Dun, dun, DUN!'

    # add an additional instance method
    def boast(self):
        for power in self.superpowers:
            print("I wield the power of {pow}!".format(pow=power))
```
### Create an Instance of the Child
```python
if __name__ == '__main__':
    sup = Superhero(name="Tick")

    # Instance type checks
    if isinstance(sup, Human):
        print('I am human')
    if type(sup) is Superhero:
        print('I am a superhero')

    # Get the "Method Resolution Order" used by both getattr() and super()
    # (the order in which classes are searched for an attribute or method)
    # This attribute is dynamic and can be updated
    print(Superhero.__mro__)    # => (<class '__main__.Superhero'>,
                                # => <class 'human.Human'>, <class 'object'>)

    # Calls parent method but uses its own class attribute
    print(sup.get_species())    # => Superhuman

    # Calls overridden method
    print(sup.sing())           # => Dun, dun, DUN!

    # Calls method from Human
    sup.say('Spoon')            # => Tick: Spoon

    # Call method that exists only in Superhero
    sup.boast()                 # => I wield the power of super strength!
                                # => I wield the power of bulletproofing!

    # Inherited class attribute
    sup.age = 31
    print(sup.age)              # => 31

    # Attribute that only exists within Superhero
    print('Am I Oscar eligible? ' + str(sup.movie))
```
## 6.2 Multiple Inheritance
### Another Parent Class
Let's assume we have another class called "Bat" which included in a module file called "bat.py"
```python
# Another class definition
# bat.py
class Bat:

    species = 'Baty'

    def __init__(self, can_fly=True):
        self.fly = can_fly

    # This class also has a say method
    def say(self, msg):
        msg = '... ... ...'
        return msg

    # And its own method as well
    def sonar(self):
        return '))) ... ((('

if __name__ == '__main__':
    b = Bat()
    print(b.say('hello'))
    print(b.fly)
```
### Child Class Inherit from multiple Parent Classes
```python

# And yet another class definition that inherits from Superhero and Bat
# superhero.py
from superhero import Superhero
from bat import Bat

# Define Batman as a child that inherits from both Superhero and Bat
class Batman(Superhero, Bat):

    def __init__(self, *args, **kwargs):
        # Typically to inherit attributes you have to call super:
        # super(Batman, self).__init__(*args, **kwargs)
        # However we are dealing with multiple inheritance here, and super()
        # only works with the next base class in the MRO list.
        # So instead we explicitly call __init__ for all ancestors.
        # The use of *args and **kwargs allows for a clean way to pass
        # arguments, with each parent "peeling a layer of the onion".
        Superhero.__init__(self, 'anonymous', movie=True,
                           superpowers=['Wealthy'], *args, **kwargs)
        Bat.__init__(self, *args, can_fly=False, **kwargs)
        # override the value for the name attribute
        self.name = 'Sad Affleck'

    def sing(self):
        return 'nan nan nan nan nan batman!'
```
### Create an Instance of the Child
```python
if __name__ == '__main__':
    sup = Batman()

    # The Method Resolution Order
    print(Batman.__mro__)       # => (<class '__main__.Batman'>,
                                # => <class 'superhero.Superhero'>,
                                # => <class 'human.Human'>,
                                # => <class 'bat.Bat'>, <class 'object'>)

    # Calls parent method but uses its own class attribute
    print(sup.get_species())    # => Superhuman

    # Calls overridden method
    print(sup.sing())           # => nan nan nan nan nan batman!

    # Calls method from Human, because inheritance order matters
    sup.say('I agree')          # => Sad Affleck: I agree

    # Call method that exists only in 2nd ancestor
    print(sup.sonar())          # => ))) ... (((

    # Inherited class attribute
    sup.age = 100
    print(sup.age)              # => 100

    # Inherited attribute from 2nd ancestor whose default value was overridden.
    print('Can I fly? ' + str(sup.fly)) # => Can I fly? False
```
## 7. Advanced
### Generator Functions - Yeild
The **yield** keyword in python is used in the contex of generator functions. It serves the purpose of creating iterators-functions that can be paused and resumed later, maintaining their state across multiple calls. The primary purpose of using **yield** is to produce a sequence of values while retaining the state of the function between calls.

#### Breakdown the purpose of using **yield**
|Purpose|Details|
|-|-|
Generators| Functions containing yield are known as generator functions. They generate a sequence of values lazily, one at a time, on-demand, rather than generating all values at once. This is beneficial when dealing with large datasets or infinite sequences because it saves memory by only computing the values as needed.
Stateful Iteration| When a generator function is called, it returns a generator object. When iterated upon (e.g., using a for loop or manually calling next() on the generator object), the function's execution starts. The function runs until it reaches a yield statement, at which point it pauses, and the yielded value is returned. The state of the function is maintained, allowing it to resume execution from the same point on the next iteration.
Efficient Memory Usage| Generators are memory-efficient because they don’t store all the generated values in memory at once. Instead, they produce values on-the-fly and retain local variables' state, allowing them to continue execution and yield the next value when asked.
Iterating through Large Sequences| Generators are particularly useful for iterating through large sequences of data, such as processing large files line by line or dealing with large numerical ranges. They allow processing elements one by one without storing the entire sequence in memory.
#### Code Example
```python
def my_generator():
    yield 1
    print("This will be printed in the second iterate next statemet")
    yield 2
    yield 3

# Using the generator
gen = my_generator()
print(next(gen))  # Outputs: 1
print(next(gen))  # Outputs: This will be printed in the second iterate next statemet 2
print(next(gen))  # Outputs: 3
# print(next(gen))  # Raises StopIteration error as all values have been yielded
```
### Generators
```python

# Generators help you make lazy code.
def double_numbers(iterable):
    for i in iterable:
        yield i + i

# Generators are memory-efficient because they only load the data needed to
# process the next value in the iterable. This allows them to perform
# operations on otherwise prohibitively large value ranges.
# NOTE: `range` replaces `xrange` in Python 3.
for i in double_numbers(range(1, 900000000)):  # `range` is a generator.
    print(i)
    if i >= 30:
        break
```
#### Diagrammatic
```python
double_numbers(range(1, 900000000)):
    +------------+
    |            |
    |            |
    |            |
    |            |
    |            |
    |            |
    |            |
    |            |
    |            |
    |   Generator Function (double_numbers)  |
    |            |
    |            |
    |            |
    |            |
    |            |
    |            |
    +------------+
           |
           |               i = 1
           V
     yield 1 + 1 = 2
           |
           |
           V
     Printing: 2
           |
           |
           V
           i = 2
           |
           V
     yield 2 + 2 = 4
           |
           |
           V
     Printing: 4
           |
           |
           V
           i = 3
           |
           V
     yield 3 + 3 = 6
           |
           |
           V
     Printing: 6
           |
           |
           V
           ...
           |
           |
           V
           i = 30
           |
           V
     yield 30 + 30 = 60
           |
           |
           V
     Printing: 60
           |
           |
           V
     Breaking the loop
```
### Decorators
Decorators are a form of syntactic sugar, They make code easier to read while accomplishing clunky syntax.

The term "syntactic sugar" refers to a feature in a programming language that doesn’t introduce new functionality but provides a more convenient or expressive way to use existing features.

#### Wrappers
```python
# Wrappers are one type of decorator.
# They're really useful for adding logging to existing functions without needing to modify them.

def log_function(func):
    def wrapper(*args, **kwargs):
        print("Entering function", func.__name__)
        result = func(*args, **kwargs)
        print("Exiting function", func.__name__)
        return result
    return wrapper

@log_function               # equivalent:
def my_function(x,y):       # def my_function(x,y):
    return x+y              #   return x+y
                            # my_function = log_function(my_function)
# The decorator @log_function tells us as we begin reading the function definition
# for my_function that this function will be wrapped with log_function.
# When function definitions are long, it can be hard to parse the non-decorated
# assignment at the end of the definition.

my_function(1,2) # => "Entering function my_function"
                 # => "3"
                 # => "Exiting function my_function"
```
#### Problem of this Method
```python
# But there's a problem.
# What happens if we try to get some information about my_function?

print(my_function.__name__) # => 'wrapper'
print(my_function.__code__.co_argcount) # => 0. The argcount is 0 because both arguments in wrapper()'s signature are optional.
```
#### Solution using **wraps**
```python
# Because our decorator is equivalent to my_function = log_function(my_function)
# we've replaced information about my_function with information from wrapper

# Fix this using functools

from functools import wraps

def log_function(func):
    @wraps(func) # this ensures docstring, function name, arguments list, etc. are all copied
                 # to the wrapped function - instead of being replaced with wrapper's info
    def wrapper(*args, **kwargs):
        print("Entering function", func.__name__)
        result = func(*args, **kwargs)
        print("Exiting function", func.__name__)
        return result
    return wrapper

@log_function               
def my_function(x,y):       
    return x+y              

my_function(1,2) # => "Entering function my_function"
                 # => "3"
                 # => "Exiting function my_function"

print(my_function.__name__) # => 'my_function'
print(my_function.__code__.co_argcount) # => 2
```

# References
- Learnxinyminutes - Python: [link](https://learnxinyminutes.com/docs/python/)
- PythonSpot: [link](https://pythonspot.com/)
- CodeAcademy - Learn Python: [link](https://www.codecademy.com/learn/learn-python-3)
- Google For Education - Google's Python Class: [link](https://developers.google.com/edu/python?hl=en)

