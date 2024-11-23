from string import ascii_lowercase
from re import sub as resub


def normalizeName(name):
    return "".join([i for i in name.lower() if i in ascii_lowercase])


def titleEnumName(name):
    return resub(
        r"( [iI]+)$", lambda x: x.group(0).upper(), name.replace("_", " ").title()
    )
