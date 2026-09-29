# AGENTS.md — Instrucciones Obligatorias para Agentes de IA (Backend)

Este archivo establece las directrices que **todo agente de IA o desarrollador DEBE cumplir estrictamente** antes de analizar, planificar o realizar cambios en el backend (`serum_app_back`).

---

## 🚨 Regla de Oro: Consulta Obligatoria de `project_index.md`

**Antes de proponer cualquier cambio de código, responder preguntas de arquitectura o modificar cualquier archivo en `serum_app_back`:**

1. **Consulta `project_index.md` como mapa rector**:
   Debes leer [project_index.md](project_index.md) para ubicar en qué capa y módulo se encuentra la funcionalidad requerida, cuáles son sus dependencias y qué reglas aplican.

2. **Verificación de Reglas de Negocio**:
   Antes de editar entidades o lógica transaccional, consulta la sección correspondiente en [reglas_negocio/](reglas_negocio/INDEX.md):
   - Si tocas órdenes o resultados: Lee [snapshot_y_ordenes.md](reglas_negocio/snapshot_y_ordenes.md).
   - Si tocas pruebas clínicas o perfiles: Lee [catalogo_lab_tests.md](reglas_negocio/catalogo_lab_tests.md).
   - Si tocas cajas, pagos o auditoría: Lee [caja_y_kardex.md](reglas_negocio/caja_y_kardex.md).
   - Si tocas presupuestos y prospectos: Lee [cotizaciones.md](reglas_negocio/cotizaciones.md).
   - Si tocas seguridad, usuarios o sesiones: Lee [autenticacion_y_roles.md](reglas_negocio/autenticacion_y_roles.md).

3. **Arquitectura y Desacoplamiento**:
   Revisa [arquitectura/capas_onion.md](arquitectura/capas_onion.md). **Jamás** lances excepciones HTTP (`HTTPException`) desde Repositorios o la capa `core/`. Todo error de dominio debe heredar de `BusinessException` / `DomainException` y registrarse en `regis_exception_handlers.py`.

---

## 🛠️ Normas de Trabajo con el CLI `onion`

- Para crear nuevos módulos o CRUDs en MongoDB, utiliza el CLI:
  ```bash
  onion crud-mongo <entity> --version v1
  ```
  *(El nombre de la entidad debe estar siempre en singular y minúsculas: ej. `sample`, `equipment`).*
- No crees la estructura base manualmente a fin de evitar inconsistencias en el nombrado de clases y archivos.

---

## 🧪 Verificación Posterior a Cambios de Código

Tras modificar cualquier archivo en `serum_app_back`, ejecuta siempre la suite de verificación:

1. **Importación y Sintaxis**:
   ```powershell
   $env:PYTHONPATH="app"; .venv\Scripts\python.exe -c "from app.main import app"
   ```
2. **Linter (`ruff`)**:
   ```powershell
   uv run ruff check
   ```
3. **Chequeo de Tipos (`ty`)**:
   ```powershell
   $env:PYTHONPATH="app"; uv run ty check
   ```
   *(El directorio `app/` debe retornar 0 diagnósticos).*
