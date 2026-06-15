# vire

Derive an `argparse` parser from a function's type hints — tuned for Vertex AI,
where hyperparameters arrive as `--learning_rate 0.01` (double-dash,
underscore-separated, every value passed by name).

```python
import vire

def main(learning_rate: float, epochs: int = 10, use_gpu: bool = False):
    ...

if __name__ == "__main__":
    vire.run(main)
```

```
python train.py --learning_rate 0.01 --epochs 5 --use_gpu
```

- Every parameter becomes a `--flag`; underscores are preserved (unlike `argh`).
- No default → required; has a default → optional with that default.
- `bool` → `--use_gpu` / `--no_use_gpu`.
- `Optional[T]` / `T | None` → optional flag, defaults to `None`.
- `list[T]` → `--layers 64 32` → `[64, 32]`.

## Custom types

Custom types are constructed from their string value. By default the type itself
is the converter; override it per type with the `@vire.vire` decorator:

```python
@vire.vire(type_init={Path: Path, Config: Config.from_json})
def main(out_dir: Path, config: Config):
    ...
```

The converter is passed straight to argparse as `type=`.

## API

- `vire.run(func, argv=None)` — build the parser, parse `argv`, call `func(**parsed)`, return its result.
- `vire.parser(func)` — return the configured `argparse.ArgumentParser`.
- `vire.vire(type_init=...)` — decorator registering per-type string converters.
