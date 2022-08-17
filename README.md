# DashAI2
DashAI2: a graphical toolbox for training, evaluating and deploying state-of-the-art AI models

## Dev Requirements

Please install on this order:

### On front/

```bash
$ npm install
```

### On back/

```bash
$ pip install -r requirements.txt && pip install -r requirements-dev.txt
```

### On root

```bash
$ pre-commit install && git config core.hooksPath .git-hooks
```

## Branches regex

All branches should be named one of the following:
develop|main|release
front/[A-Z]+-[0-9]+_[A-Z]+_.+
back/[A-Z]+-[0-9]+_[A-Z]+_.+
