from dataclasses import dataclass

import pytest

import vire


def test_basic_types_coerce():
    def main(learning_rate: float, epochs: int, name: str): ...

    ns = vire.parser(main).parse_args(["--learning_rate", "0.01", "--epochs", "10", "--name", "run-a"])
    assert ns.learning_rate == 0.01
    assert ns.epochs == 10
    assert ns.name == "run-a"


def test_underscores_preserved_in_flags():
    def main(learning_rate: float): ...

    with pytest.raises(SystemExit):
        # hyphenated form must NOT be accepted
        vire.parser(main).parse_args(["--learning-rate", "0.01"])


def test_missing_required_errors():
    def main(epochs: int): ...

    with pytest.raises(SystemExit):
        vire.parser(main).parse_args([])


def test_default_is_optional():
    def main(epochs: int = 5): ...

    assert vire.parser(main).parse_args([]).epochs == 5
    assert vire.parser(main).parse_args(["--epochs", "9"]).epochs == 9


def test_bool_optional_action():
    def main(use_gpu: bool = False): ...

    p = vire.parser(main)
    assert p.parse_args([]).use_gpu is False
    assert p.parse_args(["--use_gpu"]).use_gpu is True
    assert p.parse_args(["--no_use_gpu"]).use_gpu is False


def test_optional_defaults_to_none():
    from typing import Optional

    def main(seed: Optional[int]): ...

    p = vire.parser(main)
    assert p.parse_args([]).seed is None
    assert p.parse_args(["--seed", "42"]).seed == 42


def test_union_none_syntax():
    def main(seed: int | None): ...

    assert vire.parser(main).parse_args([]).seed is None


def test_list_type():
    def main(layers: list[int]): ...

    assert vire.parser(main).parse_args(["--layers", "64", "32"]).layers == [64, 32]


class Color:
    def __init__(self, raw: str):
        self.raw = raw

    @classmethod
    def make(cls, raw: str) -> "Color":
        return cls(raw.upper())


def test_custom_type_default_constructor():
    def main(color: Color): ...

    ns = vire.parser(main).parse_args(["--color", "red"])
    assert isinstance(ns.color, Color)
    assert ns.color.raw == "red"


def test_custom_type_with_type_init():
    @vire.vire(type_init={Color: Color.make})
    def main(color: Color): ...

    ns = vire.parser(main).parse_args(["--color", "red"])
    assert ns.color.raw == "RED"


def test_multi_type_union_errors():
    def main(x: int | str): ...

    with pytest.raises(TypeError):
        vire.parser(main)


def test_unannotated_param_errors():
    def main(x): ...

    with pytest.raises(TypeError):
        vire.parser(main)


def test_run_dispatches_and_returns():
    def main(a: int, b: int = 2):
        return a + b

    assert vire.run(main, ["--a", "3"]) == 5
    assert vire.run(main, ["--a", "3", "--b", "4"]) == 7


def test_to_argv_from_dict():
    assert vire.to_argv({"learning_rate": 0.01, "epochs": 10}) == [
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

    assert vire.to_argv(Cfg(epochs=5, use_gpu=True, debug=False), exclude={"debug"}) == [
        "--epochs",
        "5",
        "--use_gpu",
    ]


def test_to_argv_json_encodes_containers():
    assert vire.to_argv({"layers": [64, 32]}) == ["--layers", "[64, 32]"]


def test_to_argv_bool_false_negates():
    assert vire.to_argv({"use_gpu": False}) == ["--no_use_gpu"]
