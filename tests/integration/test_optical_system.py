"""Integration tests: optical system construction and ray propagation.

Exercises the numerical core of the workbench without a GUI:

* ``getMaterial`` resolves catalog materials and numeric values.
* ``getObjectPyOptoolsPose`` converts a FreeCAD Placement into the
  ``((X, Y, Z), (Rx, Ry, Rz))`` representation pyoptools expects.
* A minimal source + lens + sensor system actually propagates rays and the
  sensor records hits.

Runs inside FreeCAD's interpreter.
"""

import math
import unittest

import FreeCAD
import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.ray.ray_source as ray_source
from pyoptools.raytrace.system import System

from freecad.pyoptools.pyOpToolsWB.pyoptoolshelpers import (
    getMaterial,
    getObjectPyOptoolsPose,
)
from tests.test_base import PyOpToolsTestCaseDoc, PyOpToolsTestCaseNoDoc


def _build_system():
    source = ray_source.point_source_p(
        origin=(0, 0, -50),
        direction=(0, 0, 0),
        span=0.1,
        num_rays=(5, 5),
        wavelength=0.633,
        label="S",
    )
    lens = comp_lib.SphericalLens(
        radius=12.5,
        thickness=10,
        curvature_s1=0.01,
        curvature_s2=-0.01,
        material=1.5,
    )
    sensor = comp_lib.CCD((10, 10))
    system = System(
        [
            (lens, (0, 0, 0), (0, 0, 0), "L"),
            (sensor, (0, 0, 100), (0, 0, 0), "SEN"),
        ]
    )
    return system, source


class Materials(PyOpToolsTestCaseNoDoc):
    """Material resolution."""

    def test_numeric_value(self):
        self.assertAlmostEqual(getMaterial("Value", "1.5"), 1.5)

    def test_numeric_value_with_comma(self):
        self.assertAlmostEqual(getMaterial("Value", "1,5"), 1.5)

    def test_from_catalog(self):
        self.assertIsNotNone(getMaterial("schott", "N-BK7"))


class PlacementConversion(PyOpToolsTestCaseDoc):
    """FreeCAD Placement -> pyoptools pose conversion."""

    def test_identity_placement(self):
        obj = self.doc.addObject("Part::Feature", "P")
        obj.Placement = FreeCAD.Placement(
            FreeCAD.Vector(1.0, 2.0, 3.0), FreeCAD.Rotation(0, 0, 0)
        )
        (x, y, z), (rx, ry, rz) = getObjectPyOptoolsPose(obj)
        for got, expected in zip((x, y, z), (1.0, 2.0, 3.0)):
            self.assertAlmostEqual(got, expected)
        for got, expected in zip((rx, ry, rz), (0.0, 0.0, 0.0)):
            self.assertAlmostEqual(got, expected)

    def test_rotation_about_z(self):
        obj = self.doc.addObject("Part::Feature", "P")
        obj.Placement = FreeCAD.Placement(
            FreeCAD.Vector(0, 0, 0),
            FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 90.0),
        )
        (x, y, z), (rx, ry, rz) = getObjectPyOptoolsPose(obj)
        self.assertAlmostEqual(abs(rz), math.pi / 2, places=6)

    def test_rotation_about_x(self):
        obj = self.doc.addObject("Part::Feature", "PX")
        obj.Placement = FreeCAD.Placement(
            FreeCAD.Vector(0, 0, 0),
            FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), 90.0),
        )
        _, (rx, ry, rz) = getObjectPyOptoolsPose(obj)
        self.assertAlmostEqual(abs(rx), math.pi / 2, places=6)

    def test_rotation_about_y(self):
        obj = self.doc.addObject("Part::Feature", "PY")
        obj.Placement = FreeCAD.Placement(
            FreeCAD.Vector(0, 0, 0),
            FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 90.0),
        )
        _, (rx, ry, rz) = getObjectPyOptoolsPose(obj)
        self.assertAlmostEqual(abs(ry), math.pi / 2, places=6)

    def test_composed_rotation_is_finite(self):
        # Composition order is convention-dependent; we only require the
        # round-trip through FreeCAD to be consistent: building the same
        # Placement twice must give the same pose.
        rot = FreeCAD.Rotation(30.0, 45.0, 60.0)
        poses = []
        for _ in range(2):
            obj = self.doc.addObject("Part::Feature", "PC")
            obj.Placement = FreeCAD.Placement(FreeCAD.Vector(1, 2, 3), rot)
            poses.append(getObjectPyOptoolsPose(obj))
        (p1, r1), (p2, r2) = poses
        for a, b in zip(p1 + p2, r1 + r2):
            self.assertTrue(math.isfinite(a) and math.isfinite(b))
        for a, b in zip(r1, r2):
            self.assertAlmostEqual(a, b, places=9)


class RayPropagation(PyOpToolsTestCaseNoDoc):
    """End-to-end ray propagation through a minimal system."""

    def test_minimal_system_propagates_rays(self):
        system, source = _build_system()
        system.ray_add(source)
        system.propagate()
        X, Y, optical_path = system["SEN"][0].get_optical_path_data()
        self.assertGreater(len(X), 0, "No rays reached the sensor")
        self.assertEqual(len(X), len(Y))
        self.assertEqual(len(X), len(optical_path))

    def test_sensor_spot_is_finite(self):
        system, source = _build_system()
        system.ray_add(source)
        system.propagate()
        X, Y, _ = system["SEN"][0].get_optical_path_data()
        for x, y in zip(X, Y):
            self.assertTrue(math.isfinite(x))
            self.assertTrue(math.isfinite(y))


class ForwardCompatibilityGuard(PyOpToolsTestCaseDoc):
    """The propagation guard is a no-op on a fresh document."""

    def test_fresh_document_has_no_forward_incompatible_objects(self):
        from freecad.pyoptools.pyOpToolsWB.propagate import (
            _has_forward_incompatible_objects,
        )

        self.assertFalse(_has_forward_incompatible_objects())


if __name__ == "__main__":
    unittest.main()
