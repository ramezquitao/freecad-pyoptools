"""Aggregate test module for the pyOpTools workbench.

Registered with FreeCAD's ``Test`` runner so the suite can be launched with the
native command:

    freecadcmd -t TestPyOpTools
    FreeCAD    -t TestPyOpTools

It can also be run from within FreeCAD:

    import Test, TestPyOpTools
    Test.runTestsFromModule(TestPyOpTools)

The individual test classes live in ``tests/unit``, ``tests/smoke`` and
``tests/integration``. Importing them here makes them discoverable by the
``Test`` runner, which collects every ``unittest.TestCase`` in this module.

Importing this module requires the repository root on ``sys.path`` and the
headless GUI shim; both are applied by ``tests/bootstrap.py`` (imported first).
"""

import os
import sys

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

import bootstrap  # noqa: E402,F401  (applies source-tree + GUI shim)

from unit.test_component_info_formatter import (  # noqa: E402
    ComponentInfo,
    HumanReadable,
    NumberFormatting,
    Units,
    ValueFormatting,
)
from smoke.test_imports import WorkbenchImports  # noqa: E402
from smoke.test_wbpart_versions import WBPartVersions  # noqa: E402
from integration.test_optical_system import (  # noqa: E402
    ForwardCompatibilityGuard,
    Materials,
    PlacementConversion,
    RayPropagation,
)

# Reference the imported classes so linters do not flag them as unused. The
# ``Test`` runner discovers them via ``unittest``'s module introspection.
_ = (
    HumanReadable,
    NumberFormatting,
    Units,
    ValueFormatting,
    ComponentInfo,
    WorkbenchImports,
    WBPartVersions,
    Materials,
    PlacementConversion,
    RayPropagation,
    ForwardCompatibilityGuard,
)
