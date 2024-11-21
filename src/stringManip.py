from string import ascii_lowercase


def normalizeName(name):
    return "".join([i for i in name.lower() if i in ascii_lowercase])


def titleEnumName(name):
    return name.replace("_", " ").title()
