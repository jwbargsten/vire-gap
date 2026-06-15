from dataclasses import dataclass

import pytest

from vire_gap import args


def test_basic_types_coerce():
    def main(learning_rate: float, epochs: int, name: str): ...

    ns = args.parser(main).parse_args(["--learning_rate", "0.01", "--epochs", "10", "--name", "run-a"])
    assert ns.learning_rate == 0.01
    assert ns.epochs == 10
    assert ns.name == "run-a"


def test_underscores_preserved_in_flags():
    def main(learning_rate: float): ...

    with pytest.raises(SystemExit):
        # hyphenated form must NOT be accepted
        args.parser(main).parse_args(["--learning-rate", "0.01"])


def test_missing_required_errors():
    def main(epochs: int): ...

    with pytest.raises(SystemExit):
        args.parser(main).parse_args([])


def test_default_is_optional():
    def main(epochs: int = 5): ...

    assert args.parser(main).parse_args([]).epochs == 5
    assert args.parser(main).parse_args(["--epochs", "9"]).epochs == 9


def test_bool_optional_action():
    def main(use_gpu: bool = False): ...

    p = args.parser(main)
    assert p.parse_args([]).use_gpu is False
    assert p.parse_args(["--use_gpu"]).use_gpu is True
    assert p.parse_args(["--no_use_gpu"]).use_gpu is False


def test_optional_defaults_to_none():
    from typing import Optional

    def main(seed: Optional[int]): ...

    p = args.parser(main)
    assert p.parse_args([]).seed is None
    assert p.parse_args(["--seed", "42"]).seed == 42


def test_union_none_syntax():
    def main(seed: int | None): ...

    assert args.parser(main).parse_args([]).seed is None


def test_list_type():
    def main(layers: list[int]): ...

    assert args.parser(main).parse_args(["--layers", "64", "32"]).layers == [64, 32]


def test_literal_str_becomes_choices():
    from typing import Literal

    def main(mode: Literal["train", "eval"]): ...

    p = args.parser(main)
    assert p.parse_args(["--mode", "train"]).mode == "train"
    with pytest.raises(SystemExit):
        p.parse_args(["--mode", "predict"])


def test_literal_int_coerces_and_constrains():
    from typing import Literal

    def main(level: Literal[1, 2, 3]): ...

    p = args.parser(main)
    assert p.parse_args(["--level", "2"]).level == 2
    with pytest.raises(SystemExit):
        p.parse_args(["--level", "4"])


def test_optional_literal_defaults_to_none():
    from typing import Literal

    def main(mode: Literal["train", "eval"] | None = None): ...

    p = args.parser(main)
    assert p.parse_args([]).mode is None
    assert p.parse_args(["--mode", "eval"]).mode == "eval"


def test_literal_with_default():
    from typing import Literal

    def main(mode: Literal["train", "eval"] = "train"): ...

    p = args.parser(main)
    assert p.parse_args([]).mode == "train"
    assert p.parse_args(["--mode", "eval"]).mode == "eval"
    with pytest.raises(SystemExit):
        p.parse_args(["--mode", "predict"])


class Color:
    def __init__(self, raw: str):
        self.raw = raw

    @classmethod
    def make(cls, raw: str) -> "Color":
        return cls(raw.upper())


def test_custom_type_default_constructor():
    def main(color: Color): ...

    ns = args.parser(main).parse_args(["--color", "red"])
    assert isinstance(ns.color, Color)
    assert ns.color.raw == "red"


def test_custom_type_with_type_init():
    @args.arg(type_init={Color: Color.make})
    def main(color: Color): ...

    ns = args.parser(main).parse_args(["--color", "red"])
    assert ns.color.raw == "RED"


def test_multi_type_union_errors():
    def main(x: int | str): ...

    with pytest.raises(TypeError):
        args.parser(main)


def test_unannotated_param_errors():
    def main(x): ...

    with pytest.raises(TypeError):
        args.parser(main)


def test_run_dispatches_and_returns():
    def main(a: int, b: int = 2):
        return a + b

    assert args.run(main, ["--a", "3"]) == 5
    assert args.run(main, ["--a", "3", "--b", "4"]) == 7


def test_to_argv_from_dict():
    assert args.to_argv({"learning_rate": 0.01, "epochs": 10}) == [
        "--learning_rate",
        "0.01",
        "--epochs",
        "10",
    ]


def test_to_argv_from_dataclass_with_bool_and_exclude():
    @dataclass
    class Cfg:
        epochs: int
        use_gpu: bool
        debug: bool

    assert args.to_argv(Cfg(epochs=5, use_gpu=True, debug=False), exclude={"debug"}) == [
        "--epochs",
        "5",
        "--use_gpu",
    ]


def test_to_argv_json_encodes_containers():
    assert args.to_argv({"layers": [64, 32]}) == ["--layers", "[64, 32]"]


def test_to_argv_bool_false_negates():
    assert args.to_argv({"use_gpu": False}) == ["--no_use_gpu"]
