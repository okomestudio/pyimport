#!/usr/bin/env python
"""Generate import statements."""
import inspect
import logging
import pkgutil
from argparse import ArgumentParser
from importlib import import_module, metadata
from sys import stdlib_module_names
from typing import Iterable, List, Set

logger = logging.getLogger(__name__)


def write(items: List[str], notfrom: bool = False) -> str:
    """Return an (from) import statement in string.

    Set `notfrom` to `True` to force `import ...` form.
    """
    if notfrom:
        return f"import {'.'.join(items)}"
    if len(items) == 1:
        return f"import {items[0]}"
    else:
        return f"from {'.'.join(items[:-1])} import {items[-1]}"


def _find_importables(parts: List[str], result: List[str]) -> None:
    logger.debug(f"_find_importables({parts})...")
    try:
        module = import_module(".".join(parts))
    except Exception:
        logger.debug(f"Not a module or package: {parts}")
        return

    result.append(write(parts, notfrom=True))

    seen = set()

    if hasattr(module, "__path__"):
        for importer, name, ispkg in pkgutil.iter_modules(module.__path__):
            logger.debug(f"From __path__: {parts} {name} {ispkg}")
            if name.startswith("_"):
                continue

            _find_importables(parts + [name], result)
            seen.add(name)

    if hasattr(module, "__all__"):
        for name in (name for name in module.__all__ if name not in seen):
            logger.debug(f"From __all__: {parts} {name}")
            result.append(write(parts + [name]))

    else:
        for name in (name for name in dir(module) if name not in seen):
            logger.debug(f"From dir(module): {parts} {name}")
            if name.startswith("_"):
                continue

            obj = getattr(module, name)

            # If this is a module and not a package, then most likely
            # this is an import of stdlib or third-party
            # module/package, which we don't want to process.
            if inspect.ismodule(obj):
                continue

            assoc_module = obj.__module__ if hasattr(obj, "__module__") else None
            logger.debug(
                f"Found {name} associated with {assoc_module} in {module.__name__}"
            )

            # If the imported object is not associated with the
            # currently inspected module/package but with a stdlib or
            # third-party module/package, don't want this exposed.
            if assoc_module != module.__name__:
                continue

            result.append(write(parts + [name]))


def _process_packages(iterable: Iterable) -> None:
    """Iterate over packages and dump import statements to STDOUT."""
    result: List[str] = []
    for package in iterable:
        _find_importables([package], result)

    for i in sorted(result):
        print(i)


def _dump_stdlib_imports(packages: Set[str], excludes: Set[str]) -> None:
    excludes = excludes or set(["antigravity", "idlelib", "test", "this"])
    if packages:
        gen = (
            package
            for package in packages
            if package in stdlib_module_names and package not in excludes
        )
    else:
        gen = (package for package in stdlib_module_names if package not in excludes)

    gen = (
        package
        for package in gen
        if not package.startswith("_") or package == "__future__"
    )
    _process_packages(gen)


def _dump_thirdparty_imports(packages: Set[str], excludes: Set[str]) -> None:
    gen = (
        package
        for package in (
            packages or (dist.metadata["Name"] for dist in metadata.distributions())
        )
        if package not in excludes
    )
    _process_packages(gen)


def _dump_develop_imports(packages: Set[str], excludes: Set[str]) -> None:
    _process_packages((package for package in packages if package not in excludes))


if __name__ == "__main__":
    p = ArgumentParser()
    p.add_argument("package", nargs="*", help="Python module(s) to include.")
    p.add_argument("--exclude", "-e", action="append", help="Python modules to exclude")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--stdlib", action="store_true")
    group.add_argument("--thirdparty", action="store_true")
    group.add_argument("--develop", action="store_true", default=True)
    args = p.parse_args()

    if args.stdlib:
        func = _dump_stdlib_imports
    elif args.thirdparty:
        func = _dump_thirdparty_imports
    else:
        func = _dump_develop_imports

    packages = set(args.package or [])
    excludes = set(args.exclude or [])
    func(packages, excludes)
