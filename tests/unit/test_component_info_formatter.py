"""Unit tests for ComponentInfoFormatter (pure Python, no FreeCAD required).

The formatter module has no FreeCAD dependencies, but importing it through the
package would trigger ``pyOpToolsWB/__init__.py`` (which imports FreeCADGui).
To keep Level 1 tests runnable with any CPython, the module is loaded directly
from its file path.
"""

import importlib.util
import os
import unittest

_MODULE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "freecad",
    "pyoptools",
    "pyOpToolsWB",
    "component_info_formatter.py",
)

_spec = importlib.util.spec_from_file_location(
    "component_info_formatter", _MODULE_PATH
)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

ComponentInfoFormatter = _module.ComponentInfoFormatter


class HumanReadable(unittest.TestCase):
    def setUp(self):
        self.f = ComponentInfoFormatter()

    def test_pascal_case(self):
        self.assertEqual(self.f._to_human_readable("SphericalLens"), "Spherical Lens")

    def test_snake_case(self):
        self.assertEqual(self.f._to_human_readable("material_l1"), "Material L1")

    def test_acronyms(self):
        self.assertEqual(self.f._to_human_readable("curvature_s1"), "Curvature S1")
        self.assertEqual(self.f._to_human_readable("na"), "NA")


class NumberFormatting(unittest.TestCase):
    def setUp(self):
        self.f = ComponentInfoFormatter()

    def test_scientific_for_tiny_values(self):
        self.assertEqual(self.f._format_number(0.0005), "5.00e-04")

    def test_trims_trailing_zeros(self):
        self.assertEqual(self.f._format_number(1.5), "1.5")
        self.assertEqual(self.f._format_number(12.0), "12")


class Units(unittest.TestCase):
    def setUp(self):
        self.f = ComponentInfoFormatter()

    def test_exact_match(self):
        self.assertEqual(self.f._get_unit("diameter"), "mm")
        self.assertEqual(self.f._get_unit("wavelength"), "nm")

    def test_pattern_match(self):
        self.assertEqual(self.f._get_unit("focal_length"), "mm")

    def test_unknown_returns_empty(self):
        self.assertEqual(self.f._get_unit("totally_unknown_field"), "")


class ValueFormatting(unittest.TestCase):
    def setUp(self):
        self.f = ComponentInfoFormatter()

    def test_bool_and_none(self):
        self.assertEqual(self.f._format_value("coating", True), "Yes")
        self.assertEqual(self.f._format_value("coating", False), "No")
        self.assertEqual(self.f._format_value("coating", None), "N/A")


class ComponentInfo(unittest.TestCase):
    def setUp(self):
        self.f = ComponentInfoFormatter()

    def test_header_and_part(self):
        out = self.f.format_component_info(
            "thorlabs",
            "LA1131-A",
            {"type": "SphericalLens", "diameter": 25.4, "focal_length": 100.0},
        )
        self.assertIn("Spherical Lens", out)
        self.assertIn("Part: LA1131-A", out)
        self.assertIn("Catalog: Thorlabs", out)

    def test_truncates_long_description(self):
        out = self.f.format_component_info(
            "c", "r", {"type": "Lens", "description": "x" * 100}
        )
        self.assertIn("...", out)
        self.assertNotIn("x" * 57, out)

    def test_availability_available(self):
        out = self.f.format_component_info("c", "r", {"type": "Lens"}, is_available=True)
        self.assertIn("Available", out)

    def test_availability_unavailable(self):
        out = self.f.format_component_info(
            "c", "r", {"type": "Lens"}, is_available=False, unavailable_reason="Glass missing"
        )
        self.assertIn("Unavailable", out)
        self.assertIn("Glass missing", out)

    def test_specifications_priority_order(self):
        lines = []
        self.f._format_specifications(lines, {"type": "Lens", "coating": "AR", "diameter": 10.0})
        text = "\n".join(lines)
        self.assertLess(text.index("Diameter"), text.index("Coating"))

    def test_specifications_skip_type(self):
        lines = []
        self.f._format_specifications(lines, {"type": "Lens", "diameter": 10.0})
        self.assertNotIn("Type", "\n".join(lines))


if __name__ == "__main__":
    unittest.main()
