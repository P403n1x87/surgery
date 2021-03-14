from dis import opmap
from types import CodeType, FunctionType

HOOK_STACKSIZE = 2


def hook_bytes(names_offset):
    """The hook will receive the dictionary of locals."""
    LOAD_GLOBAL = opmap["LOAD_GLOBAL"]
    CALL_FUNCTION = opmap["CALL_FUNCTION"]
    POP_TOP = opmap["POP_TOP"]
    return bytes(
        [
            LOAD_GLOBAL,
            names_offset,
            LOAD_GLOBAL,
            names_offset + 1,
            CALL_FUNCTION,
            0,
            CALL_FUNCTION,
            1,
            POP_TOP,
            0,
        ]
    )


def offset_from_line(line, firstlineno, lnotab):
    """Find the bytecode offset for the given line."""
    # TODO: Handle negetive offsets!
    n = len(lnotab)
    assert n & 1 == 0

    l = firstlineno
    tab = lnotab
    offset = 0
    index = 0
    while tab:
        index += 1
        b, d, *tab = tab
        l += d
        offset += b
        if l >= line:
            return offset, index
    raise IndexError("Line out of bound")


def inject_hook(f: FunctionType, h: FunctionType, line: int) -> FunctionType:
    f_code = f.__code__

    # We are adding two global names to the existing ones
    names_offset = len(f_code.co_names)
    new_names = f_code.co_names + (h.__name__, "locals")

    # Inject the hook at the given line
    offset, index = offset_from_line(line, f_code.co_firstlineno, f_code.co_lnotab)
    hook = hook_bytes(names_offset)
    new_bytecode = f_code.co_code[:offset] + hook + f_code.co_code[offset:]

    # Make it look like we "inlined" the hook
    new_lnotab = (
        f_code.co_lnotab[: index << 1]
        + bytes(
            [
                f_code.co_lnotab[index << 1] + len(hook),
                f_code.co_lnotab[(index << 1) + 1],
            ]
        )
        + f_code.co_lnotab[(index + 1) << 1 :]
    )  # FIXME: Index out of range

    return FunctionType(
        CodeType(
            f_code.co_argcount,
            f_code.co_posonlyargcount,
            f_code.co_kwonlyargcount,
            f_code.co_nlocals,
            max(HOOK_STACKSIZE, f_code.co_stacksize),
            f_code.co_flags,
            new_bytecode,
            f_code.co_consts,
            new_names,
            f_code.co_varnames,
            f_code.co_filename,
            f_code.co_name,
            f_code.co_firstlineno,
            new_lnotab,
            f_code.co_freevars,
            f_code.co_cellvars,
        ),
        f.__globals__,
        f.__name__,
        f.__defaults__,
        f.__closure__,
    )


def inject(hook: FunctionType, line: int) -> FunctionType:
    """decorator."""

    def wrapper(f: FunctionType):
        return inject_hook(f, hook, line)

    return wrapper
