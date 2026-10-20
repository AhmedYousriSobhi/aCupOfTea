# nb_Robustness.ipynb

<div class="code-file">

Notebook from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/programming/software-goals/robustness/nb_Robustness.ipynb)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/programming/software-goals/robustness/nb_Robustness.ipynb)  ·  [Open in Colab](https://colab.research.google.com/github/AhmedYousriSobhi/aCupOfTea/blob/main/programming/software-goals/robustness/nb_Robustness.ipynb)

</div>


Author of this notebook: [Ahmed Sobhi](ahmedyousrisobhi@gmail.com)

Creation Date: 2023-07-09

Objective: Illusterate robust Python programming Techniques.

Sources: [WEB AGE SOLUTION](https://www.webagesolutions.com/blog/robust-python-programming-techniques)

# Robustness
## Definition:
 - Something to be robust means that is capable of handling unexpected inputs that are not explicitly defined for its application.
  - Example: if a prgram is expecting a positive integer (price of item), and instead is given a negative integer, then the program should be able to recover gracefully from this error.
  - Real-life critical applications, where a software error can lead to injury of loss of life. This point was driven home in late 1980s in accidents involving __Therac-25__, a radiation-therapy machine, which severely overdosed six patients between 1985 & 1987, some of whom died from complications resulting from their radiation overdose.

## Assertions
- It is a mechanism that helps software developers write a more robust code.
- They are part and parcel of the __Defensive Programming__ philosopy.
- Assertions are boolean expressions that ensure that a specific (often critical) assumption about the program’s state is not violated Program execution proceeds if the assertion evaluates to True (the program is in normal state); an exception with a supplied error message is raised otherwise.
- Assertions are usually used to validate input parameters passed to a function, an object method, or to verify some fundamental business conditions.

### Assertions in Python

```python
assert <context-specific boolean expressions>, <error message>
```

```python
def valid_age(age: int = 10)->bool:
    """
        Used to check if the user age is +16 to be valid or not.

        Input:
            age: integer, input user age.
        
        output:
            boolean value, indicate whether input age is valid or not
    """

    # We have to make sure the user input age is not negative.
    assert age > 0, 'Age must be a positive number over 0'

    return_val = False

    if age > 16:
        return_val = True

    return return_val
```

```python
age = 5
valid_age(age)
```

```output
False
```

```python
age = 50
valid_age(age)
```

```output
True
```

```python
age = -5
valid_age(age)
```

```output
---------------------------------------------------------------------------
AssertionError                            Traceback (most recent call last)
/tmp/ipykernel_48842/343721057.py in <module>
      1 age = -5
----> 2 valid_age(age)

/tmp/ipykernel_48842/3080515404.py in valid_age(age)
     11 
     12     # We have to make sure the user input age is not negative.
---> 13     assert age > 0, 'Age must be a positive number over 0'
     14 
     15     return_val = False

AssertionError: Age must be a positive number over 0
```
