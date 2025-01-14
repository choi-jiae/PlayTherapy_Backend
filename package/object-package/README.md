# PlayTherapy_Backend/cloud-package
AWS S3를 다루는 tool code가 포함되어 있습니다.

## Install Env

```bash
pip install poetry
```

## Install Dependency

```bash
cd package/object-package
poetry install --sync
```

## Test

```bash
cd package/object-package
poetry run python -m unittest discover -s tests
```