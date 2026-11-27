import math


def estimate_tokens(text: str) -> int:
    if not text:
        return 0

    return math.ceil(len(text) / 4)