"""GUI test infrastructure for the pyOpTools workbench.

These tests require the full ``FreeCAD`` executable (not ``freecadcmd``) running
with a display. In CI and headless environments they are run under ``xvfb-run``,
mirroring how FreeCAD runs its own GUI tests (see ``TestDraftGui``).

Only the pieces of ``tests/bootstrap.py`` that are relevant without a console
interpreter are applied here: the repository source tree is forced to take
precedence over the installed Mod copy. The ``FreeCADGui.addCommand`` shim is
*not* installed, because in GUI mode it already exists and the commands must be
registered for real.
"""

import os
import sys
import unittest

import FreeCAD as App

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_TESTS_DIR)


def _force_repo_source_tree():
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)
    installed_markers = (
        "Mod/pyOpToolsWorkbench",
        os.sep + "Mod" + os.sep + "pyoptools",
    )
    sys.path[:] = [
        p
        for p in sys.path
        if not any(marker in p.replace("\\", "/") for marker in installed_markers)
    ]

    import freecad

    freecad.__path__ = [
        p
        for p in getattr(freecad, "__path__", [])
        if "pyOpToolsWorkbench" not in p.replace("\\", "/")
    ]
    repo_freecad = os.path.join(_REPO_ROOT, "freecad")
    if repo_freecad not in freecad.__path__:
        freecad.__path__.insert(0, repo_freecad)

    for name in list(sys.modules):
        if name == "freecad.pyoptools" or name.startswith("freecad.pyoptools."):
            del sys.modules[name]


_force_repo_source_tree()


class PyOpToolsGuiTestCaseDoc(unittest.TestCase):
    """Base class for GUI tests that require an active document."""

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
