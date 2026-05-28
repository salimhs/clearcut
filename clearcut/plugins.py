"""Plugin system — load hooks from external Python files."""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from typing import Any, Callable

log = logging.getLogger(__name__)

# Hook registry: event -> stage_name -> list of callbacks
# Events: "before_stage", "after_stage"
_hooks: dict[str, dict[str, list[Callable[[str, dict[str, Any]], dict[str, Any]]]]] = {}


def register_hook(
    event: str,
    stage: str,
    callback: Callable[[str, dict[str, Any]], dict[str, Any]],
) -> None:
    """Register a hook callback for a pipeline event.

    Args:
        event: 'before_stage' or 'after_stage'.
        stage: Pipeline stage name (e.g., 'silence', 'encode').
        callback: Function receiving (stage_name, context) and returning modified context.
    """
    if event not in _hooks:
        _hooks[event] = {}
    if stage not in _hooks[event]:
        _hooks[event][stage] = []
    _hooks[event][stage].append(callback)


def run_hooks(event: str, stage: str, context: dict[str, Any]) -> dict[str, Any]:
    """Run all registered hooks for an event+stage combination.

    Args:
        event: 'before_stage' or 'after_stage'.
        stage: Pipeline stage name.
        context: Current pipeline context dict.

    Returns:
        Modified context after all hooks have run.
    """
    stage_hooks = _hooks.get(event, {}).get(stage, [])
    for hook in stage_hooks:
        try:
            context = hook(stage, context)
        except Exception as e:
            log.warning("Hook %s failed on %s/%s: %s", hook.__name__, event, stage, e)
    return context


def load_plugin(path: Path) -> dict[str, Any] | None:
    """Load a plugin from a Python file path.

    The plugin file can define:
    - ``register()`` function that calls ``register_hook()``

    Returns:
        Dict with plugin info, or None if loading failed.
    """
    path = Path(path)
    if not path.exists():
        log.warning("Plugin not found: %s", path)
        return None

    spec = importlib.util.spec_from_file_location(path.stem, str(path))
    if spec is None or spec.loader is None:
        log.warning("Could not load plugin: %s", path)
        return None

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        log.warning("Error loading plugin %s: %s", path, e)
        return None

    if hasattr(module, "register"):
        try:
            module.register()
        except Exception as e:
            log.warning("Error in plugin.register() for %s: %s", path, e)

    return {
        "name": path.stem,
        "path": str(path),
        "hooks": len(_hooks),
    }


def discover_plugins(paths: list[Path]) -> list[dict]:
    """Load all plugins from a list of file paths.

    Args:
        paths: List of plugin file paths.

    Returns:
        List of plugin info dicts.
    """
    results: list[dict] = []
    for p in paths:
        info = load_plugin(p)
        if info:
            results.append(info)
    return results
