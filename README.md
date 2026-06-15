# vire-gap

Utilities for the Gemini Enterprise Agent Platform (formerly Vertex AI).

```
pip install vire-gap   # imports as vire_gap
```

## `vire_gap.args` — type-driven argparse

Derive an `argparse` parser from a function's type hints — tuned for the platform,
where hyperparameters arrive as `--learning_rate 0.01` (double-dash,
underscore-separated, every value passed by name).

```python
from vire_gap import args

def main(learning_rate: float, epochs: int = 10, use_gpu: bool = False):
    ...

if __name__ == "__main__":
    args.run(main)
```

```
python train.py --learning_rate 0.01 --epochs 5 --use_gpu
```

- Every parameter becomes a `--flag`; underscores are preserved (unlike `argh`).
- No default → required; has a default → optional with that default.
- `bool` → `--use_gpu` / `--no_use_gpu`.
- `Optional[T]` / `T | None` → optional flag, defaults to `None`.
- `list[T]` → `--layers 64 32` → `[64, 32]`.

### Custom types

Custom types are constructed from their string value. By default the type itself
is the converter; override it per type with the `@args.arg` decorator:

```python
from vire_gap import args

@args.arg(type_init={Path: Path, Config: Config.from_json})
def main(out_dir: Path, config: Config):
    ...
```

The converter is passed straight to argparse as `type=`.

### API

- `args.run(func, argv=None)` — build the parser, parse `argv`, call `func(**parsed)`, return its result.
- `args.parser(func)` — return the configured `argparse.ArgumentParser`.
- `args.arg(type_init=...)` — decorator registering per-type string converters.
- `args.to_argv(instance, exclude=None)` — render a dataclass instance or mapping back into an argv list (inverse of parsing).
