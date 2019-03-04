import functools

def unpack(func):
    @functools.wraps(func)
    def func_inner(args):
        return func(*args)
    return func_inner

def choice(question, default="yes"):
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        print(question + prompt)
        value = input().lower()
        if default is not None and value == '':
            return valid[default]
        if value in valid:
            return valid[value]
        print("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")
