"""Derive an argparse parser from a function's type hints.

Tuned for the Gemini Enterprise Agent Platform: every parameter becomes a
``--flag`` with underscores preserved (``--learning_rate``), and custom
parameter types are built from their string value via argparse's normal
``type=`` mechanism.
"""

import argparse
import dataclasses
import inspect
import json
import types
from typing import Any, Callable, Literal, Union, get_args, get_origin, get_type_hints

__all__ = ["arg", "parser", "run", "to_argv"]


class _BooleanOptionalAction(argparse.Action):
    """Like ``argparse.BooleanOptionalAction`` but negates with ``--no_`` (not ``--no-``)."""

    def __init__(self, option_strings, dest, default=None, required=False, help=None):
        strings = []
        for opt in option_strings:
            strings.append(opt)
            if opt.startswith("--"):
                strings.append("--no_" + opt[2:])
        super().__init__(strings, dest, nargs=0, default=default, required=required, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        if option_string is not None and option_string in self.option_strings:
            setattr(namespace, self.dest, not option_string.startswith("--no_"))

    def format_usage(self):
        return " | ".join(self.option_strings)


def arg(*, type_init: dict[type, Callable[[str], Any]] | None = None):
    """Attach per-type string converters to a function.

    ``type_init`` maps a parameter type to a ``Callable[[str], T]`` that is
    passed straight to argparse as ``type=``. It overrides the default
    converter (the type itself) for that type.

    Example::

        @arg(type_init={Path: Path})
        def main(out_dir: Path): ...
    """

    def decorate(func):
        func.__vire_gap_type_init__ = type_init or {}
        return func

    return decorate


def _unwrap_optional(hint) -> tuple[Any, bool]:
    """Return ``(inner, is_optional)``; strips a single ``None`` from a Union."""
    origin = get_origin(hint)
    if origin is Union or origin is getattr(types, "UnionType", None):
        args = [a for a in get_args(hint) if a is not type(None)]
        is_optional = len(args) != len(get_args(hint))
        if len(args) == 1:
            return args[0], is_optional
        raise TypeError(
            f"unsupported union of multiple types: {hint}; only Optional[T] / T | None is supported"
        )
    return hint, False


def _converter_for(tp, type_init: dict[type, Callable[[str], Any]]) -> Callable[[str], Any]:
    """The callable argparse uses as ``type=`` for a scalar (non-list) type."""
    if tp in type_init:
        return type_init[tp]
    return tp


def _param_to_add_argument(
    param: inspect.Parameter,
    hint: Any,
    type_init: dict[type, Callable[[str], Any]],
) -> tuple[list[str], dict[str, Any]]:
    """Map one parameter to ``(["--name"], add_argument_kwargs)``."""
    if hint is inspect.Parameter.empty:
        raise TypeError(f"parameter '{param.name}' has no type annotation; argument derivation is type-driven")

    has_default = param.default is not inspect.Parameter.empty
    inner, is_optional = _unwrap_optional(hint)
    kwargs: dict[str, Any] = {}

    if inner is bool:
        kwargs["action"] = _BooleanOptionalAction
    elif get_origin(inner) is Literal:
        choices = get_args(inner)
        kwargs["choices"] = list(choices)
        kwargs["type"] = _converter_for(type(choices[0]), type_init)
    elif get_origin(inner) is list:
        item_args = get_args(inner)
        kwargs["nargs"] = "*"
        if item_args:
            kwargs["type"] = _converter_for(item_args[0], type_init)
    else:
        kwargs["type"] = _converter_for(inner, type_init)

    if has_default:
        kwargs["default"] = param.default
    elif is_optional:
        kwargs["default"] = None
    else:
        kwargs["required"] = True

    return [f"--{param.name}"], kwargs


def parser(func: Callable) -> argparse.ArgumentParser:
    """Build an :class:`argparse.ArgumentParser` from ``func``'s signature."""
    type_init = getattr(func, "__vire_gap_type_init__", {})
    signature = inspect.signature(func)
    hints = get_type_hints(func)

    p = argparse.ArgumentParser(description=inspect.getdoc(func))
    for param in signature.parameters.values():
        names, kwargs = _param_to_add_argument(
            param, hints.get(param.name, inspect.Parameter.empty), type_init
        )
        p.add_argument(*names, **kwargs)
    return p


def run(func: Callable, argv: list[str] | None = None) -> Any:
    """Parse ``argv`` (default ``sys.argv``) and call ``func`` with the result."""
    namespace = parser(func).parse_args(argv)
    return func(**vars(namespace))


def to_argv(instance: Any, exclude: set[str] | None = None) -> list[str]:
    """Render a dataclass instance or mapping as an argv list.

    Bools use the ``--name`` (True) / ``--no_name`` (False) convention, matching
    the parser; ``dict``/``list`` values are JSON-encoded. ``exclude`` skips
    fields by name.
    """
    exclude = exclude or set()

    if dataclasses.is_dataclass(instance) and not isinstance(instance, type):
        items = [(f.name, getattr(instance, f.name)) for f in dataclasses.fields(instance)]
    else:
        mapping: Any = instance
        items = list(mapping.items())

    argv: list[str] = []
    for name, value in items:
        if name in exclude:
            continue
        flag = f"--{name}"
        if isinstance(value, bool):
            argv.append(flag if value else f"--no_{name}")
        elif isinstance(value, (dict, list)):
            argv += [flag, json.dumps(value)]
        else:
            argv += [flag, str(value)]

    return argv
