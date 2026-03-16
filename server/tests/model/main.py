import sys
import os
from .model_tests_framework import run_tests
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(current_dir, 'model_tests.log')

logger = logging.getLogger() # Root Logger
logger.setLevel(logging.INFO)

# Clear existing handlers to prevent duplicates if main is called multiple times
if logger.hasHandlers():
    logger.handlers.clear()

formatter = logging.Formatter("%(asctime)s | %(name)33s | %(levelname)8s | %(message)s")

# File Handler
file_handler = logging.FileHandler(log_path)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def main():
    """
    Run a model test for a specified model.
    The model gets specified via the first cmd line argument.

    **Example**: python -m tests.model.main llama4
    """
    model = sys.argv[1]

    run_tests(model)


if __name__ == "__main__":
    main()
