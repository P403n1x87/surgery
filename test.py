from hook import hook
from surgery import inject


@inject(hook, line=10)
def add(a, b):
    s = 0
    for i in range(10):
        s = 0
    s += a
    s += b
    return s


print(add(10, 1))
