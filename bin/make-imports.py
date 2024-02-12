#!/usr/bin/env python3
import inspect
import logging
import pkgutil
from argparse import ArgumentParser
from importlib import import_module, metadata
from sys import stdlib_module_names

logger = logging.getLogger(__name__)


def write(items, notfrom=False):
    if notfrom:
        return f"import {'.'.join(items)}"

    if len(items) == 1:
        return f"import {items[0]}"
    else:
        return f"from {'.'.join(items[:-1])} import {items[-1]}"


def process(parts, result):
    logger.info(f"Trying {parts}...")
    try:
        module = import_module(".".join(parts))
    except Exception:
        logger.warning(f"ERR {parts}")
        return
    result.append(write(parts, notfrom=True))

    packages_or_modules = set()

    if hasattr(module, "__path__"):
        for importer, name, ispkg in pkgutil.iter_modules(module.__path__):
            if name.startswith("_"):
                continue
            logger.info(f"FROMPATH {parts} {name} {ispkg}")
            process(parts + [name], result)
            packages_or_modules.add(name)

    if True:
        logger.info(f"AF {module}")

        # for name, obj in inspect.getmembers_static(module, lambda s):
        if hasattr(module, "__all__"):
            for name in module.__all__:
                if name in packages_or_modules:
                    continue

                result.append(write(parts + [name]))

        else:
            for name in dir(module):
                if name.startswith("_"):
                    continue
                if name in packages_or_modules:
                    continue

                obj = getattr(module, name)
                if inspect.ismodule(obj):
                    continue

                assoc_module = obj.__module__ if hasattr(obj, "__module__") else None
                logger.info(f"AFI {name} {type(obj)} {module.__name__} {assoc_module}")

                if assoc_module != module.__name__:
                    continue

                result.append(write(parts + [name]))


def _process_packages(iterable):
    result = []
    for package in iterable:
        process([package], result)

    for i in sorted(result):
        print(i)


# pkgutil.iter_modules()
# sys.stdlib_module_names
# for distribution in importlib.metadata.distributions():
#    print(distribution.metadata['Name'], distribution.metadata['Version'])


def dump_stdlib_imports(packages=None, excludes=None):
    excludes = excludes or set(["antigravity", "idlelib", "test", "this"])
    if packages:
        packages = (
            package
            for package in packages
            if package in stdlib_module_names and package not in excludes
        )
    else:
        packages = (
            package for package in stdlib_module_names if package not in excludes
        )

    packages = (
        package
        for package in packages
        if not package.startswith("_") or package == "__future__"
    )
    _process_packages(packages)


def dump_thirdparty_imports(packages=None, excludes=None):
    excludes = excludes or set()
    # packages = (
    #     packages
    #     if packages
    #     else (dist.metadata["Name"] for dist in metadata.distributions())
    # )
    packages = (
        package
        for package in (
            packages or (dist.metadata["Name"] for dist in metadata.distributions())
        )
        if package not in excludes
    )
    _process_packages(packages)


def dump_develop_imports(packages=None, excludes=None):
    excludes = excludes or set()
    packages = (package for package in (packages or []) if package not in excludes)
    _process_packages(packages)


if __name__ == "__main__":
    p = ArgumentParser()
    p.add_argument("package", nargs="*")
    p.add_argument("--exclude", "-e", action="append")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--stdlib", action="store_true")
    group.add_argument("--thirdparty", action="store_true")
    group.add_argument("--develop", action="store_true", default=True)
    args = p.parse_args()
    if args.stdlib:
        dump_stdlib_imports(args.package, args.exclude)
    elif args.thirdparty:
        dump_thirdparty_imports(args.package, args.exclude)
    elif args.develop:
        dump_develop_imports(args.package, args.exclude)
    else:
        raise RuntimeError("Bad option")
