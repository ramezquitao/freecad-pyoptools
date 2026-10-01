#!/usr/bin/env bash
# Convenience wrapper to run the freecad-pyoptools test suites.
#
# Usage:
#   tests/run.sh unit                 # Level 1: pure Python (system python3)
#   tests/run.sh smoke                # Level 2: imports/versions (FreeCAD)
#   tests/run.sh integration          # Level 3: optical propagation (FreeCAD)
#   tests/run.sh gui                  # Level 4: real ViewObject tests (FreeCAD + display)
#   tests/run.sh all                  # Levels 1-3 (FreeCAD)
#   tests/run.sh native               # Levels 1-3 via FreeCAD's native 'Test' runner
#   tests/run.sh native-gui           # Level 4 via FreeCAD's native 'Test' runner
#
# The suites use the standard library `unittest` plus FreeCAD's `Test` runner,
# so no third-party test dependency is required inside FreeCAD.
#
# The `gui` suite needs a display. It runs under `xvfb-run` (which must be
# installed) so no window appears on your screen, mirroring FreeCAD's own GUI
# CI. Set PYOPTOOLS_TEST_USE_DISPLAY=1 to run on the current DISPLAY instead.
#
# Environment overrides:
#   FREECAD_APPIMAGE            path to the FreeCAD AppImage (default: ~/bin/FreeCAD_1.1.4-Linux-x86_64-py311.AppImage)
#   FREECAD_EXTRACTED           path to the extracted AppImage tree (default: tests/squashfs-root)
#   PYOPTOOLS_TEST_USE_DISPLAY  set to 1 to use the real DISPLAY instead of Xvfb
#   PYOPTOOLS_TEST_TIMEOUT      hard timeout in seconds for FreeCAD runs (default: 300)

set -euo pipefail

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$TESTS_DIR")"

FREECAD_APPIMAGE="${FREECAD_APPIMAGE:-$HOME/bin/FreeCAD_1.1.4-Linux-x86_64-py311.AppImage}"
FREECAD_EXTRACTED="${FREECAD_EXTRACTED:-$TESTS_DIR/squashfs-root}"
FREECADCMD="$FREECAD_EXTRACTED/usr/bin/freecadcmd"
FREECAD="$FREECAD_EXTRACTED/usr/bin/freecad"
XVFB_SCREEN="-screen 0 1024x768x24"

# Hard timeout so a hung FreeCAD interpreter cannot block CI forever.
TEST_TIMEOUT="${PYOPTOOLS_TEST_TIMEOUT:-300}"

SUITE="${1:-}"

if [[ -z "$SUITE" ]]; then
    echo "Usage: tests/run.sh <unit|smoke|integration|gui|all|native|native-gui>" >&2
    exit 2
fi

if [[ "$SUITE" == "unit" ]]; then
    cd "$REPO_ROOT"
    exec python3 -m unittest discover -s tests/unit -t "$REPO_ROOT" -v
fi

if [[ ! -x "$FREECADCMD" ]]; then
    echo "freecadcmd not found at: $FREECADCMD" >&2
    echo "Extract the AppImage first:" >&2
    echo "  cd \"$TESTS_DIR\" && \"$FREECAD_APPIMAGE\" --appimage-extract" >&2
    exit 3
fi

# Run a GUI command. Xvfb is used by default so tests never pop up windows on
# the developer's real screen. Set PYOPTOOLS_TEST_USE_DISPLAY=1 to use the
# current DISPLAY instead (useful for interactive debugging).
run_gui() {
    if [[ "${PYOPTOOLS_TEST_USE_DISPLAY:-0}" == "1" ]]; then
        if [[ -z "${DISPLAY:-}" ]]; then
            echo "PYOPTOOLS_TEST_USE_DISPLAY=1 but DISPLAY is not set." >&2
            exit 4
        fi
        exec "$@"
    fi
    if command -v xvfb-run >/dev/null 2>&1; then
        exec xvfb-run -a -s "$XVFB_SCREEN" "$@"
    fi
    echo "xvfb-run not found." >&2
    echo "Install Xvfb (e.g. 'sudo apt install xvfb'), or run with" >&2
    echo "PYOPTOOLS_TEST_USE_DISPLAY=1 to use the current display." >&2
    exit 4
}

case "$SUITE" in
    native)
        cd "$TESTS_DIR"
        exec timeout "$TEST_TIMEOUT" "$FREECADCMD" -P . -t TestPyOpTools
        ;;
    native-gui)
        if [[ ! -x "$FREECAD" ]]; then
            echo "freecad GUI binary not found at: $FREECAD" >&2
            exit 3
        fi
        cd "$TESTS_DIR"
        run_gui timeout "$TEST_TIMEOUT" "$FREECAD" -P . -t TestPyOpToolsGui
        ;;
    gui)
        # The GUI must be launched through FreeCAD's own Test runner (-t),
        # because `freecad -c` does not initialize the GUI command registry.
        if [[ ! -x "$FREECAD" ]]; then
            echo "freecad GUI binary not found at: $FREECAD" >&2
            exit 3
        fi
        cd "$TESTS_DIR"
        run_gui timeout "$TEST_TIMEOUT" "$FREECAD" -P . -t TestPyOpToolsGui
        ;;
    *)
        export PYOPTOOLS_TESTS_DIR="$TESTS_DIR"
        export PYOPTOOLS_TEST_SUITE="$SUITE"
        cd "$TESTS_DIR"
        exec timeout "$TEST_TIMEOUT" "$FREECADCMD" -c "exec(open('run_headless.py').read())"
        ;;
esac
