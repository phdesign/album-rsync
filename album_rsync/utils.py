import functools

def unpack(func):
    @functools.wraps(func)
    def func_inner(args):
        return func(*args)
    return func_inner
