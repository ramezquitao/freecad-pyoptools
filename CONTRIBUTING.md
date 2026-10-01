# Contributing to freecad-pyoptools

Thanks for your interest in improving the pyOpTools workbench. This guide covers
how to set up a development environment, run the test suite, and submit changes.

If you are an AI coding assistant, read [`AGENTS.md`](AGENTS.md) as well: it
lists project-specific decisions and pitfalls that are not obvious from the code.

## Prerequisites

- A working [FreeCAD](https://freecadweb.org/) (>= 1.0.0) with Python 3 support.
- [pyoptools](https://github.com/cihologramas/pyoptools) (>= 0.4.1) available to
  FreeCAD's Python interpreter.

## Development setup

Clone the repository into FreeCAD's `Mod` directory so FreeCAD loads the
workbench from your working copy:

```bash
git clone https://github.com/cihologramas/freecad-pyoptools.git \
  ~/.local/share/FreeCAD/Mod/pyOpToolsWorkbench
```

Then start FreeCAD and select the **pyOpTools** workbench.

There are no runtime Python dependencies to install: FreeCAD and pyoptools
provide everything. `requirements.txt` intentionally lists none.

## Running the tests

The test suite lives in `tests/` and has four levels. It uses the Python
standard library `unittest` plus FreeCAD's own `Test` runner, so **no
third-party test dependency is required**.

| Level | Suite | Needs FreeCAD? | Display? | Covers |
|-------|-------|----------------|----------|--------|
| 1 | `unit` | No (system `python3`) | No | Pure-Python logic |
| 2 | `smoke` | Yes (headless) | No | Module imports, `WBPart` versioning contract |
| 3 | `integration` | Yes (headless) | No | Materials, placement, ray propagation |
| 4 | `gui` | Yes (GUI) | Yes (Xvfb) | Real component creation, view providers, `pyoptools_repr` |

The convenience wrapper runs them:

```bash
tests/run.sh unit           # Level 1 (system python3)
tests/run.sh smoke          # Level 2 (FreeCAD, headless)
tests/run.sh integration    # Level 3 (FreeCAD, headless)
tests/run.sh gui            # Level 4 (FreeCAD GUI; uses xvfb-run if no DISPLAY)
tests/run.sh all            # Levels 1-3
```

See the **Testing** section of [`README.md`](README.md) for the one-time
AppImage extraction step and the environment variables
(`FREECAD_APPIMAGE`, `FREECAD_EXTRACTED`, `PYOPTOOLS_TEST_USE_DISPLAY`,
`PYOPTOOLS_TEST_TIMEOUT`).

**Always run the suite before opening a pull request.** For changes that touch
component code, run at least `tests/run.sh all` and `tests/run.sh gui`.

## Submitting changes

1. Fork the repository and create a topic branch
   (e.g. `fix/roundmirror-wedge-angle`).
2. Keep each commit focused on one logical change.
3. Make sure the test suite passes (see above).
4. Open a pull request against `master`, describing **what** changed and **why**.
   If your change affects component properties or versioning, say so explicitly.

## Style

- Follow the existing code style in `freecad/pyoptools/pyOpToolsWB/`.
- Prefer the conventions of the bundled FreeCAD workbenches (Draft, BIM) when
  in doubt.
- Keep user-facing strings and comments in English.

## License

By contributing you agree that your contributions are licensed under the
**GPL-3.0-or-later**, matching the project's [`LICENSE`](LICENSE).
