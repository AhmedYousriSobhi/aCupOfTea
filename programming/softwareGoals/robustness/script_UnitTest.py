"""
    This script is used to illustrate how to use pyUnit libarary to run unit test on certain code.

    Documentaion: https://docs.python.org/3/library/unittest.html
    
    external sources: https://machinelearningmastery.com/a-gentle-introduction-to-unit-testing-in-python/

    To run Command-Line Interface:
    
    ```python
        python -m unittest script_UnitTest.py
    ```
"""

from script_RectangleClass import *

import unittest

class TestGetAreaRectangle(unittest.TestCase):
    """
        This class is used to define certain tests related to the subject class 'Rectangle' we want to test.
    """

    def test_normal_case(self):
        rectangle = Rectangle(2, 3)
        self.assertEqual(rectangle.get_area(), 6, "incorrect area")

    def test_negative_case(self): 
        """expect -1 as output to denote error when looking at negative area"""
        rectangle = Rectangle(-1, 2)
        self.assertEqual(rectangle.get_area(), -1, "incorrect negative output")


class TestGetAreaRectangleWithSetUp(unittest.TestCase):
    """
        This class is used to define certain tests related to the subject class 'Rectangle' we want to test.

        But here we define setUpClass with decorator classmethod, 
        To make sure the run per TestCase instead of Once per test run.
    """

    @classmethod
    def setUpClass(self):
        """
            We define setup method, as what is we had some code that we needed to run to set up before running each test.
        """

        # Create an instance of rectangle class
        self.rectangle = Rectangle(0, 0)

    def test_normal_case(self):
        """
            # To checks if the rectangle.get_area() method returns the correct area for a rectangle with width = 2 and length = 3. 
        """

        self.rectangle.set_width(2)
        self.rectangle.set_height(3)

        # We use self.assertEqual instead of simply using assert to allow the unittest library to allow the runner to accumulate all test cases and produce a report.
        self.assertEqual(self.rectangle.get_area(), 6, 'incorrect area')

    def test_negative_case(self):
        """
            Expect -1 as output to denote error when looking at negative area
        """

        self.rectangle.set_width(-1)
        self.rectangle.set_height(2)

        self.assertEqual(self.rectangle.get_area(), -1, 'incorrect negative output')

    def test_assert_raises(self):
        """
            Using assertRaise to detect if an expected error is raised when running a particular block of code.
        """
        
        with self.assertRaises(ZeroDivisionError):
            a = 1 / 0

if __name__ == '__main__':
    # Call unittest.main() to run the unit test.
    # This will test all the tests inside this script.
    # unittest.main()

    # Another Case, if we need to select certain Test.
    """
        To help us organize tests and select which set of tests we want to run,
        we can aggregate test cases into test suites which help to group tests that should executed together into a single object
    """
    # loads all unit tests from TestGetAreaRectangle into a test suite
    calculate_area_suite = unittest.TestLoader() \
                       .loadTestsFromTestCase(TestGetAreaRectangleWithSetUp)
    
    # User unittest.TextTestRunner class to allow us to run specific test suits.
    runner = unittest.TextTestRunner()

    # Run the tests
    runner.run(calculate_area_suite)
