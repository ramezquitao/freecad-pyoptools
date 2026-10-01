"""GUI aggregate test module for the pyOpTools workbench.

Registered with FreeCAD's ``Test`` runner so the GUI suite can be launched with
the full FreeCAD executable and a display:

    xvfb-run -a -s "-screen 0 1024x768x24" freecad -P tests -t TestPyOpToolsGui

or, from within FreeCAD's Python console:

    import Test, TestPyOpToolsGui
    Test.runTestsFromModule(TestPyOpToolsGui)

The non-GUI suites live in ``TestPyOpTools`` (run with ``freecadcmd``).
"""

import os
import sys

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

import test_base_gui  # noqa: E402,F401  (applies source-tree precedence)

from gui.test_viewproviders import (  # noqa: E402
    RaysPointGui,
    RoundMirrorGui,
    SensorGui,
    SphericalLensGui,
    ViewObjectAvailability,
)
from gui.test_pyoptools_repr import (  # noqa: E402
    DoubletLensBranchRepr,
    LensReprParameters,
    MirrorFilterRepr,
    PrismAndMirrorRepr,
    RaySourceRepr,
    WavelengthUnitsRepr,
)
from gui.test_component_creation import ComponentCreationContract  # noqa: E402
from gui.test_panels import LightSourcesPanelGui, SensorsPanelGui  # noqa: E402

_ = (
    ViewObjectAvailability,
    SphericalLensGui,
    RoundMirrorGui,
    SensorGui,
    RaysPointGui,
    PrismAndMirrorRepr,
    LensReprParameters,
    DoubletLensBranchRepr,
    MirrorFilterRepr,
    RaySourceRepr,
    WavelengthUnitsRepr,
    ComponentCreationContract,
    SensorsPanelGui,
    LightSourcesPanelGui,
)
