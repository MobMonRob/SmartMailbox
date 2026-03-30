import sys

from .model_tests_framework import run_tests
from .logger import logger

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
    logger.info("START")
    model = sys.argv[1]

    if len(sys.argv) == 3:
        tests = parse_test_range(sys.argv[2])
        run_tests(model,tests)
    else:
        run_tests(model)




if __name__ == "__main__":
    main()
