# freecad-pyoptools

Workbench to integrate pyoptools with freecad, that means basically optics ray tracing capabilities for FreeCAD.

## Prerequisite

It requires a working [FreeCAD](https://freecadweb.org/) with python3 support,  and [pyoptools](https://github.com/cihologramas/pyoptools) 
installation for python3.

## Linux Installation

Clone directly the git repository into the Mod dir of FreeCAD. This usually
means cloning the repo into ~/.local/share/FreeCAD/Mod directory.

After that you just select the "pyOpTools" workbench in FreeCAD in the usual way. As seen in the following screenshot
![image](https://raw.githubusercontent.com/cihologramas/freecad-pyoptools/master/media/PyOpTools-workbench-selection.png)

## Development

For information on testing local pyoptools library changes in FreeCAD, see the [Development Guide](docs/DEVELOPMENT.md).

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, the test suite,
and the pull-request workflow. AI coding assistants should also read
[AGENTS.md](AGENTS.md).

## Testing

The test suite has four levels (see `tests/`):

| Level | Suite | Needs FreeCAD? | Display? | What it covers |
|-------|-------|----------------|----------|----------------|
| 1 | `unit` | No (system `python3`) | No | Pure-Python logic (e.g. `ComponentInfoFormatter`) |
| 2 | `smoke` | Yes (headless) | No | Imports of every module, `WBPart` versioning contract |
| 3 | `integration` | Yes (headless) | No | Material resolution, Placement conversion, ray propagation |
| 4 | `gui` | Yes (GUI) | Yes (Xvfb) | Real component creation + versioning contract, real `ViewObject` (transparency, shape colours), `pyoptools_repr` conversion for every component, Sensors/Light Sources panels |

Following the FreeCAD convention (as used by the bundled workbenches, e.g.
Draft, with `TestDraft` / `TestDraftGui`), the tests use the standard library
`unittest` and FreeCAD's own `Test` runner. **No third-party test dependency is
required inside FreeCAD.**

Levels 2 and 3 run inside FreeCAD's console interpreter (`freecadcmd`) and need
no display. Level 4 runs the full `FreeCAD` binary under a display (Xvfb in
headless environments), mirroring FreeCAD's own GUI CI.

### One-time setup

Extract the FreeCAD AppImage to get `freecadcmd` and `freecad`:

```bash
cd tests
~/bin/FreeCAD_1.1.4-Linux-x86_64-py311.AppImage --appimage-extract
```

Override the AppImage location with `FREECAD_APPIMAGE` if it lives elsewhere.

Test-runner environment variables:

```
FREECAD_APPIMAGE            path to the FreeCAD AppImage
FREECAD_EXTRACTED           path to the extracted AppImage tree (default: tests/squashfs-root)
PYOPTOOLS_TEST_USE_DISPLAY  set to 1 to use the real DISPLAY instead of Xvfb
PYOPTOOLS_TEST_TIMEOUT      hard timeout in seconds for FreeCAD runs (default: 300)
```

For the `gui` suite, install a virtual display server if you don't have one:

```bash
sudo apt install xvfb
```

### Running the tests

```bash
tests/run.sh unit           # Level 1 (system python3)
tests/run.sh smoke          # Level 2 (FreeCAD, headless)
tests/run.sh integration    # Level 3 (FreeCAD, headless)
tests/run.sh gui            # Level 4 (FreeCAD GUI; uses xvfb-run if no DISPLAY)
tests/run.sh all            # Levels 1-3 (FreeCAD)
tests/run.sh native         # Levels 1-3 via FreeCAD's native `Test` runner
tests/run.sh native-gui     # Level 4 via FreeCAD's native `Test` runner
```

You can also use FreeCAD's native test runner directly, exactly like the
bundled workbenches do:

```bash
cd tests
./squashfs-root/usr/bin/freecadcmd -P . -t TestPyOpTools
xvfb-run -a -s "-screen 0 1024x768x24" \
    ./squashfs-root/usr/bin/freecad -P . -t TestPyOpToolsGui
```

or from inside FreeCAD's Python console:

```python
import sys; sys.path.insert(0, "path/to/tests")
import Test, TestPyOpTools          # non-GUI suites
Test.runTestsFromModule(TestPyOpTools)
import TestPyOpToolsGui             # GUI suite (needs a display)
Test.runTestsFromModule(TestPyOpToolsGui)
```

The headless runner (`tests/run_headless.py`) makes the repository source tree
take precedence over the copy installed in FreeCAD's `Mod/` directory, so the
tests always run against the code in this repository.

### Notes on GUI tests

FreeCAD's console interpreter has no `ViewObject` (a GUI-only concept), so
component creation cannot run headless. Level 4 therefore runs the real GUI and
creates **real** objects with real view providers: it checks the `WBPart`
contract (proxy, `ComponentType`, versions, base properties) for every
component, asserts on `Transparency`, `ShapeColor` and the visual response to
the `Enabled` property, and exercises `pyoptools_repr` (the FreeCAD to pyoptools
conversion) for every component. There are no fake document objects anywhere in
the suite: everything is tested against real FreeCAD objects.

The `gui` suite is launched with FreeCAD's own `Test` runner (`-t`) rather than
`-c`, because only the full GUI startup registers the command registry and
creates view objects. It always runs under `xvfb-run` (a virtual display), so no
window pops up on your screen. To run it on your real display instead (e.g. for
interactive debugging):

```bash
PYOPTOOLS_TEST_USE_DISPLAY=1 tests/run.sh gui
```




## Small Instructions

Please have in mind that this is a work in progress, so it may change radically some day, and your simulations may not run anymore.

The idea behind this workbench is to be able to simulate (by raytracing) optical systems. To do so, you need to build the optical system you want to simulate.

To build the system first change to the pyOpTools workbench. You will find 2 new menus:

* Add Component
* Simulate

The first menu allows you to add optical components to your system. Each component creates a dialog
that can be used to position it, and also to adjust it's parameters such as focal length (for example). There are also some kind of ray sources that must be added to perform a simulation (point source, parallel source). After all the components and ray sources are located in the system, press simulate-> propagate, and the ray tracing simulation will be ran.








