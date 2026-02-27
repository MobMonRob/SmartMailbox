import sys

from .model_tests_framework import run_tests
import logging
logging.basicConfig(level=logging.DEBUG)

def main():
    """
    Run a model test for a specified model.
    The model gets specified via the first cmd line argument.

    **Example**: python -m tests.model.main llama4
    """
    model = sys.argv[1]

    print(model)
    run_tests(model)


if __name__ == "__main__":
    main()
