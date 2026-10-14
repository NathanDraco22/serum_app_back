---
type: doc
title: Reglas de Negocio — Catálogo Unificado de Pruebas (LabTest) y Packs
description: Modelo unificado de pruebas clínicas individuales, perfiles/packs compuestos, tipos de datos y rangos demográficos.
tags: [lab_tests, packs, catalog, clinical, reference_values]
timestamp: 2026-09-28T18:30:00Z
---

# 🧪 Catálogo Unificado de LabTests y Packs

El catálogo de estudios médicos se administra a través de una entidad unificada: `LabTest` (colección `lab_tests`), eliminando la duplicidad conceptual entre exámenes y pruebas atómicas.

---

## 1. Modalidades de LabTest

### A. Prueba Individual (`isPack: false`)
Representa un análisis clínico específico (ej. *Glucosa*, *Colesterol Total*, *Hemoglobina*, *Prueba de Embarazo*).
- **Precio individual (`salePrice`)**: Entero en centavos (Nivel 1 / Regular).
- **Precio preferencial (`salePrice2`)**: Entero en centavos (Nivel 2 / Convenio o especial).
- **Categoría comercial (`commercialCategory`)**: Clasificación analítica (ej. *Química Clínica*, *Hematología*).
- **Tipo de dato (`dataType`)**:
  - `numeric`: Medición cuantitativa con unidad de medida (`mg/dL`, `g/dL`, etc.) y rangos demográficos (`referenceValues`).
  - `boolean` / `qualitative`: Resultado dicotómico o de opciones cerradas (ej. `["Negativo", "Positivo"]`, `["No Reactivo", "Reactivo"]`).
  - `text`: Observación descriptiva o narrativa libre.
- **Rangos de referencia (`referenceValues`)**: Arreglo de rangos que dependen de la demografía del paciente (`patientType`, `gender`, `minAgeDays`, `maxAgeDays`, `minValue`, `maxValue`).

### B. Pack o Perfil Comercial (`isPack: true`)
Representa una oferta o combo comercial que agrupa múltiples pruebas individuales (ej. *Perfil Lipídico*, *Perfil Hepático*, *Checkup General*).
- **Precio de paquete (`salePrice`)**: Precio especial del combo en centavos (Nivel 1).
- **Precio de paquete preferencial (`salePrice2`)**: Precio de combo preferencial en centavos (Nivel 2).
- **Pruebas contenidas (`childTestIds`)**: Lista de IDs de las pruebas individuales que componen el paquete.
- **Venta flexible**: Al crear cotizaciones u órdenes, se puede vender el pack completo por su precio de combo o seleccionar únicamente pruebas individuales facturando solo las pruebas elegidas.

---

## 2. Expansión Automática en Órdenes Médicas

Cuando una orden incluye un Pack (`isPack: true`), el backend expande automáticamente sus `childTestIds` en la lista plana de `results` (`OrderTestResult`) de la orden, garantizando que el personal técnico tenga una fila de captura individual para cada análisis constituyente del perfil.

---

## 3. Cuentas Comerciales y Precios por Sucursal (`LabTestAccount`)

Las pruebas y packs médicos pertenecen a un catálogo clínico maestro (`lab_tests`). La información comercial y de precios se gestiona de forma desacoplada por cada sede mediante la colección `lab_test_accounts`:

- **Subdocumento `commercial`**:
  - `salePrice: int`: Precio regular (Nivel 1) en centavos para la sucursal.
  - `salePrice2: int`: Precio preferencial (Nivel 2) en centavos para la sucursal.
  - `costPrice: int`: Costo operativo/insumos del estudio en centavos.
  - `currency: str`: Divisa (`"USD"` por defecto).
- **Creación Transaccional en Core (`LabTestsManager`)**:
  - Al dar de alta un `LabTest` indicando `branchId`, se inserta la prueba en `lab_tests` y su `LabTestAccount` en la sucursal de origen con los precios provistos.
  - Automáticamente, se aprovisionan en lote los `LabTestAccount` para todas las demás sucursales activas con valores en `0`.
- **Aprovisionamiento de Nuevas Sedes**:
  - Cuando se da de alta una nueva sucursal (`POST /branches`), el sistema genera en lote las cuentas con precio `0` para todas las pruebas activas existentes.
- **Resolución Contextual en el POS**:
  - Los endpoints de consulta `GET /lab_tests?branch_id=...` y `GET /lab_tests/search/...` ejecutan un pipeline de agregación con `$lookup` hacia `lab_test_accounts`, proyectando el precio correspondiente a la sucursal activa en tiempo de ejecución.

