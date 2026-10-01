# AGENTS.md — notes for AI coding assistants

Project-specific decisions and pitfalls that are **not** obvious from reading
the code. Human contributors should also read [`CONTRIBUTING.md`](CONTRIBUTING.md);
users should read [`README.md`](README.md).

## Testing

- **Runner:** `tests/run.sh <unit|smoke|integration|gui|all>`.
- **Do not add pytest, coverage, or any third-party test dependency.** The
  suite must keep running inside FreeCAD's bundled interpreter using the
  standard library `unittest` and FreeCAD's `Test` runner (the convention used
  by the official `TestDraft` / `TestDraftGui`).
- **Do not introduce fake/mock document objects (e.g. the former `FakeObj`).**
  All tests use real FreeCAD objects. A hand-written fake re-implements
  FreeCAD's property and `ViewObject` semantics and can silently pass while the
  real conversion is broken. This was a deliberate removal — do not bring it
  back to "make a test easier".
- **Component creation lives in `tests/gui/` on purpose** (`ViewObject` is
  `None` in `freecadcmd`). Do not move it to `smoke` until the `GuiUp`/
  `ViewObject` guards are added to production code (tracked in
  `REFACTOR_PLAN.md`, step 2.5).
- **`PropagatePart` is never instantiated in tests.** Its `__init__` calls
  `getActiveSystem()` and propagates rays immediately, showing Qt dialogs on
  failure. It is covered only by the versioning contract and
  `ForwardCompatibilityGuard`.
- **`pyoptools_repr` needs a resolvable material.** With empty `matcat`/
  `matref` it raises `KeyError: Material not found`. Use
  `matcat="Value", matref="1.5"` (the "Value" catalog returns the number).
- **`LensDataPart` requires an exact 6-tuple of lists**
  (`surfType, radius, thick, semid, matcat, matref`), and `Radius` is an
  `App::PropertyFloatList` (it rejects the string `"inf"`).

## Behaviour that is pinned on purpose

- **Transparency 30/50/90:** components are created at 50, disabling sets 90,
  re-enabling sets 30. The 30-vs-50 asymmetry is a suspected long-standing bug
  (issue #19) but it is the *current* behaviour and the GUI tests pin it
  deliberately. If you fix `WBPart.onChanged` (30 → 50), update
  `tests/gui/test_viewproviders.py` in the **same** commit.
- **`RaysPointPart.pyoptools_repr` ignores `Enabled`** (unlike `RaysParPart`
  and `RaysArrayPart`): a disabled point source still yields rays. This is
  pinned in `tests/gui/test_pyoptools_repr.py`. If you fix it, update that test
  in the same commit.

## Production code

- **Do not rename FreeCAD properties** (`Thk`, `D`, `matcat`, …) without
  writing a migration (`migrate_to_vN` + `ObjectVersion`). Renaming breaks
  existing `.FCStd` files.
- When adding a new `WBPart` subclass, define `CURRENT_PART_VERSION`; the base
  class enforces it.
- Prefer the headless-safe pattern used by the official workbenches:
  `if App.GuiUp and getattr(obj, "ViewObject", None):` instead of assuming the
  GUI exists.

## Living documents

- [`README.md`](README.md) — user-facing usage and testing setup.
- [`REFACTOR_PLAN.md`](REFACTOR_PLAN.md) — pending refactor work.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — contributor workflow.
