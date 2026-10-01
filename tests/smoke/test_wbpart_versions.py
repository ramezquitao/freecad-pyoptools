"""Smoke test: WBPart versioning contract.

``WBPart.__init_subclass__`` enforces that every child class defines a valid
``CURRENT_PART_VERSION``. This test verifies that the contract holds for all
concrete parts loaded by the workbench.

Runs inside FreeCAD's interpreter.
"""

import unittest

from freecad.pyoptools.pyOpToolsWB.wbpart import WBPart
from tests.test_base import PyOpToolsTestCaseNoDoc


def _all_subclasses(cls):
    out = []
    for sub in cls.__subclasses__():
        out.append(sub)
        out.extend(_all_subclasses(sub))
    return out


class WBPartVersions(PyOpToolsTestCaseNoDoc):
    """Validate the WBPart versioning contract."""

    def test_every_subclass_defines_current_part_version(self):
        subclasses = _all_subclasses(WBPart)
        self.assertTrue(subclasses, "No WBPart subclasses found")
        for cls in subclasses:
            with self.subTest(cls=cls.__name__):
                self.assertIn("CURRENT_PART_VERSION", cls.__dict__)
                self.assertIsInstance(cls.CURRENT_PART_VERSION, int)
                self.assertGreaterEqual(cls.CURRENT_PART_VERSION, 0)

    def test_expected_parts_are_registered(self):
        names = {cls.__name__ for cls in _all_subclasses(WBPart)}
        for expected in (
            "AperturePart",
            "BSCubePart",
            "CylindricalLensPart",
            "DiffractionGrattingPart",
            "DoubletLensPart",
            "DovePrismPart",
            "LensDataPart",
            "PentaPrismPart",
            "PowellLensPart",
            "PropagatePart",
            "RayPart",
            "RaysArrayPart",
            "RaysParPart",
            "RaysPointPart",
            "RectMirrorPart",
            "RightAnglePrismPart",
            "RoundMirrorPart",
            "SensorPart",
            "SimpleDMDPart",
            "SphericalLensPart",
            "ThickLensPart",
        ):
            self.assertIn(expected, names)


if __name__ == "__main__":
    unittest.main()
