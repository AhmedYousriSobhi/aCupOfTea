# 101_python_nb.ipynb

<div class="code-file">

Notebook from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/programming/python/101_python_nb.ipynb)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/programming/python/101_python_nb.ipynb)  ·  [Open in Colab](https://colab.research.google.com/github/AhmedYousriSobhi/aCupOfTea/blob/main/programming/python/101_python_nb.ipynb)

</div>


```python
7%-3
```

```output
-2
```

```python
bool(-5)
```

```output
True
```

```python
# Note that a tuple of length one has to have a comma after the last element but
# tuples of other lengths, even zero, do not.
print(type((1)))   # => <class 'int'>
print(type((1,)))  # => <class 'tuple'>
print(type(()))    # => <class 'tuple'>
```

```output
<class 'int'>
<class 'tuple'>
<class 'tuple'>
```

## Dictionaries

```python
d = {(1,2,3):[4,5,6]}
```

```python
d
```

```output
{(1, 2, 3): [4, 5, 6]}
```

```python
d[(1,2,3)]
```

```output
[4, 5, 6]
```

```python
filled_dict = {"one": 1, "two": 2, "three": 3}
print(list(filled_dict.keys()))
```

```output
['one', 'two', 'three']
```

```python
{'a': 1, **{'b': 2}}
```

```output
{'a': 1, 'b': 2}
```

```python
{'a': 1, **{'a': 2}}
```

```output
{'a': 2}
```

### Copy

```python
b = {(1, 2, 3): [4, 5, 6]}
d == b, d is b
```

```output
(True, False)
```

```python
# Deep Copy
import copy
c = copy.deepcopy(d)
d==c, d is c
```

```output
(True, False)
```

## Sets

```python
{(1,), 1}
```

```output
{(1,), 1}
```

```python
{(1,), 1}[0]
```

```output
<>:1: SyntaxWarning: 'set' object is not subscriptable; perhaps you missed a comma?
<>:1: SyntaxWarning: 'set' object is not subscriptable; perhaps you missed a comma?
/tmp/ipykernel_10799/3294254955.py:1: SyntaxWarning: 'set' object is not subscriptable; perhaps you missed a comma?
  {(1,), 1}[0]
/tmp/ipykernel_10799/3294254955.py:1: SyntaxWarning: 'set' object is not subscriptable; perhaps you missed a comma?
  {(1,), 1}[0]
/tmp/ipykernel_10799/3294254955.py:1: SyntaxWarning: 'set' object is not subscriptable; perhaps you missed a comma?
  {(1,), 1}[0]
/tmp/ipykernel_10799/3294254955.py:1: SyntaxWarning: 'set' object is not subscriptable; perhaps you missed a comma?
  {(1,), 1}[0]
/tmp/ipykernel_10799/3294254955.py:1: SyntaxWarning: 'set' object is not subscriptable; perhaps you missed a comma?
  {(1,), 1}[0]
```

```output
---------------------------------------------------------------------------
TypeError                                 Traceback (most recent call last)
Cell In[20], line 1
----> 1 {(1,), 1}[0]

TypeError: 'set' object is not subscriptable
```

## Handle Exceptions

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

```output
We can clean up resources here
```

## Iteratable

```python
filled_dict = {"one": 1, "two": 2, "three": 3}
our_iterable = filled_dict.keys()
print(our_iterable)
```

```output
dict_keys(['one', 'two', 'three'])
```

```python
our_iterable[0]
```

```output
---------------------------------------------------------------------------
TypeError                                 Traceback (most recent call last)
Cell In[27], line 1
----> 1 our_iterable[0]

TypeError: 'dict_keys' object is not subscriptable
```

```python
# Iterator
iterator = iter(our_iterable)
iterator
```

```output
<dict_keyiterator at 0x7ff614199bc0>
```

```python
iterator[0]
```

```output
---------------------------------------------------------------------------
TypeError                                 Traceback (most recent call last)
Cell In[29], line 1
----> 1 iterator[0]

TypeError: 'dict_keyiterator' object is not subscriptable
```

```python
next(iterator)
```

```output
'one'
```

```python
list(iterator)
```

```output
['two', 'three']
```

```python
list(our_iterable)
```

```output
['one', 'two', 'three']
```

## Functions

```python
def varargs(*args):
    return args

varargs(1, 2, 3)  # => (1, 2, 3)
```

```output
(1, 2, 3)
```

```python
def keyword_args(**kwargs):
    return kwargs

keyword_args(n=1, m=3)
```

```output
{'n': 1, 'm': 3}
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

```output
13
```

### Closure

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
print(avg(3)) # => 3.0
print(avg(5)) # (3+5)/2 => 4.0
print(avg(7)) # (8+7)/3 => 5.0
```

```output
3.0
4.0
5.0
```

The nonlocal keyword in Python is used within nested functions to modify variables that are defined in the nearest enclosing scope, excluding the global scope

```python
# Closures in nested functions:
# We can use the nonlocal keyword to work with variables in nested scope which shouldn't be declared in the inner functions.
def create_avg():
    total = 0
    count = 0
    def avg(n):
        total, count
        total += n
        count += 1
        return total/count
    return avg
avg = create_avg()
print(avg(3)) # => 3.0
print(avg(5)) # (3+5)/2 => 4.0
print(avg(7)) # (8+7)/3 => 5.0
```

```output
---------------------------------------------------------------------------
UnboundLocalError                         Traceback (most recent call last)
Cell In[38], line 13
     11     return avg
     12 avg = create_avg()
---> 13 print(avg(3)) # => 3.0
     14 print(avg(5)) # (3+5)/2 => 4.0
     15 print(avg(7))

Cell In[38], line 7, in create_avg.<locals>.avg(n)
      6 def avg(n):
----> 7     total, count
      8     total += n
      9     count += 1

UnboundLocalError: cannot access local variable 'total' where it is not associated with a value
```

### built-in higher order functions

```python
list(map(max, [1, 2, 3], [4, 2, 5]))
```

```output
[4, 2, 5]
```

```python
list(filter(lambda x: x > 5, [3, 4, 5, 6, 7]))
```

```output
[<function __main__.<lambda>(x)>, [3, 4, 5, 6, 7]]
```

## Modules

```python
import math

dir(math)
```

```output
['__doc__',
 '__file__',
 '__loader__',
 '__name__',
 '__package__',
 '__spec__',
 'acos',
 'acosh',
 'asin',
 'asinh',
 'atan',
 'atan2',
 'atanh',
 'cbrt',
 'ceil',
 'comb',
 'copysign',
 'cos',
 'cosh',
 'degrees',
 'dist',
 'e',
 'erf',
 'erfc',
 'exp',
 'exp2',
 'expm1',
 'fabs',
 'factorial',
 'floor',
 'fmod',
 'frexp',
 'fsum',
 'gamma',
 'gcd',
 'hypot',
 'inf',
 'isclose',
 'isfinite',
 'isinf',
 'isnan',
 'isqrt',
 'lcm',
 'ldexp',
 'lgamma',
 'log',
 'log10',
 'log1p',
 'log2',
 'modf',
 'nan',
 'nextafter',
 'perm',
 'pi',
 'pow',
 'prod',
 'radians',
 'remainder',
 'sin',
 'sinh',
... 6 more lines (the full output is in the notebook on GitHub)
```

## Classes

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
    # i.age
```

```output
Ian: hi
Joel: hello
Ian: H. sapiens
Ian: H. neanderthalensis
Joel: H. neanderthalensis
*grunt*
*grunt*
Ian: 42
Joel: 0
```

```python
i.age
```

```output
---------------------------------------------------------------------------
AttributeError                            Traceback (most recent call last)
Cell In[54], line 1
----> 1 i.age

Cell In[52], line 46, in Human.age(self)
     44 @property
     45 def age(self):
---> 46     return self._age

AttributeError: 'Human' object has no attribute '_age'
```

```python
j.age
```

```output
0
```

```python
Human.age
```

```output
<property at 0x7ff5f73140e0>
```

```python
Human.name
```

```output
---------------------------------------------------------------------------
AttributeError                            Traceback (most recent call last)
Cell In[61], line 1
----> 1 Human.name

AttributeError: type object 'Human' has no attribute 'name'
```

## Inheritance

```python
#from human import Human


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

```output
I am human
I am a superhero
(<class '__main__.Superhero'>, <class '__main__.Human'>, <class 'object'>)
Superhuman
Dun, dun, DUN!
Tick: Spoon
I wield the power of super strength!
I wield the power of bulletproofing!
31
Am I Oscar eligible? False
```

## 7. Advanced

```python
def double_numbers(iterable):
    for i in iterable:
        yield i + i

for i in double_numbers(range(1, 9000000000)):
    print(i)
    if i >= 30:
        break
```

```output
2
4
6
8
10
12
14
16
18
20
22
24
26
28
30
```

```python
def my_generator():
    yield 1
    yield 2
    yield 3

# Using the generator
gen = my_generator()
print(next(gen))  # Outputs: 1
print(next(gen))  # Outputs: 2
print(next(gen))  # Outputs: 3
```

```output
1
2
3
```

```python
next(my_generator())
```

```output
1
```

```python
def my_generator():
    yield 1
    print("This will be printed in the second iterate next statemet")
    yield 2
    yield 3

# Using the generator
gen = my_generator()
print(next(gen))  # Outputs: 1
print(next(gen))  # Outputs: 2
print(next(gen))  # Outputs: 3
```

```output
1
This will be printed in the second iterate next statemet
2
3
```

## Wrapper

```python
def log_function(func):
    def wrapper(*args, **kwargs):
        print("Entering functions ", func.__name__)
        results= func(*args, **kwargs)
        print("Exutubg function ", func.__name__)
        return results
    return wrapper

@log_function
def my_function(x,y):
    return x+y
```

```python
my_function(1,2)
```

```output
Entering functions  my_function
Exutubg function  my_function
```

```output
3
```

```python
my_function.__name__, my_function.__code__.co_argcount
```

```output
('wrapper', 0)
```

```python
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

```output
Entering function my_function
Exiting function my_function
my_function
0
```
