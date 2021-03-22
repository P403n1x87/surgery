from pprint import pprint as print
from inspect import currentframe


def hook(ident):
    print(f"Breakpoint {ident} has been hit!")
    print(currentframe().f_back.f_locals)
