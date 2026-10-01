"""GUI tests: the Sensors and Light Sources dock panels.

These panels are the main GUI surface for enabling/disabling components. They
are the target of the panel-unification refactor (``REFACTOR_PLAN.md`` step
4.1), which extracts a shared ``ComponentListPanel`` base class. The tests here
pin the *observable behaviour* that the refactor must preserve:

* the per-panel filter (which ``ComponentType`` values appear in each table),
* the ``Enabled`` checkbox state reflected in the table,
* ``enable_all`` / ``disable_all`` / ``toggle`` driving ``obj.Enabled``,
* the light-source wavelength extraction (two property paths) and the
  wavelength-coloured icon generation.

They use the real panels against real document objects, so a regression in the
shared base class (wrong filter, lost selection, broken toggle) is caught.

Runs with the GUI FreeCAD binary, e.g.::

    xvfb-run -a -s "-screen 0 1024x768x24" freecad -P tests -t TestPyOpToolsGui
"""

import unittest

from freecad.pyoptools.pyOpToolsWB.lightsourcespanel import LightSourcesPanel
from freecad.pyoptools.pyOpToolsWB.rayspoint import InsertRPoint
from freecad.pyoptools.pyOpToolsWB.sensor import InsertSen
from freecad.pyoptools.pyOpToolsWB.sensorspanel import SensorsPanel
from tests.test_base_gui import PyOpToolsGuiTestCaseDoc


class SensorsPanelGui(PyOpToolsGuiTestCaseDoc):
    """SensorsPanel behaviour."""

    def setUp(self):
        super().setUp()
        self.panel = SensorsPanel()
        self.addCleanup(self.panel.close)

    def test_empty_document_lists_nothing(self):
        self.panel.refresh_sensors()
        self.assertEqual(self.panel.table.rowCount(), 0)
        self.assertEqual(self.panel.row_objects, [])

    def test_only_sensors_are_listed(self):
        InsertSen(10, 10, ID="SEN1")
        InsertRPoint(ID="RP1")  # a light source, must NOT appear here
        self.panel.refresh_sensors()
        self.assertEqual(self.panel.table.rowCount(), 1)
        self.assertEqual(len(self.panel.row_objects), 1)
        self.assertEqual(self.panel.row_objects[0].ComponentType, "Sensor")

    def test_enabled_state_is_reflected(self):
        sensor = InsertSen(10, 10, ID="SEN1")
        sensor.Enabled = False
        self.panel.refresh_sensors()
        checkbox = self.panel.table.cellWidget(0, 0).layout().itemAt(0).widget()
        self.assertFalse(checkbox.isChecked())

    def test_disable_all_then_enable_all(self):
        sensor_a = InsertSen(10, 10, ID="SEN_A")
        sensor_b = InsertSen(20, 20, ID="SEN_B")
        self.panel.refresh_sensors()

        self.panel.disable_all()
        self.assertFalse(sensor_a.Enabled)
        self.assertFalse(sensor_b.Enabled)

        self.panel.enable_all()
        self.assertTrue(sensor_a.Enabled)
        self.assertTrue(sensor_b.Enabled)

    def test_toggle_sensor(self):
        from PySide import QtCore

        sensor = InsertSen(10, 10, ID="SEN1")
        self.panel.toggle_sensor(sensor, QtCore.Qt.Unchecked.value)
        self.assertFalse(sensor.Enabled)
        self.panel.toggle_sensor(sensor, QtCore.Qt.Checked.value)
        self.assertTrue(sensor.Enabled)

    def test_object_name_is_stable(self):
        # FreeCAD restores the dock layout by objectName; the refactor must
        # keep these names intact (REFACTOR_PLAN step 4.1).
        self.assertEqual(self.panel.objectName(), "PyOpTools_SensorsPanel")


class LightSourcesPanelGui(PyOpToolsGuiTestCaseDoc):
    """LightSourcesPanel behaviour."""

    def setUp(self):
        super().setUp()
        self.panel = LightSourcesPanel()
        self.addCleanup(self.panel.close)

    def test_empty_document_lists_nothing(self):
        self.panel.refresh_sources()
        self.assertEqual(self.panel.table.rowCount(), 0)
        self.assertEqual(self.panel.row_objects, [])

    def test_only_light_sources_are_listed(self):
        InsertRPoint(ID="RP1")
        InsertSen(10, 10, ID="SEN1")  # a sensor, must NOT appear here
        self.panel.refresh_sources()
        self.assertEqual(self.panel.table.rowCount(), 1)
        self.assertEqual(len(self.panel.row_objects), 1)
        self.assertEqual(self.panel.row_objects[0].ComponentType, "RaysPoint")

    def test_disable_all_then_enable_all(self):
        source_a = InsertRPoint(ID="RP_A")
        source_b = InsertRPoint(ID="RP_B")
        self.panel.refresh_sources()

        self.panel.disable_all()
        self.assertFalse(source_a.Enabled)
        self.assertFalse(source_b.Enabled)

        self.panel.enable_all()
        self.assertTrue(source_a.Enabled)
        self.assertTrue(source_b.Enabled)

    def test_wavelength_from_point_source(self):
        source = InsertRPoint(wavelength=633, ID="RP1")
        # 633 nm -> 0.633 µm
        self.assertAlmostEqual(
            self.panel._get_wavelength_from_object(source), 0.633, places=6
        )

    def test_wavelength_default_when_no_property(self):
        # A sensor has neither `wl` nor `wavelength`; the helper must fall
        # back to the default 0.633 µm rather than raising.
        sensor = InsertSen(10, 10, ID="SEN1")
        self.assertAlmostEqual(
            self.panel._get_wavelength_from_object(sensor), 0.633, places=6
        )

    def test_wavelength_coloured_icon_is_generated(self):
        source = InsertRPoint(wavelength=633, ID="RP1")
        icon = self.panel._create_icon_for_object(source)
        self.assertFalse(icon.isNull())

    def test_object_name_is_stable(self):
        self.assertEqual(
            self.panel.objectName(), "PyOpTools_LightSourcesPanel"
        )


if __name__ == "__main__":
    unittest.main()
