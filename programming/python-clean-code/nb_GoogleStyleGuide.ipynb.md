# nb_GoogleStyleGuide.ipynb

<div class="code-file">

Notebook from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/programming/python-clean-code/nb_GoogleStyleGuide.ipynb)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/programming/python-clean-code/nb_GoogleStyleGuide.ipynb)  ·  [Open in Colab](https://colab.research.google.com/github/AhmedYousriSobhi/aCupOfTea/blob/main/programming/python-clean-code/nb_GoogleStyleGuide.ipynb)

</div>


# Python Google Style Guide
Author: Ahmed Sobhi

Department: Data Science

Created_at: 2023-07-06

Objective: Python clean code using Google Style guide.

## Lint
- pylint is a tool for finding bugs and style problems in Python source code. It finds problems that are typically caught by a compiler for less dynamic languages like C and C++. Because of the dynamic nature of Python, some warnings may be incorrect; however, spurious warnings should be fairly infrequent.

```python
# Installing pylint
!pip install -q pylint
```

```python
import pylint
```

The pylint package is used with python script files, so it will not work inside a jupyter notebook.

So Instead we will use: __pycodestyle__

## pycodestyle

Alternative to pylint, but will capability to work inside Jupyter notebook

```python
! pip install -q pycodestyle pycodestyle_magic
# Another required libarary to make pycodestyle work.
! pip install -q flake8
```

```python
# Loading the magic into our notebook
%load_ext pycodestyle_magic
```

You will have you use __%%pycodestyle__ everytime before the code you want to check sytle for.

```python
%%pycodestyle
a=1
```

```output
2:2: E225 missing whitespace around operator
3:1: W391 blank line at end of file
```

```python
%%pycodestyle
a = 1
```

```output
3:1: W391 blank line at end of file
```

```python
%%pycodestyle
dict = 'something'
```

```output
3:1: W391 blank line at end of file
```

```python
%%pycodestyle
def viking_cafe_order(spam, beans, eggs=None):
    del beans, eggs  # Unused by vikings.
    return spam + spam + spam


viking_cafe_order(10, 20, 30)
```

```output
8:1: W391 blank line at end of file
```

The different here between pylint and pycodestyle, is that, there will be a warning for the unused variable inside the function, so to suppressed it by using a del fucntion to remove unused variables.

Always try to add comment explaining you reason for deleting variables.
