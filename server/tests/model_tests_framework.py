from db import get_image_paths, get_prompt


def test():
    for selection in [
        "ALL",
        "PERFECT",
        "SLIGHTLY_BLURRED",
        "FLASH_VISIBLE",
        "VERY_BLURRED",
        "CUT_OFF",
    ]:
        images = get_image_paths(selection)
