"""GUI tests: real component creation with real ViewObjects.

These tests run with the full FreeCAD GUI under a display (``xvfb-run`` in
headless environments). They exercise the real view providers: transparency,
shape colours and the visual response to the ``Enabled`` property.

Runs with the GUI FreeCAD binary, e.g.::

    xvfb-run -a -s "-screen 0 1024x768x24" freecad -P tests -t TestPyOpToolsGui
"""

import unittest

import FreeCAD
import FreeCADGui

from freecad.pyoptools.pyOpToolsWB.sphericallens import InsertSL
from freecad.pyoptools.pyOpToolsWB.roundmirror import InsertRM
from freecad.pyoptools.pyOpToolsWB.sensor import InsertSen
from freecad.pyoptools.pyOpToolsWB.rayspoint import InsertRPoint
from tests.test_base_gui import PyOpToolsGuiTestCaseDoc


class ViewObjectAvailability(PyOpToolsGuiTestCaseDoc):
    """Sanity: GUI mode really provides view objects and the command registry."""

    def test_view_object_is_created(self):
        obj = self.doc.addObject("Part::FeaturePython", "VO")
        self.assertIsNotNone(obj.ViewObject)

    def test_command_registry_exists(self):
        self.assertTrue(hasattr(FreeCADGui, "addCommand"))


# Transparency contract: components are created at 50, disabling sets 90,
# re-enabling sets 30 (see WBPart.onChanged). The 30-vs-50 asymmetry for the
# "enabled" state is suspected to be a long-standing BUG (tracked in issue #19:
# https://github.com/cihologramas/freecad-pyoptools/issues/19)
# but it is current behavior and these tests pin it deliberately. If
# WBPart.onChanged is fixed (30 -> 50), update these tests in the SAME commit.
class SphericalLensGui(PyOpToolsGuiTestCaseDoc):
    def test_creation_sets_transparency_and_shape(self):
        obj = InsertSL(CS1=0.01, CS2=-0.01, CT=10, D=50, ID="L1")
        self.assertIsNotNone(obj.ViewObject)
        self.assertEqual(obj.ViewObject.Transparency, 50)
        self.assertGreater(obj.Shape.Volume, 0)

    def test_disabling_increases_transparency(self):
        obj = InsertSL(ID="L2")
        obj.Enabled = False
        FreeCAD.ActiveDocument.recompute()
        self.assertEqual(obj.ViewObject.Transparency, 90)

    def test_reenabling_restores_transparency(self):
        obj = InsertSL(ID="L3")
        obj.Enabled = False
        obj.Enabled = True
        FreeCAD.ActiveDocument.recompute()
        self.assertEqual(obj.ViewObject.Transparency, 30)


class RoundMirrorGui(PyOpToolsGuiTestCaseDoc):
    def test_creation_sets_transparency_and_shape(self):
        obj = InsertRM(Ref=100, Th=10, D=50, ID="M1")
        self.assertIsNotNone(obj.ViewObject)
        self.assertEqual(obj.ViewObject.Transparency, 50)
        self.assertGreater(obj.Shape.Volume, 0)


class SensorGui(PyOpToolsGuiTestCaseDoc):
    def test_creation_sets_transparency(self):
        obj = InsertSen(height=10, width=10, ID="SEN1")
        self.assertIsNotNone(obj.ViewObject)
        self.assertEqual(obj.ViewObject.Transparency, 50)


class RaysPointGui(PyOpToolsGuiTestCaseDoc):
    def test_creation_and_wavelength_colour(self):
        obj = InsertRPoint(nr=6, na=6, distribution="polar", wavelength=633,
                           angle=30, ID="S1")
        self.assertIsNotNone(obj.ViewObject)
        # A red wavelength should set a shape colour (r, g, b, a).
        colour = obj.ViewObject.ShapeColor
        self.assertEqual(len(colour), 4)
        self.assertGreater(colour[0], colour[2])


if __name__ == "__main__":
    unittest.main()
