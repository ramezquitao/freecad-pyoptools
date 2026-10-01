"""GUI tests: creation and versioning contract for every component.

This replaces the former ``tests/smoke/test_component_creation.py``, which
drove the Part classes through a hand-written ``FakeObj`` document object.
The fake had to re-implement FreeCAD's property and ``ViewObject`` semantics,
so it could drift from real FreeCAD and either miss real regressions or report
failures that only existed in the fake. These tests instead create **real**
``Part::FeaturePython`` objects through the public ``Insert*`` helpers, under
the GUI binary, and assert the same contract on them.

Every component is checked for:

* a wired ``Proxy``,
* a non-empty ``ComponentType``,
* ``BaseVersion`` equal to ``WBPart.CURRENT_BASE_VERSION``,
* an integer ``ObjectVersion`` equal to the class's ``CURRENT_PART_VERSION``,
* the base properties ``Enabled``, ``Reference`` and ``Notes``.

``PropagatePart`` is deliberately excluded: its ``__init__`` immediately calls
``getActiveSystem()`` and propagates rays (showing Qt error dialogs on failure),
so it cannot be instantiated in isolation. It stays covered by the versioning
contract test in ``tests/smoke`` and by ``ForwardCompatibilityGuard``.

Runs with the GUI FreeCAD binary, e.g.::

    xvfb-run -a -s "-screen 0 1024x768x24" freecad -P tests -t TestPyOpToolsGui
"""

import unittest

from freecad.pyoptools.pyOpToolsWB.aperture import AperturePart, InsertApp
from freecad.pyoptools.pyOpToolsWB.bscube import BSCubePart, InsertBSC
from freecad.pyoptools.pyOpToolsWB.cylindricallens import (
    CylindricalLensPart,
    InsertCL,
)
from freecad.pyoptools.pyOpToolsWB.diffractiongratting import (
    DiffractionGrattingPart,
    InsertDiffG,
)
from freecad.pyoptools.pyOpToolsWB.doubletlens import DoubletLensPart, InsertDL
from freecad.pyoptools.pyOpToolsWB.doveprism import DovePrismPart, InsertDP
from freecad.pyoptools.pyOpToolsWB.lensdata import InsertLD, LensDataPart
from freecad.pyoptools.pyOpToolsWB.pentaprism import InsertPP, PentaPrismPart
from freecad.pyoptools.pyOpToolsWB.powelllens import InsertSL as InsertPowell
from freecad.pyoptools.pyOpToolsWB.powelllens import PowellLensPart
from freecad.pyoptools.pyOpToolsWB.ray import InsertRay, RayPart
from freecad.pyoptools.pyOpToolsWB.raysarray import InsertRArray, RaysArrayPart
from freecad.pyoptools.pyOpToolsWB.raysparallel import InsertRPar, RaysParPart
from freecad.pyoptools.pyOpToolsWB.rayspoint import InsertRPoint, RaysPointPart
from freecad.pyoptools.pyOpToolsWB.rectmirror import InsertRectM, RectMirrorPart
from freecad.pyoptools.pyOpToolsWB.rightangleprism import (
    InsertRAP,
    RightAnglePrismPart,
)
from freecad.pyoptools.pyOpToolsWB.roundmirror import InsertRM, RoundMirrorPart
from freecad.pyoptools.pyOpToolsWB.sensor import InsertSen, SensorPart
from freecad.pyoptools.pyOpToolsWB.simpledmd import InsertSimpleDMD, SimpleDMDPart
from freecad.pyoptools.pyOpToolsWB.sphericallens import InsertSL, SphericalLensPart
from freecad.pyoptools.pyOpToolsWB.thicklens import InsertTL, ThickLensPart
from freecad.pyoptools.pyOpToolsWB.wbpart import WBPart
from tests.test_base_gui import PyOpToolsGuiTestCaseDoc

# A material that always resolves: the "Value" catalog returns the number.
MAT = dict(matcat="Value", matref="1.5")

# (PartClass, expected ComponentType, insert callable)
PART_CASES = [
    (AperturePart, "Aperture", lambda: InsertApp(InD=10, OutD=25, ID="AP")),
    (BSCubePart, "BSCube", lambda: InsertBSC(S=50, Ref=100, ID="BS", **MAT)),
    (CylindricalLensPart, "CylindricalLens",
     lambda: InsertCL(0.01, -0.01, 10, 20, 20, ID="CL", **MAT)),
    (DiffractionGrattingPart, "DiffractionGratting",
     lambda: InsertDiffG(100, 10, 50, 50, 0, 1000.0, [1], ID="DG", **MAT)),
    (DoubletLensPart, "DoubletLens",
     lambda: InsertDL(0.01, -0.01, 5, 0.01, -0.01, 5, 50, 1, "DL",
                      "Value", "1.5", "Value", "1.5")),
    (DovePrismPart, "DovePrism", lambda: InsertDP(S=20, L=50, ID="DP", **MAT)),
    (LensDataPart, "LensData",
     lambda: InsertLD((["Plane", "Plane"], [1e6, 1e6], [10.0, 10.0],
                       [12.5, 12.5], ["Value", "Value"], ["1.5", "1.5"]),
                      ID="LD")),
    (PentaPrismPart, "PentaPrism", lambda: InsertPP(S=50, ID="PP", **MAT)),
    (PowellLensPart, "PowellLens",
     lambda: InsertPowell(3.0, 7.62, -4.302, 8.89, ID="PL", **MAT)),
    (RayPart, "Ray", lambda: InsertRay(wavelength=633, ID="RY")),
    (RaysArrayPart, "RaysArray", lambda: InsertRArray(ID="RA")),
    (RaysParPart, "RaysPar", lambda: InsertRPar(ID="RP")),
    (RaysPointPart, "RaysPoint", lambda: InsertRPoint(ID="RPT")),
    (RectMirrorPart, "RectangularMirror",
     lambda: InsertRectM(100, 10, 50, 50, ID="RM", **MAT)),
    (RightAnglePrismPart, "RightAnglePrism",
     lambda: InsertRAP(S=50, ID="RAP", **MAT)),
    (RoundMirrorPart, "RoundMirror",
     lambda: InsertRM(Ref=100, Th=10, D=50, ID="RDM", **MAT)),
    (SensorPart, "Sensor", lambda: InsertSen(10, 10, ID="SEN")),
    (SimpleDMDPart, "SimpleDMD",
     lambda: InsertSimpleDMD(10, 10, 2, 12, 0, 0, 1, ID="DMD")),
    (SphericalLensPart, "SphericalLens",
     lambda: InsertSL(0.01, -0.01, 10, 50, ID="SL", **MAT)),
    (ThickLensPart, "ThickLens", lambda: InsertTL(ID="TL")),
]


class ComponentCreationContract(PyOpToolsGuiTestCaseDoc):
    """Every component wires the full WBPart contract on a real object."""

    def _assert_base_properties(self, obj, component_type):
        self.assertIsNotNone(obj.Proxy)
        self.assertEqual(obj.ComponentType, component_type)
        self.assertTrue(hasattr(obj, "Enabled"))
        self.assertTrue(hasattr(obj, "Reference"))
        self.assertTrue(hasattr(obj, "Notes"))
        self.assertEqual(obj.BaseVersion, WBPart.CURRENT_BASE_VERSION)
        self.assertIsInstance(obj.ObjectVersion, int)

    def test_every_part_instantiates_with_contract(self):
        for part_cls, component_type, insert in PART_CASES:
            with self.subTest(part=part_cls.__name__):
                obj = insert()
                self._assert_base_properties(obj, component_type)
                self.assertEqual(
                    obj.ObjectVersion, part_cls.CURRENT_PART_VERSION
                )

    def test_spherical_lens_creates_geometry(self):
        obj = InsertSL(0.01, -0.01, 10, 50, ID="SL_GEO", **MAT)
        self.assertGreater(obj.Shape.Volume, 0)

    def test_disabled_flag_is_stored(self):
        obj = InsertRPoint(enabled=False, ID="RPT_OFF")
        self.assertIs(obj.Enabled, False)


if __name__ == "__main__":
    unittest.main()
