# Contributing to ClearCut

Thank you for your interest in contributing to ClearCut! 🎬

ClearCut is an automated video editing pipeline for content creators. We welcome contributions of all kinds — bug fixes, features, documentation, tests, and more.

## Table of Contents

- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Pull Request Process](#pull-request-process)
- [Feature Flags / Optional Dependencies Policy](#feature-flags--optional-dependencies-policy)
- [Documentation](#documentation)
- [Issue Templates](#issue-templates)

---

## Development Setup

### Prerequisites

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/download.html) installed on your system
- [git](https://git-scm.com/)

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/salimhs/clearcut.git
cd clearcut

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package in editable mode with dev and test dependencies
pip install -e ".[dev,test]"
```

### Install with all optional dependencies

Some features require additional dependencies (see [Feature Flags](#feature-flags--optional-dependencies-policy)):

```bash
pip install -e ".[all,dev,test]"
```

---

## Code Style

ClearCut uses [ruff](https://docs.astral.sh/ruff/) for both linting and formatting, and [mypy](https://mypy-lang.org/) for static type checking.

### Linting

```bash
# Run ruff linter
ruff check .
```

### Formatting

```bash
# Format all files with ruff
ruff format .
```

### Type Checking

```bash
# Run mypy type checker
mypy clearcut/
```

### Configuration

All tool configuration lives in `pyproject.toml`:

- **ruff**: line length 100, target Python 3.10
- **mypy**: Python 3.10, `ignore_missing_imports = true`

### Guidelines

- Follow PEP 8 conventions
- Use type annotations for all function signatures
- Keep line length under 100 characters
- Write descriptive docstrings for public APIs
- Use `pathlib.Path` over `os.path`

---

## Testing

ClearCut uses [pytest](https://docs.pytest.org/) with coverage reporting.

### Running all tests

```bash
pytest
```

### Running with coverage

```bash
pytest --cov=clearcut --cov-report=term-missing
```

### Running specific test files

```bash
pytest tests/test_crop.py
pytest tests/test_color.py
pytest tests/test_intro.py
pytest tests/test_ramping.py
```

### Running tests by keyword

```bash
pytest -k "test_silence"          # Run tests matching "silence"
pytest -k "test_silence and not slow"  # Exclude slow tests
```

### Test configuration

Test configuration is in `pyproject.toml` under `[tool.pytest.ini_options]`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

---

## Pre-commit Hooks

ClearCut uses [pre-commit](https://pre-commit.com/) to automate code quality checks before each commit.

### Install hooks

```bash
pre-commit install
```

### Run hooks manually

```bash
pre-commit run --all-files
```

### What's checked

The pre-commit configuration runs:

1. **ruff** — lint and format check
2. **mypy** — static type checking (on staged files only)

> **Note:** If you installed with `pip install -e ".[dev]"`, pre-commit is already available.

---

## Pull Request Process

### Branch Naming

Use descriptive branch names with a prefix:

| Prefix     | Purpose                          |
|------------|----------------------------------|
| `feat/`    | New feature                      |
| `fix/`     | Bug fix                          |
| `docs/`    | Documentation changes            |
| `ci/`      | CI/CD configuration changes      |
| `refactor/`| Code refactoring (no behavior change) |
| `test/`    | Adding or updating tests         |
| `chore/`   | Maintenance, tooling, deps       |

Examples: `feat/auto-crop-detection`, `fix/silence-threshold-bug`, `docs/docker-quickstart`

### Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]
```

Examples:

```
feat(crop): add auto-crop detection for black bars
fix(silence): correct threshold parsing for float values
docs(readme): update installation instructions
ci(docker): add multistage build
test(ramping): add tests for frame ramping
```

### PR Process

1. **Create a branch** from `main` with an appropriate prefix
2. **Make your changes** following the code style and testing guidelines
3. **Run tests** locally to ensure nothing is broken:
   ```bash
   pytest --cov=clearcut
   ```
4. **Run linting and type checks**:
   ```bash
   ruff check .
   ruff format --check .
   mypy clearcut/
   ```
5. **Push your branch** and open a Pull Request against `main`
6. **Wait for CI** to pass (lint, type check, tests)
7. **Request a review** from a maintainer
8. **Address feedback** if needed — push additional commits
9. **Merge** once approved (squash merge preferred)

### PR Checklist

- [ ] Code follows the project's style guide
- [ ] Tests pass locally (`pytest --cov=clearcut`)
- [ ] Ruff linting and formatting pass (`ruff check . && ruff format --check .`)
- [ ] MyPy type checking passes (`mypy clearcut/`)
- [ ] New features include tests
- [ ] Documentation is updated if public API changed
- [ ] CHANGELOG.md is updated (if applicable)

---

## Feature Flags / Optional Dependencies Policy

ClearCut uses [PEP 508](https://peps.python.org/pep-0508/) optional dependencies to keep the core lightweight.

### Current optional dependency groups

| Extra      | Dependencies               | Enables                    |
|------------|----------------------------|----------------------------|
| `captions` | `whisperx`                 | Speech-to-text captions    |
| `silence`  | `torch`, `torchaudio`      | Silero-VAD silence removal |
| `scenes`   | `scenedetect[opencv]`      | Scene detection            |
| `all`      | everything above           | All features               |
| `dev`      | `ruff`, `mypy`, `pre-commit` | Development tooling      |
| `docs`     | `mkdocs`, `mkdocs-material` | Documentation build       |
| `test`     | `pytest`, `pytest-cov`, `pytest-mock` | Testing        |

### Policy

1. **Core dependencies** (`dependencies` in `pyproject.toml`) should be minimal — only what's needed for basic silence removal, compositing, and encoding.
2. **Heavy dependencies** (PyTorch, WhisperX, etc.) must be optional extras.
3. **New features** requiring new optional deps should add a new extra group.
4. **All extras** should be composable via `clearcut[all]`.

---

## Documentation

ClearCut uses [MkDocs](https://www.mkdocs.org/) with the [Material theme](https://squidfunk.github.io/mkdocs-material/) for documentation.

### Build locally

```bash
pip install -e ".[docs]"
mkdocs serve
```

### Documentation structure

```
docs/
├── index.md           # Home page
├── installation.md    # Installation guide
├── quickstart.md      # Quick start tutorial
├── cli-reference.md   # CLI command reference
├── configuration.md   # Configuration options
├── pipeline-stages.md # Pipeline architecture details
├── templates.md       # Template/preset documentation
├── faq.md             # Frequently asked questions
└── remote-gpu.md      # Remote GPU execution guide
```

---

## Issue Templates

ClearCut uses structured GitHub issue templates for bug reports and feature requests.

### Bug Reports

When filing a bug report, include:

- ClearCut version (`clearcut --version`)
- System information (`clearcut info`)
- The exact command that produced the error
- Expected vs actual behavior
- Steps to reproduce
- Input video metadata (duration, codec, resolution)
- Full error output

### Feature Requests

When suggesting a feature, include:

- The problem you're trying to solve
- Your proposed solution
- Alternative solutions considered
- Any examples or mockups

---

## Questions?

If you have questions or need help, please:

- Open a [Discussion](https://github.com/salimhs/clearcut/discussions)
- Check the [FAQ](https://github.com/salimhs/clearcut/blob/main/docs/faq.md)
- Review existing [Issues](https://github.com/salimhs/clearcut/issues)

---

*Happy cutting! 🎬*
