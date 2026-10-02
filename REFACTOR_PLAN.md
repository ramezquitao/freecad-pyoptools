# Plan de Refactorización — freecad-pyoptools

> **Propósito:** mejorar la organización y calidad del código **sin alterar la funcionalidad actual**.
> **Estado:** Plan aprobado. Ejecución pendiente.
> **Fecha:** 2026-09-30 · **Última revisión:** 2026-10-01 (verificado contra código y suite de tests)
>
> **Red de seguridad:** el proyecto tiene una suite de tests automatizados en `tests/`
> (niveles `unit|smoke|integration|gui`, runner `tests/run.sh`). Aun así, cada cambio debe
> verificarse también manualmente en FreeCAD antes de commit: la suite cubre el contrato
> de los componentes y paneles, pero no todos los flujos visuales. Cada paso está diseñado
> para ser independiente y de bajo riesgo.

---

## Contexto del diagnóstico

El diagnóstico identificó los siguientes problemas (todos verificados contra el código):

1. **Código muerto:**
   - `freecad/pyoptools/pyOpToolsWB/optimize.py` — versión antigua de optimización, nunca importada (el paquete `optimize/` tiene precedencia en el import).
   - `freecad/pyoptools/pyOpToolsWB/wbutils.py` — contiene una `WipeMenu` vieja; nada lo importa.
   - `wbpart.py:238` — método `pyoptools_repr` referencia `self.pyOpToolsType`, atributo inexistente (**bug latente**: lanzaría `AttributeError` si se llama).
   - `lightsourcespanel.py:186` — `get_icon_for_type` marcado como legacy, no usado.

2. **Imports y patrones frágiles:**
   - Star imports: `optimize.py:4`, `propagate.py:5` (`from .wbcommand import *`).
   - `except:` desnudos: `wbcommand.py:159`, `lightsourcespanel.py:478,484`, `sensorspanel.py:352,358`.
   - `FreeCAD.ActiveDocument == None` en vez de `is None`: `wbcommand.py:113`, `propagate.py:82`.
   - `print()` de depuración mezclados con `FreeCAD.Console`: `merit_functions.py:130`, `pyoptoolshelpers.py:68,77`.
   - Re-imports dentro de funciones en `feedback.py:229-248` (ya importados arriba).

3. **Duplicación:**
   - Construcción de `Placement` repetida en 21 puntos (19 archivos con el bloque literal + 2 variantes; ver inventario completo en Paso 2.1) (`sphericallens.py:57-63`, `roundmirror.py:45-51`, `rayspoint.py:39-48`, ...).
   - Extracción de material desde el form repetida en todos los componentes con material.
   - `sensorspanel.py` y `lightsourcespanel.py` comparten ~70-75% de código (tabla, selección, enable/disable).
   - `EnableComponentsMenu`/`DisableComponentsMenu` en `utils/enable_disable.py` idénticos salvo el valor booleano.

4. **Fragilidad de instalación:**
   - `qthelpers.py:getUIFilePath` hardcodea `UserAppData/Mod/pyOpToolsWorkbench/...` — falla si la carpeta del Mod tiene otro nombre (el repo se llama `freecad-pyoptools`).

5. **Estructura:**
   - `__init__.py` (122 líneas): 25 bloques de import + `addCommand` intercalados.
   - `optimize_gui.py` (1034 líneas): mezcla worker, timers, pick observers, estilos, aceptación.
   - Nomenclatura inconsistente de propiedades: `sphericallens.py` usa `CenterThickness`/`Diameter`, `roundmirror.py` usa `Thk`/`D`/`matcat`/`matref`.

---

## Reglas de ejecución

1. **Un paso = un commit.** No mezclar pasos.
2. **Verificación manual en FreeCAD** tras cada paso (lista de chequeo incluida).
3. **No renombrar propiedades FreeCAD** (`Thk`, `D`, etc.) en esta fase — rompería archivos `.FCStd` existentes. La unificación de nombres queda **fuera de alcance** salvo que se escriban migraciones.
4. **No tocar el shim `pyOpToolsWB/`** de la raíz (es la capa de migración legacy).
5. Si un paso falla la verificación, revertir con `git checkout -- <archivo>` y re-evaluar.
6. **Correr la suite tras cada paso:** `tests/run.sh all` (headless) y `tests/run.sh gui` (Xvfb). Si un paso toca `wbpart.py`, versionado o migraciones, correr también `tests/run.sh smoke`.
7. **Si un paso altera un comportamiento fijado por tests** (ver `AGENTS.md`: transparencia 30/50/90, `RaysPointPart` ignora `Enabled`, `expectedFailure` del Paso 1.3a), actualizar el test **en el mismo commit**.

---

## Fase 1 — Limpieza segura (riesgo mínimo)

### Paso 1.1 — Eliminar `optimize.py` (código muerto)
- **Archivo:** `freecad/pyoptools/pyOpToolsWB/optimize.py`
- **Acción:** borrar el archivo.
- **Por qué es seguro:** `__init__.py:57` hace `from .optimize import OptimizeMenu`, que resuelve al paquete `optimize/` (los paquetes tienen precedencia sobre módulos homónimos). Verificado: nada importa `optimize.py` directamente.
- **Verificación:** activar el workbench → menú *Simulate → Optimize* abre el diálogo moderno (con barra de progreso y botón Accept). Si abre el diálogo viejo (un `QMessageBox` simple), revertir.

### Paso 1.2 — Eliminar `wbutils.py` (código muerto)
- **Archivo:** `freecad/pyoptools/pyOpToolsWB/wbutils.py`
- **Acción:** borrar el archivo.
- **Por qué es seguro:** `grep -r wbutils` no encuentra ningún import. `__init__.py:118` usa `from .utils import WipeMenu` (la versión nueva en `utils/wipe.py`).
- **Verificación:** comando *Simulate → Wipe* funciona y borra propagaciones.

### Paso 1.3 — Eliminar métodos/código muerto dentro de archivos vivos
- **`wbpart.py`:** corregir `pyoptools_repr` (línea 236-239) — reemplazar `self.pyOpToolsType` por `obj.ComponentType`. Es la corrección mínima del bug latente (no borrar el método: es el fallback documentado para subclases).
- **`lightsourcespanel.py`:** borrar `get_icon_for_type` (líneas 186-189, marcado como legacy no usado).
- **`placementWidget.py`:** quitar comentarios obsoletos (líneas 10, 51) sobre clases eliminadas.
- **Verificación:** el workbench carga sin errores en la consola de Python de FreeCAD; crear una lente esférica y una fuente de luz funcionan.
- **Test de seguridad (1.3a):** `tests/gui/test_component_creation.py::test_base_pyoptools_repr_does_not_raise` está marcado con `@unittest.expectedFailure` y falla hoy **precisamente** por el bug `self.pyOpToolsType`. Al aplicar el fix, **quitar el decorador en el mismo commit**: el test pasa a verificar el comportamiento corregido.

### Paso 1.4 — Arreglar `except:` desnudos y `== None`
- `wbcommand.py:113` → `is None`
- `wbcommand.py:159` → `except Exception:`
- `propagate.py:82` → `is None`
- `lightsourcespanel.py:478,484` → `except Exception:`
- `sensorspanel.py:352,358` → `except Exception:`
- **Verificación:** abrir/cerrar diálogos con ESC; cerrar los paneles dock; no deben aparecer trazas nuevas en consola.

### Paso 1.5 — Arreglar star import en `propagate.py`
- `propagate.py:5` → reemplazar `from .wbcommand import *` por **`from .wbpart import WBPart`** (import directo del módulo que define la clase; hoy el star import funciona solo porque `wbcommand.py:10` tiene un `from .wbpart import WBPart` **sin usar** que se re-exporta — ese import sin usar se elimina en el Paso 1.8, así que este paso debe ir primero o hacerse junto).
- De paso: eliminar el re-import local redundante de `propagate.py:19` (`from freecad.pyoptools.pyOpToolsWB.wbpart import WBPart` dentro de `_has_forward_incompatible_objects`).
- Los imports muertos restantes de `propagate.py` (`radians` en `:4`, `System` en `:9`, `parallel_propagate` en `:12`) se tratan en el Paso 1.8.
- **Verificación:** *Simulate → Propagate* funciona con una fuente + una lente; `tests/run.sh integration` (ejercita `ForwardCompatibilityGuard`, que importa `_has_forward_incompatible_objects` de este módulo).

### Paso 1.6 — Limpiar re-imports en `feedback.py`
- Quitar `import FreeCAD` / `import FreeCADGui` internos (líneas 229-248); usar los imports del tope del archivo.
- **Verificación:** provocar un error controlado (p.ej. insertar componente sin documento abierto) y confirmar que el diálogo de error sigue apareciendo.

### Paso 1.7 — Completar Version History en docstrings de componentes versionados
- **Contexto:** el contrato de versionado (`CURRENT_PART_VERSION` + migraciones) se introdujo en `b0050f4` y se extendió en `bb4e667` (WedgeAngle). Varios componentes tienen versiones > 0 sin su Version History documentado en el docstring de la clase, lo que rompe la trazabilidad del mecanismo de migración. Inventario real (verificado 2026-09-30 contra código e historial git):

| Clase | `CURRENT_PART_VERSION` | Version History en docstring | Acción |
|-------|------------------------|------------------------------|--------|
| `RoundMirrorPart` (`roundmirror.py:90-100`) | 2 | Solo V0 y V1 | **Añadir V2:** "Added `WedgeAngle` property (App::PropertyAngle). `migrate_to_v2` adds it with default 0.0 (parallel faces, original behavior preserved)." Referencia: `migrate_to_v2` en `roundmirror.py:310-319` y commit `bb4e667`. |
| `RectMirrorPart` (`rectmirror.py`) | 1 | V0, V1 completos | Ninguna ✔ |
| `SphericalLensPart` (`sphericallens.py:86-110`) | 1 | **Sección inexistente** | **Añadir sección completa:** V1 = "Renamed properties to descriptive names: `CS1`→`CurvatureFront`, `CS2`→`CurvatureBack`, `Thk`→`CenterThickness`, `D`→`Diameter`, `matcat`→`MaterialCatalog`, `matref`→`MaterialReference` (ver `migrate_to_v1`, `sphericallens.py:261`)." V0 = initial version con nombres cortos. |
| `SimpleDMDPart` (`simpledmd.py:131`) | 1 | **Sección inexistente** | **Añadir sección:** V1 = "Initial version. This component was versioned as v1 from its first commit (`eb89ff4`, which hardcoded `obj.ObjectVersion = 1` in the constructor; `b0050f4` later moved it to the formal `CURRENT_PART_VERSION` mechanism without schema change). **No v0 was ever committed**, so no saved documents can exist without `ObjectVersion`, and no `migrate_to_v1` is ever needed. When migrating to v2, only the v1→v2 transition needs handling (keep the `ObjectVersion < N` guard pattern for uniformity with other components). Also fix the misleading comment in `onDocumentRestored` (`simpledmd.py:305`): *"No migration needed for ObjectVersion=1 (initial version)"* → *"v1 is the initial version; add migrate_to_v2 here when CURRENT_PART_VERSION becomes 2."* |
| `WBPart` (`wbpart.py:97-106`) | 1 (base) | V0, V1 completos | Ninguna ✔ |
| Resto (17 clases, todas `= 0`) | 0 | ninguna | Opcional: añadir "Version 0: Initial version" por uniformidad. Decidir y aplicar a todas o a ninguna. |

- **Acción:** solo editar docstrings (y el comentario de `simpledmd.py:305` si aplica). **No tocar lógica ni migraciones.**
- **Verificación:** `tests/run.sh all` y `tests/run.sh gui` deben seguir en OK (los docstrings no afectan ejecución, pero confirma que no se tocó código por accidente); revisión visual de que cada `migrate_to_vN` tiene su entrada VN en el docstring.

### Paso 1.8 — Eliminar imports sin usar
- **Contexto:** inventario verificado a 2026-10-01 (cada uno comprobado con `rg` contra el cuerpo del archivo; los falsos positivos por re-export vía `__all__`/star import se descartaron). **Regla:** re-verificar cada import con `rg "simbolo" <archivo>` justo antes de borrarlo.
- **Lista (módulo → imports a eliminar):**
  - `propagate.py`: `radians` (`:4`), `System` (`:9`), `parallel_propagate` (`:12`) — ninguno usado (el re-import local de `WBPart` en `:19` se elimina en el Paso 1.5).
  - `wbcommand.py`: `QtGui` (`:8`; solo se usa `QtWidgets`) y `from .wbpart import WBPart` (`:10`, sin usar; eliminar **después** del Paso 1.5, que deja de depender de este re-export).
  - `thicklens.py`: `getMaterial` (`:8`), `comp_lib` (`:11`).
  - `lensdata.py`: `import Part` (`:10`), `matlib` (`:15`), `ICONPATH` (`:17`).
  - `pyopPlot.py`: `from distutils.version import LooseVersion as V` (`:28`) — **prioritario: `distutils` está eliminado en Python 3.12**; FreeCAD 1.1 aún usa py3.11, pero es una bomba de tiempo.
  - `about.py`: `import FreeCAD` (`:5`; solo se usa `FreeCADGui`).
  - `reports.py`: `from .propagate import PropagatePart` (`:7`).
  - `spotdiagram.py`: `from .propagate import PropagatePart` (`:18`).
  - `qthelpers.py`: `QtGui` (`:2`; solo se usan `QtCore`/`QtWidgets`).
  - Componentes (~18 archivos): `import FreeCADGui` sin usar en `bscube`, `cylindricallens`, `doveprism`, `doubletlens`, `diffractiongratting`, `pentaprism`, `powelllens`, `rightangleprism`, `roundmirror`, `sensor`, `sphericallens`, `rectmirror`, `raysarray`, `raysparallel`, `rayspoint`, `catalogcomponent`, `lensdata`, `aperture`. En `simpledmd.py:5` `FreeCADGui` solo aparece en comentarios (líneas 65-66) — eliminar el import y limpiar/actualizar los comentarios.
- **Casos a confirmar antes de tocar** (revisar el archivo en ese momento):
  - `placementWidget.py:81` — `import os` local dentro de una función; verificar si se usa después del import.
  - `pyoptoolshelpers.py:5` — `degrees` importado junto a `radians`; confirmar que no se usa.
- **No tocar:** los star imports se tratan en el Paso 1.5; los imports que existen para re-exportar (`utils/__init__.py`, `optimize/__init__.py`, `__init__.py` principal) son punto de entrada, no código muerto.
- **Red de seguridad:** `tests/smoke/test_imports.py` importa todos los módulos del paquete y fallará si se rompe un import.
- **Verificación:** `tests/run.sh all` en OK.

**Fin de Fase 1 — Checklist global (verificado 2026-10-01 en FreeCAD GUI):**
- [x] Workbench activa sin errores en consola.
- [x] Insertar: SphericalLens, RoundMirror, RaysPoint, Sensor.
- [x] Propagate genera rayos; Wipe los borra.
- [x] Optimize abre el diálogo moderno.
- [x] Paneles Light Sources / Sensors listan y habilitan/deshabilitan.
- [x] `tests/run.sh all` y `tests/run.sh gui` en OK (regla 6).

---

## Fase 2 — Extracción de helpers (riesgo bajo, refactor mecánico)

### Paso 2.1 — Helper para construir Placement desde el form
- **Nuevo:** función en `wbcommand.py` (o nuevo módulo `placehelpers.py`):
  `placement_from_form(form) -> FreeCAD.Placement` leyendo `Xpos/Ypos/Zpos/Xrot/Yrot/Zrot`.
- **Diseño en dos capas (para que sea testeable headless):**
  1. función pura `placement_from_values(x, y, z, rx, ry, rz) -> FreeCAD.Placement` (sin dependencia de GUI/widgets), y
  2. wrapper fino `placement_from_form(form)` que solo lee los widgets y delega en la pura.
- **Alcance real (verificado 2026-10-01):** el patrón `Matrix(); rotateX/Y/Z; move; Placement` se repite en **21 puntos**, no ~10: 19 archivos con el bloque literal (`sphericallens.py:62-63`, `roundmirror.py:50-51`, `rayspoint.py:47-48`, `raysparallel.py:47-48`, `raysarray.py:82-83`, `ray.py:44-45`, `bscube.py:46-47`, `aperture.py:41-42`, `doveprism.py:44-45`, `doubletlens.py:100-101`, `diffractiongratting.py:67-68`, `thicklens.py:56-57`, `powelllens.py:52-53`, `cylindricallens.py:50-51`, `rightangleprism.py:55-56`, `pentaprism.py:45-46`, `lensdata.py:125-126`, `sensor.py:37-38`, `rectmirror.py:50-51`) más 2 variantes equivalentes (`simpledmd.py:56-61` asigna sin variable intermedia, `catalogcomponent.py:666-669`).
- **Aplicar a:** los 21 puntos anteriores (todos los `accept()` de componentes).
- **⚠️ Cobertura de tests:** los tests de creación (`tests/gui/test_component_creation.py`) llaman a los `Insert*` directamente, **no** a los `accept()` de los diálogos, así que este refactor **no tiene red automática** salvo el test nuevo de abajo — la verificación manual es imprescindible.
- **⚠️ Cuidado:** algunos componentes leen los nombres de campos del `.ui` directamente (p.ej. `self.form.Xpos`). El helper debe operar sobre `self.form` y no cambiar nombres de widgets.
- **Test nuevo:** añadir en `tests/integration/` (headless, junto a `PlacementConversion` en `test_optical_system.py:68-123`) un caso que verifique `placement_from_values` contra placements conocidos (identidad, rotaciones no triviales, composición), de modo que el helper quede cubierto aunque los `accept()` no lo estén.
- **Verificación:** insertar 2-3 componentes con rotaciones/posiciones no triviales y confirmar en el editor de propiedades que `Placement` es idéntico al comportamiento anterior; `tests/run.sh integration` incluye el test nuevo.

### Paso 2.2 — Helper para extracción de material
- **Nuevo:** `material_from_form(form) -> (matcat, matref)` encapsulando el patrón `if Catalog == "Value" ... else ...`.
- **Diseño en dos capas** (igual que 2.1): resolución pura (`(catalog_value, reference) -> (matcat, matref)` sin tocar widgets) + wrapper fino sobre `form`.
- **Aplicar a:** todos los componentes que usan `materialWidget`.
- **Test nuevo:** en `tests/integration/`, reutilizando el patrón de `Materials` (`test_optical_system.py:55-65`): valor numérico (`"Value"/"1.5"`), referencia con coma, y catálogo real (`schott`/`N-BK7`) a través del helper.
- **Verificación:** insertar lente con material de catálogo y otra con valor numérico; propagar y comprobar refracción; `tests/run.sh integration` incluye el test nuevo.

### Paso 2.3 — Unificar `EnableComponentsMenu`/`DisableComponentsMenu`
- **Archivo:** `utils/enable_disable.py`
- **Acción:** clase base `_ToggleComponentsMenu` con atributo `target_state` (True/False); las dos clases públicas heredan y solo definen texto/icono/shortcut.
- **Verificación:** seleccionar componentes → Ctrl+Shift+E habilita, Ctrl+Shift+D deshabilita; transparencia cambia en vista 3D.

### Paso 2.4 — Unificar prints de depuración
- Reemplazar `print(...)` en `pyoptoolshelpers.py:68,77` y `merit_functions.py:130` por `FreeCAD.Console.PrintLog` (o eliminarlos si son solo de depuración — preferible `PrintLog` para no cambiar comportamiento visible).
- **Verificación:** propagar y confirmar que los mensajes aparecen en la vista de reporte con nivel Log.

### Paso 2.5 — Guardas `GuiUp`/`ViewObject` para creación headless (desbloquea tests)
- **Problema:** los constructores de componentes y `WBPart.onChanged` acceden a `obj.ViewObject.Transparency` sin comprobar que exista. En el intérprete de consola (`freecadcmd`) `obj.ViewObject` es `None`, así que **la creación de componentes no se puede testear headless**. Es la razón por la que `tests/gui/test_component_creation.py` (contrato de las partes) vive en la suite GUI bajo Xvfb en lugar de en `smoke`.
- **Inventario real (verificado 2026-10-01):** **63 accesos** a `ViewObject` sin guarda en producción; **no existe ni un uso de `App.GuiUp`/`FreeCAD.GuiUp`** en el código del proyecto. Agrupado:
  - 20 constructores `Insert*` con `myObj.ViewObject.Proxy = 0` (sphericallens, cylindricallens, roundmirror, rectmirror, rayspoint, raysparallel, raysarray, ray, bscube, aperture, doveprism, doubletlens, diffractiongratting, thicklens, powelllens, rightangleprism, pentaprism, lensdata, sensor, simpledmd).
  - `wbpart.py:232-234` (`onChanged` — transparencia 30/90).
  - `execute()`/`onChanged()` de ~20 partes (transparencia/color) — lista completa generable con el `rg` de abajo.
  - `propagate.py:107` (`myObj.ViewObject.Proxy` en `Activated`), `propagate.py:194` (`LineColorArray` en `execute` — **ojo: es código de datos que corre en recompute**, sin guarda explícita rompe headless, incluirlo sí o sí) y `propagate.py:210` (`obj.ViewObject.Proxy`).
- **Patrón oficial (Draft/BIM de FreeCAD):** nunca asumir que la GUI existe. Envolver todo acceso a vista con la guarda:
  ```python
  if App.GuiUp and getattr(obj, "ViewObject", None):
      obj.ViewObject.Transparency = 50
  ```
  y usar `getattr(obj, "ViewObject", None)` en lugar de `obj.ViewObject` cuando se lee. Ejemplos upstream: `Mod/Draft/draftobjects/dimension.py` (`if App.GuiUp and obj.ViewObject:`), `Mod/Draft/draftobjects/draft_annotation.py` (`vobj = getattr(obj, "ViewObject", None)`).
- **Cómo encontrarlos todos:**
  ```bash
  rg -n "obj\.ViewObject|myObj\.ViewObject" freecad/pyoptools/pyOpToolsWB/
  ```
- **Micro-limpieza del mismo paso:** `thicklens.py:135` y `:142` asignan `obj.ViewObject.Transparency = 50` dos veces en la misma función — deduplicar (verificar antes que ambas asignaciones están en la misma función y aplican el mismo valor). Nota: `optimize.py:25` (`filter(...)` sin `list()`) no requiere acción: muere con el Paso 1.1.
- **Riesgo:** bajo. En GUI el comportamiento es idéntico (la guarda es siempre verdadera); en consola simplemente se omite el ajuste visual. **No cambia ningún archivo `.FCStd`** (la transparencia es propiedad de vista, no de datos).
- **Beneficio:** al terminar, mover `tests/gui/test_component_creation.py` → `tests/smoke/test_component_creation.py` (headless, sin Xvfb, rápido), dejando en `gui` solo lo genuinamente visual (transparencia, colores, view providers). Alinea el proyecto con el estándar de los workbenches oficiales. Se mueven las **20 clases creables** de `PART_CASES` (`test_component_creation.py:68-102`); `PropagatePart` (la 21ª registrada en smoke) sigue **excluida a propósito** de la creación — su exclusión está documentada en el docstring del propio test (`:19-22`) y se mantiene en el traslado.
- **Verificación:**
  1. `freecadcmd -c "..."` crea cada componente sin error (sin Xvfb).
  2. `tests/run.sh smoke` incluye el contrato de las 20 clases creables y pasa headless.
  3. `tests/run.sh gui` sigue pasando (transparencia 50/90/30 intacta).
  4. Abrir FreeCAD con GUI y crear un componente: se ve igual que antes (misma transparencia/color).
- **Estado:** ⬜ pendiente — decidido el 2026-10-01: se hará **durante el refactor**, no ahora, para no mezclar un cambio de producción con la estabilización de la suite. Mientras tanto, la suite actual (con la creación en GUI) actúa como red de seguridad que garantiza que el refactor no rompe nada.

**Fin de Fase 2 — Checklist global:** igual que Fase 1 + componentes con material + `tests/run.sh all` y `tests/run.sh gui` en OK (regla 6).

---

## Fase 3 — Robustez de instalación

### Paso 3.1 — `getUIFilePath` relativo a `__file__`
- **Archivo:** `qthelpers.py:29-41`
- **Acción:** derivar la ruta de `GUI/` a partir de la ubicación del paquete:
  `os.path.join(os.path.dirname(os.path.dirname(__file__)), "GUI", targetfile)`
  (subir de `pyOpToolsWB/` a `pyoptools/` y entrar en `GUI/`).
- **⚠️ ANTES de este paso:** confirmar cómo está instalado el workbench (symlink en `Mod/`, `PYTHONPATH`, o copia). La ruta actual hardcodeada `Mod/pyOpToolsWorkbench` sugiere que existe una carpeta con ese nombre en alguna instalación.
- **Verificación:** que todos los diálogos `.ui` carguen (insertar cada tipo de componente al menos una vez).

---

## Fase 4 — Unificación de paneles (riesgo medio)

### Paso 4.1 — Clase base `ComponentListPanel`
- **Nuevo archivo:** `freecad/pyoptools/pyOpToolsWB/widgets/componentlistpanel.py`
- **Contenido:** la lógica común de `sensorspanel.py` y `lightsourcespanel.py`:
  - tabla (checkbox Enabled / Label / Notes),
  - observers de selección y documento,
  - `enable_all`/`disable_all`/`toggle`,
  - sincronización de selección bidireccional.
- **Parametrizar:** predicado de filtro (`component_filter: Callable[[obj], bool]`) y hook `get_icon(obj) -> QIcon` (vacío por defecto; `LightSourcesPanel` lo sobrescribe con la lógica de longitud de onda).
- **Subclases finales:**
  - `SensorsPanel(ComponentListPanel)` — filtro `ComponentType == "Sensor"`.
  - `LightSourcesPanel(ComponentListPanel)` — filtro `in ["RaysPoint","RaysPar","RaysArray","Ray"]` + iconos por longitud de onda (mover `_create_icon_for_object`, `_svg_to_icon`, `_get_wavelength_from_object`, `_icon_cache`).
- **⚠️ Mantener intactos:** `objectName` de los QDockWidget (`PyOpTools_LightSourcesPanel`, `PyOpTools_SensorsPanel`) — FreeCAD los usa para restaurar el layout.
- **Verificación:** ambos paneles aparecen tabbed al activar el workbench; crear/borrar/habilitar fuentes y sensores se refleja en las tablas; selección bidireccional funciona; iconos de color por longitud de onda siguen apareciendo en fuentes.
- **Tests de seguridad:** `tests/gui/test_panels.py` fija el comportamiento observable que el refactor debe preservar: filtro por `ComponentType`, estado `Enabled`, `enable_all`/`disable_all`/`toggle`, extracción de longitud de onda (dos rutas + default) y generación de icono. Correr `tests/run.sh gui` tras el paso.

---

## Fase 5 — Estructura (riesgo medio/alto, opcional)

### Paso 5.1 — Tabla de comandos en `__init__.py`
- Convertir los 25 bloques `import` + `addCommand` en una lista `COMMANDS = [...]` + bucle de registro.
- **Nota:** los imports seguirán existiendo (Python los necesita); solo se reorganiza la presentación. Riesgo bajo pero toca el punto de entrada.

### Paso 5.2 — Dividir `optimize_gui.py` (1034 líneas)
- Extraer:
  - `optimize/progress_display.py` — timers, `updateUINow`, `updateParameterDisplayNow`, labels de mérito.
  - `optimize/pickers.py` — `startElementPick`/`startSensorPick` y validadores (`isOpticalComponent`, `isSensor`).
- Dejar en `optimize_gui.py`: inicialización del form, `accept`, `onAcceptClicked`, señales del worker.
- **⚠️ Este es el refactor más invasivo.** Hacerlo solo si las Fases 1-4 están verificadas y hay tiempo para probar el flujo completo de optimización (incl. Stop, Accept, ESC, cerrar panel durante optimización).

---

## Fuera de alcance (registrado para futuro)

- **Unificar nomenclatura de propiedades** (`Thk`→`CenterThickness`, `D`→`Diameter`, `matcat`→`MaterialCatalog` en componentes que aún usan nombres cortos): requiere escribir migraciones con `ObjectVersion` por componente (el mecanismo ya existe: ver `sphericallens.py:migrate_to_v1` y `roundmirror.py:migrate_to_v1/v2`). Al hacerlo, cada migración nueva debe documentarse en el Version History del docstring de la clase (ver Paso 1.7). **Precondición de test:** hoy **ningún test invoca `migrate_to_vN`/`onDocumentRestored`** sobre un documento antiguo — la única cobertura de versionado es que los objetos nuevos nacen con `ObjectVersion == CURRENT_PART_VERSION` (`test_component_creation.py:122-124`). Antes de tocar nombres de propiedades, añadir un test que cree un objeto, degrade su `ObjectVersion` (o cargue un `.FCStd` viejo) y ejecute la migración.
- **Registro de migraciones declarativo** en `WBPart` (lista `(versión, función)` en vez de cadenas de `if` en `onDocumentRestored`). Misma precondición de test que el punto anterior.
- **Serialización de `PropagatePart.S`** (ver `propagate.py:164-174`, TODO existente) para que las propagaciones sobrevivan al guardar/recargar.
- **Hueco de cobertura conocido:** `DiffractionGrattingPart` no tiene test de `pyoptools_repr` en `tests/gui/test_pyoptools_repr.py` (las demás familias de componentes sí). Añadirlo al tocar ese componente o al ampliar la suite.
- **Tests automatizados:** implementados en `tests/` (ver README → Testing). Cuatro niveles (`unit`, `smoke`, `integration`, `gui`) con `unittest` y el runner `Test` de FreeCAD, siguiendo la convención de los workbenches oficiales (`TestDraft`/`TestDraftGui`). Los tests GUI corren con el binario `freecad` bajo Xvfb. Se pueden correr con `tests/run.sh` o `freecadcmd -P tests -t TestPyOpTools` / `freecad -P tests -t TestPyOpToolsGui`. **No se usan objetos falsos (`FakeObj`):** toda la suite trabaja con objetos FreeCAD reales. La creación/contrato de las 20 clases creables vive hoy en `tests/gui/` (bajo Xvfb) porque los constructores requieren `ViewObject`; el **Paso 2.5** la devolverá a `smoke` (headless) añadiendo guardas `GuiUp`/`ViewObject` en producción. `PropagatePart` (la 21ª clase) no se instancia en tests: se cubre por el contrato de versionado en smoke y `ForwardCompatibilityGuard`.
- **`.pyc`/`__pycache__`:** ya cubierto por `.gitignore` ✔ (los archivos en disco son locales y pueden borrarse con `find . -name __pycache__ -type d -exec rm -rf {} +`).

---

## Referencia rápida de comandos

```bash
# Buscar usos antes de borrar/renombrar algo
rg -n "nombre_simbolo" freecad/

# Verificar que un módulo muerto no se importa en ninguna parte
rg -n "wbutils|from .optimize import" freecad/ --type py

# Limpiar caché de Python tras cambios
find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
```

## Historial de ejecución

| Paso | Fecha | Resultado | Notas |
|------|-------|-----------|-------|
| 1.1  | 2026-10-01 | ✅ hecho | `optimize.py` eliminado. `tests/run.sh all` y `gui` en OK. Sin commit (a petición). |
| 1.2  | 2026-10-01 | ✅ hecho | `wbutils.py` eliminado. `tests/run.sh all` y `gui` en OK. Sin commit (a petición). |
| 1.3  | 2026-10-01 | ✅ hecho | `wbpart.py` usa `obj.ComponentType`; `get_icon_for_type` eliminado; comentarios legacy de `placementWidget.py` eliminados; `@expectedFailure` retirado de `test_base_pyoptools_repr_does_not_raise` (1.3a). `all`+`gui` OK. Sin commit. |
| 1.4  | 2026-10-01 | ✅ hecho | `== None`→`is None` (wbcommand, propagate); `except:`→`except Exception:` (wbcommand, lightsourcespanel, sensorspanel). `all`+`gui` OK. Sin commit. |
| 1.5  | 2026-10-01 | ✅ hecho | `from .wbcommand import *`→`from .wbpart import WBPart`; re-import local eliminado. `all`+`gui` OK. Sin commit. |
| 1.6  | 2026-10-01 | ✅ hecho | Re-imports internos de `feedback.py` eliminados; `import FreeCADGui` movido al tope. `all`+`gui` OK. Sin commit. |
| 1.7  | 2026-10-01 | ✅ hecho | Version History añadido: `RoundMirrorPart` V2, `SphericalLensPart` V1/V0, `SimpleDMDPart` V1; comentario de `simpledmd.py` corregido. Solo docstrings. `all`+`gui` OK. Sin commit. |
| 1.8  | 2026-10-01 | ✅ hecho | Imports sin usar eliminados (propagate, thicklens, lensdata, pyopPlot, about, reports, spotdiagram, qthelpers, pyoptoolshelpers, ~19 componentes). **Corrección al plan:** `wbcommand.py:10 from .wbpart import WBPart` NO es muerto — es re-export usado por ~21 componentes (`from .wbcommand import ... WBPart`); se restauró. `all`+`gui` OK. Sin commit. |
| 2.1  |       | ⬜ pendiente |       |
| 2.2  |       | ⬜ pendiente |       |
| 2.3  |       | ⬜ pendiente |       |
| 2.4  |       | ⬜ pendiente |       |
| 2.5  |       | ⬜ pendiente | Guardas `GuiUp`/`ViewObject`; mueve creación de componentes a `smoke` headless. Hacer DURANTE el refactor, con la suite actual como red de seguridad. |
| 3.1  |       | ⬜ pendiente | Confirmar método de instalación antes |
| 4.1  |       | ⬜ pendiente |       |
| 5.1  |       | ⬜ pendiente |       |
| 5.2  |       | ⬜ pendiente | Solo si hay tiempo para probar |
| Tests | 2026-09-30 | ✅ hecho | `unittest` + runner `Test` de FreeCAD (convención oficial). Suites `unit`/`smoke`/`integration` (headless) y `gui` (Xvfb, ViewObject real) en `tests/`; correr con `tests/run.sh`. Bug corregido en `component_info_formatter._format_value` (rama `bool` inalcanzable). |
| Revisión del plan | 2026-10-01 | ✅ hecho | Verificado contra código y suite: 1.5 corregido (import directo `.wbpart`, re-import local, dependencia con 1.8); 2.1 realzado a 21 puntos de duplicación; 2.5 con inventario de 63 accesos `ViewObject` y `propagate.py:194` explícito; "21 clases" aclarado (20 creables + PropagatePart excluida); añadido Paso 1.8 (imports sin usar); tests nuevos para helpers 2.1/2.2; reglas 6-7 (suite tras cada paso); huecos de cobertura registrados (migraciones, DiffractionGratting). |
