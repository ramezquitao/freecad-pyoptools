"""Smoke tests: every workbench module must import cleanly.

Catches broken imports, star-import regressions, circular imports and
``CURRENT_PART_VERSION`` contract violations at import time. This is the test
recommended by REFACTOR_PLAN.md.

Runs inside FreeCAD's interpreter.
"""

import importlib
import pkgutil
import unittest

import freecad.pyoptools.pyOpToolsWB as wb_pkg
from tests.test_base import PyOpToolsTestCaseNoDoc

WB_PACKAGE = "freecad.pyoptools.pyOpToolsWB"


def _discover_modules():
    return sorted(
        mod.name
        for mod in pkgutil.walk_packages(wb_pkg.__path__, prefix=WB_PACKAGE + ".")
    )


class WorkbenchImports(PyOpToolsTestCaseNoDoc):
    """Import every module in the workbench package."""

    def test_workbench_package_has_modules(self):
        self.assertGreater(len(_discover_modules()), 10)

    def test_each_module_imports(self):
        for name in _discover_modules():
            with self.subTest(module=name):
                importlib.import_module(name)


if __name__ == "__main__":
    unittest.main()
