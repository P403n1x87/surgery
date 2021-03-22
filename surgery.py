from bytecode import Instr, Bytecode
from types import FunctionType
from typing import List, Tuple


def _hook_bytecode(hook, lineno, ident):
    """The hook receives a breakpoint identifier.

    This is the equivalent of ``hook(ident)``.
    """
    return Bytecode(
        [
            Instr("LOAD_GLOBAL", hook.__name__, lineno=lineno),
            Instr("LOAD_CONST", ident, lineno=lineno),
            Instr("CALL_FUNCTION", 1, lineno=lineno),
            Instr("POP_TOP", lineno=lineno),
        ]
    )


def _inject_hook(code: Bytecode, h: FunctionType, line: int, ident: int) -> Bytecode:
    for i, instr in enumerate(code):
        try:
            if instr.lineno == line:
                # gotcha!
                break
        except AttributeError:
            # pseudo-instruction (e.g. label)
            pass
    else:
        raise RuntimeError("Invalid line number. It either is empty or is a comment.")

    # actual injection
    code[i:i] = _hook_bytecode(h, line, ident)


def inject_hooks(
    f: FunctionType, hs: List[Tuple[FunctionType, int, int]]
) -> FunctionType:
    f_code = f.__code__
    abstract_code = Bytecode.from_code(f_code)

    # sanity check
    assert len(abstract_code)

    lo, hi = abstract_code[0].lineno, abstract_code[-1].lineno
    for line in [_[1] for _ in hs]:
        if not (lo <= line <= hi):
            raise RuntimeError(
                f"Line out of bounds for '{f.__qualname__}'. Valid range is [{lo}-{hi}]"
            )

    for h, line, ident in hs:
        _inject_hook(abstract_code, h, line, ident)

    return FunctionType(
        abstract_code.to_code(),
        f.__globals__,
        f.__name__,
        f.__defaults__,
        f.__closure__,
    )


def inject_hook(
    f: FunctionType, h: FunctionType, line: int, ident: int
) -> FunctionType:
    return inject_hooks(f, [(h, line, ident)])


def inject(hook: FunctionType, line: int) -> FunctionType:
    """decorator."""

    def wrapper(f: FunctionType):
        return inject_hook(f, hook, line, 0)

    return wrapper
