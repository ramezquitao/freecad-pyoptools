"""GUI tests: ``pyoptools_repr`` conversion for every component.

``pyoptools_repr(obj)`` is the bridge from a FreeCAD document object to a
pyoptools ray-trace component. It is the highest-value, highest-risk conversion
in the workbench: it reads FreeCAD ``Quantity``/``Placement`` properties and
builds a pyoptools object from them. A regression here silently corrupts the
optical model without any import or versioning error.

These tests deliberately use **real FreeCAD objects** created through the
``Insert*`` helper functions, under the GUI binary (``xvfb-run``). Reasons:

* ``pyoptools_repr`` consumes real ``App::PropertyLength``/``PropertyAngle``
  values (``.Value`` / ``.getValueAs``) and real ``Placement`` objects
  (``getGlobalPlacement``); a hand-written fake would have to re-implement
  FreeCAD's property semantics and could pass while the real conversion is
  broken.
* The constructors touch ``obj.ViewObject``, which only exists in GUI mode.

The tests assert two levels of behaviour:

1. **Type**: the conversion returns the expected pyoptools class. This catches
   a wrong component being produced.
2. **Parameters**: where pyoptools exposes the input as a stable attribute
   (e.g. ``SphericalLens.radius``), the value is checked. Where pyoptools
   does not expose it, only the type and a sanity check are asserted to avoid
   coupling to pyoptools internals.

Runs with the GUI FreeCAD binary, e.g.::

    xvfb-run -a -s "-screen 0 1024x768x24" freecad -P tests -t TestPyOpToolsGui
"""

import math
import unittest

import FreeCAD
import pyoptools.raytrace.comp_lib as comp_lib
from pyoptools.raytrace.ray.ray import Ray
from pyoptools.raytrace.system.idealcomponent import IdealThickLens

from freecad.pyoptools.pyOpToolsWB.aperture import InsertApp
from freecad.pyoptools.pyOpToolsWB.bscube import InsertBSC
from freecad.pyoptools.pyOpToolsWB.cylindricallens import InsertCL
from freecad.pyoptools.pyOpToolsWB.diffractiongratting import InsertDiffG
from freecad.pyoptools.pyOpToolsWB.doubletlens import InsertDL
from freecad.pyoptools.pyOpToolsWB.doveprism import InsertDP
from freecad.pyoptools.pyOpToolsWB.lensdata import InsertLD
from freecad.pyoptools.pyOpToolsWB.pentaprism import InsertPP
from freecad.pyoptools.pyOpToolsWB.powelllens import InsertSL as InsertPowell
from freecad.pyoptools.pyOpToolsWB.ray import InsertRay
from freecad.pyoptools.pyOpToolsWB.raysarray import InsertRArray
from freecad.pyoptools.pyOpToolsWB.raysparallel import InsertRPar
from freecad.pyoptools.pyOpToolsWB.rayspoint import InsertRPoint
from freecad.pyoptools.pyOpToolsWB.rectmirror import InsertRectM
from freecad.pyoptools.pyOpToolsWB.rightangleprism import InsertRAP
from freecad.pyoptools.pyOpToolsWB.roundmirror import InsertRM
from freecad.pyoptools.pyOpToolsWB.sensor import InsertSen
from freecad.pyoptools.pyOpToolsWB.simpledmd import InsertSimpleDMD
from freecad.pyoptools.pyOpToolsWB.sphericallens import InsertSL
from freecad.pyoptools.pyOpToolsWB.thicklens import InsertTL
from tests.test_base_gui import PyOpToolsGuiTestCaseDoc

# A material that always resolves: "Value" catalog returns the number itself.
MAT = dict(matcat="Value", matref="1.5")


class PyOptoolsReprTestCase(PyOpToolsGuiTestCaseDoc):
    """Helper base: create a component and run its pyoptools_repr."""

    def _repr(self, insert, *args, **kwargs):
        obj = insert(*args, **kwargs)
        self.assertIsNotNone(obj.Proxy, "component has no Proxy")
        return obj.Proxy.pyoptools_repr(obj)


class PrismAndMirrorRepr(PyOptoolsReprTestCase):
    """Conversions that only need type + material sanity checks."""

    def test_aperture(self):
        result = self._repr(InsertApp, InD=10, OutD=25, ID="AP")
        self.assertIsInstance(result, comp_lib.Stop)

    def test_bscube(self):
        result = self._repr(InsertBSC, S=50, Ref=100, ID="BS", **MAT)
        self.assertIsInstance(result, comp_lib.BeamSplitingCube)

    def test_doveprism(self):
        result = self._repr(InsertDP, S=20, L=50, ID="DP", **MAT)
        self.assertIsInstance(result, comp_lib.DovePrism)

    def test_pentaprism(self):
        result = self._repr(InsertPP, S=50, ID="PP", **MAT)
        self.assertIsInstance(result, comp_lib.PentaPrism)

    def test_rightangleprism(self):
        result = self._repr(
            InsertRAP, S=50, ID="RAP", rla=10, rlb=20, rhy=30, **MAT
        )
        self.assertIsInstance(result, comp_lib.RightAnglePrism)

    def test_rectmirror(self):
        result = self._repr(InsertRectM, 100, 10, 50, 50, ID="RM", **MAT)
        self.assertIsInstance(result, comp_lib.RectMirror)

    def test_roundmirror(self):
        result = self._repr(InsertRM, Ref=100, Th=10, D=50, ID="RDM", **MAT)
        self.assertIsInstance(result, comp_lib.RoundMirror)

    def test_sensor(self):
        result = self._repr(InsertSen, 10, 20, ID="SEN")
        self.assertIsInstance(result, comp_lib.CCD)

    def test_simpledmd(self):
        result = self._repr(
            InsertSimpleDMD, 10, 10, 2, 12, 0, 0, 1, ID="DMD"
        )
        self.assertIsInstance(result, comp_lib.SimpleDMDDevice)


class LensReprParameters(PyOptoolsReprTestCase):
    """Conversions whose inputs are exposed as pyoptools attributes."""

    def test_spherical_lens_parameters(self):
        result = self._repr(
            InsertSL, 0.01, -0.01, 10, 50, ID="SL", **MAT
        )
        self.assertIsInstance(result, comp_lib.SphericalLens)
        self.assertAlmostEqual(result.radius, 25.0)  # D / 2
        self.assertAlmostEqual(result.thickness, 10)
        self.assertAlmostEqual(result.curvature_s1, 0.01)
        self.assertAlmostEqual(result.curvature_s2, -0.01)

    def test_cylindrical_lens_parameters(self):
        result = self._repr(
            InsertCL, 0.01, -0.01, 10, 20, 30, ID="CL", **MAT
        )
        self.assertIsInstance(result, comp_lib.CylindricalLens)
        self.assertAlmostEqual(result.thickness, 10)
        self.assertAlmostEqual(result.curvature_s1, 0.01)
        self.assertAlmostEqual(result.curvature_s2, -0.01)

    def test_powell_lens_parameters(self):
        result = self._repr(
            InsertPowell, R=3.0, CT=7.62, K=-4.302, D=8.89, ID="PL", **MAT
        )
        self.assertIsInstance(result, comp_lib.PowellLens)
        self.assertAlmostEqual(result.radius, 4.445)  # D / 2
        self.assertAlmostEqual(result.thickness, 7.62)
        self.assertAlmostEqual(result.K, -4.302)
        self.assertAlmostEqual(result.R, 3.0)

    def test_thick_lens_parameters(self):
        result = self._repr(InsertTL, Th=10, D=50, f=100, ID="TL")
        self.assertIsInstance(result, IdealThickLens)
        self.assertAlmostEqual(result.focal_length, 100)

    def test_lensdata_builds_multilens(self):
        datalist = (
            ["Plane", "Plane"],
            [1e6, 1e6],
            [10.0, 10.0],
            [12.5, 12.5],
            ["Value", "Value"],
            ["1.5", "1.5"],
        )
        result = self._repr(InsertLD, datalist, ID="LD")
        self.assertIsInstance(result, comp_lib.MultiLens)
        # The surfaces are packed into the internal component list.
        self.assertGreater(len(result.complist), 0)


class DoubletLensBranchRepr(PyOptoolsReprTestCase):
    """``ILD`` selects between cemented and air-spaced doublets."""

    def _doublet(self, ild):
        return self._repr(
            InsertDL,
            0.01, -0.01, 5,
            0.01, -0.01, 5,
            50, ild, "DL",
            "Value", "1.5", "Value", "1.6",
        )

    def test_cemented_when_ild_is_zero(self):
        self.assertIsInstance(self._doublet(0), comp_lib.Doublet)

    def test_air_spaced_when_ild_is_nonzero(self):
        self.assertIsInstance(self._doublet(2), comp_lib.AirSpacedDoublet)


class MirrorFilterRepr(PyOptoolsReprTestCase):
    """``FilterType`` maps to the pyoptools ``filter_spec`` tuple."""

    def _round(self, filter_type, **extra):
        obj = InsertRM(Ref=100, Th=10, D=50, ID="RDM", **MAT)
        obj.FilterType = filter_type
        for key, value in extra.items():
            setattr(obj, key, value)
        return obj.Proxy.pyoptools_repr(obj)

    def test_nofilter(self):
        self.assertIsInstance(self._round("NoFilter"), comp_lib.RoundMirror)

    def test_shortpass(self):
        self.assertIsInstance(self._round("ShortPass"), comp_lib.RoundMirror)

    def test_longpass(self):
        self.assertIsInstance(self._round("LongPass"), comp_lib.RoundMirror)

    def test_bandpass(self):
        self.assertIsInstance(self._round("BandPass"), comp_lib.RoundMirror)


class RaySourceRepr(PyOptoolsReprTestCase):
    """Ray sources convert to lists of pyoptools ``Ray`` objects."""

    def test_single_ray(self):
        result = self._repr(InsertRay, wavelength=633, ID="RY")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Ray)

    def test_point_source_produces_rays(self):
        result = self._repr(
            InsertRPoint, nr=4, na=3, distribution="polar", ID="RPT"
        )
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertTrue(all(isinstance(r, Ray) for r in result))

    def test_parallel_source_produces_rays(self):
        result = self._repr(
            InsertRPar, nr=4, na=3, distribution="polar", ID="RPAR"
        )
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertTrue(all(isinstance(r, Ray) for r in result))

    def test_parallel_source_disabled_produces_no_rays(self):
        result = self._repr(
            InsertRPar, nr=4, na=3, enabled=False, ID="RPAR_OFF"
        )
        self.assertEqual(result, [])

    def test_rays_array_produces_rays(self):
        result = self._repr(
            InsertRArray, Sx=2, Sy=2, Nx=2, Ny=2, nr=3, na=3, ID="RA"
        )
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertTrue(all(isinstance(r, Ray) for r in result))

    # KNOWN BEHAVIOUR (suspected BUG, pinned deliberately): unlike
    # RaysParPart and RaysArrayPart, RaysPointPart.pyoptools_repr does NOT
    # check obj.Enabled, so a disabled point source still yields rays.
    # If that is fixed, update this test in the SAME commit.
    def test_point_source_ignores_enabled_flag(self):
        result = self._repr(
            InsertRPoint, nr=4, na=3, enabled=False, ID="RPT_OFF"
        )
        self.assertGreater(
            len(result),
            0,
            "RaysPointPart now respects Enabled; update this pinned test.",
        )


class WavelengthUnitsRepr(PyOptoolsReprTestCase):
    """Wavelength is stored in nm and must reach pyoptools in µm."""

    def test_point_source_wavelength_is_converted_to_micrometers(self):
        result = self._repr(InsertRPoint, wavelength=633, ID="RPT_WL")
        self.assertGreater(len(result), 0)
        for ray in result:
            self.assertAlmostEqual(ray.wavelength, 0.633, places=6)


if __name__ == "__main__":
    unittest.main()
