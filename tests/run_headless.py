"""Headless test runner for freecad-pyoptools.

Runs the workbench test suite inside FreeCAD's console interpreter
(``freecadcmd``), which is the only interpreter that has FreeCAD and pyoptools
available. No third-party test dependency is required: the suite uses the
standard library ``unittest`` and FreeCAD's ``Test`` runner.

Usage (see ``tests/run.sh`` for the convenience wrapper)::

    freecadcmd -c "exec(open('tests/run_headless.py').read())"

The suite is selected with the ``PYOPTOOLS_TEST_SUITE`` environment variable
(``unit``, ``smoke``, ``integration`` or ``all``).

The script makes the repository source tree take precedence over the copy
installed in FreeCAD's ``Mod/`` directory, so the tests always run against the
code in this repository.
"""

import os
import sys
import unittest

TESTS_DIR = os.environ.get(
    "PYOPTOOLS_TESTS_DIR",
    os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd(),
)
REPO_ROOT = os.path.dirname(TESTS_DIR)

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if TESTS_DIR not in sys.path:
    sys.path.insert(0, TESTS_DIR)

import bootstrap  # noqa: E402,F401  (source-tree precedence + GUI shim)

SUITES = {
    "unit": [
        "unit.test_component_info_formatter",
    ],
    "smoke": [
        "smoke.test_imports",
        "smoke.test_wbpart_versions",
    ],
    "integration": [
        "integration.test_optical_system",
    ],
}

SUITES["all"] = SUITES["smoke"] + SUITES["integration"] + SUITES["unit"]


def main(argv):
    suite_name = os.environ.get("PYOPTOOLS_TEST_SUITE")
    if suite_name is None and len(argv) >= 2 and not argv[1].startswith("-"):
        suite_name = argv[1]

    if suite_name not in SUITES:
        sys.stderr.write(
            "Usage: PYOPTOOLS_TEST_SUITE=<suite> freecadcmd -c "
            "'exec(open(\"tests/run_headless.py\").read())'\n"
            f"Available suites: {', '.join(SUITES)}\n"
        )
        return 2

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for module_name in SUITES[suite_name]:
        suite.addTests(loader.loadTestsFromName(module_name))

    result = unittest.TextTestRunner(verbosity=2).run(suite)

    status = "OK" if result.wasSuccessful() else "FAILURES"
    sys.stdout.write(
        f"\n[pyoptools-tests] suite='{suite_name}' "
        f"run={result.testsRun} failures={len(result.failures)} "
        f"errors={len(result.errors)} ({status})\n"
    )
    sys.stdout.flush()
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
