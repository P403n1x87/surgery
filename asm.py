from dis import dis as d, opmap as O
from hook import hook
from types import CodeType, FunctionType


def add(a, b):
    s = 0
    s += a
    s += b
    return s


def dadd(a, b):
    s = 0
    s += a
    hook(locals())
    s += b
    return s


def bc(code):
    for i, b in enumerate(code.__code__.co_code):
        print(f"{i:4} |  {b}")


print(add.__code__.co_names)
bc(add)
d(add)
print("=" * 80)
print(dadd.__code__.co_names)
bc(dadd)
d(dadd)


def surgery():
    add_code = add.__code__

    n_old_names = len(add_code.co_names)
    LDG = O["LOAD_GLOBAL"]
    CALL = O["CALL_FUNCTION"]
    POPT = O["POP_TOP"]
    injection = bytes(
        [LDG, n_old_names, LDG, n_old_names + 1, CALL, 0, CALL, 1, POPT, 0]
    )
    new_bytecode = add_code.co_code[0:12] + injection + add_code.co_code[12:]
    old_lnotab = add_code.co_lnotab
    new_lnotab = (
        old_lnotab[: 3 << 1]
        + bytes([old_lnotab[3 << 1] + len(injection), old_lnotab[(3 << 1) + 1]])
        + old_lnotab[4 << 1 :]
    )
    print(list(add_code.co_lnotab))
    print(list(dadd.__code__.co_lnotab))
    print(list(new_lnotab))
    return CodeType(
        add_code.co_argcount,
        add_code.co_posonlyargcount,
        add_code.co_kwonlyargcount,
        add_code.co_nlocals,
        max(2, add_code.co_stacksize),
        add_code.co_flags,
        new_bytecode,
        add_code.co_consts,
        add_code.co_names + ("hook", "locals"),
        add_code.co_varnames,
        add_code.co_filename,
        add_code.co_name,
        add_code.co_firstlineno,
        new_lnotab,  
        add_code.co_freevars,
        add_code.co_cellvars,
    )


print("Original function name:", add.__name__)
print("Performing surgery")
add = FunctionType(
    surgery(), add.__globals__, "sadd", add.__defaults__, add.__closure__
)
print("New function name:", add.__name__)
bc(add)
d(add)

print(add(1, 3))
