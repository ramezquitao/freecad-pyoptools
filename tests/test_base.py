"""Shared test infrastructure for the pyOpTools workbench test suite.

Follows the FreeCAD convention (see ``src/Mod/Draft/drafttests/test_base.py``):
tests use the standard library ``unittest`` and the FreeCAD ``Test`` runner, so
no third-party test dependency is needed inside FreeCAD's interpreter.

The GUI shim and source-tree bootstrap live in ``tests/bootstrap.py`` and are
applied by the runner (``tests/run_headless.py``) before any test is imported.
"""

import unittest

import FreeCAD as App


class PyOpToolsTestCaseDoc(unittest.TestCase):
    """Base class for tests that require an active document."""

    def setUp(self):
        name = "___".join(self.id().split(".")[-2:])
        if name not in App.listDocuments():
            App.newDocument(name)
        App.setActiveDocument(name)
        self.doc = App.ActiveDocument
        # Guarantee cleanup even if tearDown is skipped on error.
        self.addCleanup(self._close_doc_quietly, name)

    def tearDown(self):
        pass

    @staticmethod
    def _close_doc_quietly(name):
        if name in App.listDocuments():
            App.closeDocument(name)


class PyOpToolsTestCaseNoDoc(unittest.TestCase):
    """Base class for tests that do not require a document."""
