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

def parse_test_range(tests_input: str) -> set[int]:
    tests = set()
    for s in tests_input.split(","):
        if s.startswith("-"):
            end = int(s.removeprefix("-"))
            for i in range(0, end+1):
                tests.add(i)
        elif s.endswith("-"):
            start = int(s.removesuffix("-"))
            for i in range(start, 451):
                tests.add(i)
        elif s.find("-") != -1:
            start, end = s.split("-")
            for i in range(int(start), int(end)+1):
                tests.add(i)
        else:
            tests.add(int(s))

    return tests


def main():
    """
    Run a model test for a specified model.
    The model gets specified via the first cmd line argument.

    **Example**: python -m tests.model.main llama4

    Range:
    1,6,8
    -45
    69-
    34-65
    1,69-
    """
    model = sys.argv[1]

    if len(sys.argv) == 3:
        tests = parse_test_range(sys.argv[2])
        run_tests(model,tests)
    else:
        run_tests(model)




if __name__ == "__main__":
    main()
