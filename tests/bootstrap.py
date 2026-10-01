"""Bootstrap helpers for running the pyOpTools tests inside FreeCAD.

These helpers make the tests runnable in FreeCAD's console interpreter, where:

* the installed Mod copy of the workbench would otherwise shadow the repository
  source tree under test, and
* ``FreeCADGui`` lacks the command registry / UI loader used by the workbench
  package at import time.

Importing this module applies both fixes. It is safe to import repeatedly.
"""

import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)


def _force_repo_source_tree():
    """Make ``freecad.pyoptools`` resolve to the repository under test.

    FreeCAD adds the installed Mod copy (e.g.
    ``~/.local/share/FreeCAD/v1-1/Mod/pyOpToolsWorkbench``) to ``sys.path``.
    Because ``freecad`` is a namespace package, both trees merge and the Mod
    copy may win. Remove any path pointing at an installed pyOpTools workbench
    and drop cached modules so the repo source is used instead.
    """
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)

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
    repo_freecad = os.path.join(REPO_ROOT, "freecad")
    if repo_freecad not in freecad.__path__:
        freecad.__path__.insert(0, repo_freecad)

    for name in list(sys.modules):
        if name == "freecad.pyoptools" or name.startswith("freecad.pyoptools."):
            del sys.modules[name]


def _install_headless_gui_shim():
    """Provide the GUI bits the workbench package expects at import time.

    In console mode ``FreeCADGui`` exposes no command registry, but
    ``pyOpToolsWB/__init__.py`` calls ``FreeCADGui.addCommand`` for every
    command. The shim records the commands instead of failing.
    """
    import FreeCADGui

    if not hasattr(FreeCADGui, "addCommand"):
        registered = {}

        def addCommand(name, command):
            registered[name] = command

        FreeCADGui.addCommand = addCommand
        FreeCADGui._headless_registered_commands = registered


_force_repo_source_tree()
_install_headless_gui_shim()
