#!/usr/bin/env python3
import inspect
import logging
import pkgutil
from importlib import import_module
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


result = []

exclude = ["antigravity", "idlelib", "test", "this"]

#for _, module_name, _ in pkgutil.iter_modules():
for module_name in stdlib_module_names:
    if (module_name in exclude) or (module_name.startswith("_")):
        continue
    process([module_name], result)

for i in sorted(result):
    print(i)


# for distribution in importlib.metadata.distributions():
#    print(distribution.metadata['Name'], distribution.metadata['Version'])

# or

# pkgutil.iter_modules()
