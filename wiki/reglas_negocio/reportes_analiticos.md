---
type: doc
title: Backend — Módulo de Reportes Analíticos y Pipelines de Agregación
description: Especificación de las reglas analíticas, pipelines de agregación en MongoDB, contratos de endpoints y arquitectura en generators/.
tags: [backend, reports, aggregation, mongodb, pipelines, analytics]
timestamp: 2026-10-04T15:30:00Z
---

# 📊 Módulo de Reportes Analíticos (Backend)

El módulo de reportes analíticos del servidor provee 5 endpoints de alto rendimiento construidos bajo agregaciones nativas de MongoDB (`Motor` async). Estos endpoints computan métricas financieras, comerciales, de demanda clínica y de auditoría de caja sin requerir procesamiento pesado en memoria en la capa de la aplicación.

Prefijo base: `/api/v1/reports/`

---

## 🏛️ 1. Arquitectura y Delegación en `generators/`

Para evitar concentración de responsabilidades en un único archivo monolítico, la lógica se estructuró siguiendo el patrón de delegación modular del proyecto:

```
app/
├── api/v1/reports/
│   ├── reports_router.py          # Enrutador FastAPI con validaciones de Query params
│   ├── reports_controller.py      # Controlador asíncrono
│   └── reports_schemas.py         # DTOs y modelos de respuesta Pydantic
└── core/reports/
    ├── reports_manager.py         # Fachada orquestadora liviana (~65 líneas)
    ├── reports_pipelines.py       # Pipelines nativos de agregación de MongoDB ($match, $group, $lookup, $sort)
    └── generators/                # Generadores independientes por reporte
        ├── reports_helpers.py             # Mapeos en memoria de sucursales y usuarios
        ├── generate_financial_report.py
        ├── generate_top_doctors_report.py
        ├── generate_lab_tests_volume_report.py
        ├── generate_pending_balances_report.py
        └── generate_shifts_audit_report.py
```

---

## 📑 2. Contrato y Reglas de los 5 Endpoints

Todos los endpoints requieren los siguientes parámetros estándar de consulta:
- `start_date: int` (Timestamp Unix en milisegundos).
- `end_date: int` (Timestamp Unix en milisegundos).
- `branch_id: str | None = None` (Opcional: si se omite, computa el consolidado global y desglosa por sucursal en `byBranch`).

### 1. `GET /api/v1/reports/financial`
* **Propósito**: Contraste entre la facturación devengada en órdenes clínicas y el recaudo efectivo real en caja registrado en el Kardex (`CashTransaction`).
* **Métricas**:
  - `totalBilled`: Suma de `totalPrice` de órdenes emitidas en el rango.
  - `totalCollected`: Cobranza real de transacciones de tipo `order_payment` en el Kardex.
  - `pendingReceivables`: Saldo insoluto (`totalPrice - paidAmount`).
  - `paymentMethods`: Desglose en `cash`, `card` y `transfer`.
  - `ordersCount` y `transactionsCount`.

### 2. `GET /api/v1/reports/top-doctors`
* **Parámetros Adicionales**: `limit: int = 10` (1 a 100).
* **Propósito**: Ranking de médicos prescriptores que derivan pacientes al laboratorio.
* **Regla de Negocio**: Si una orden médica no tiene médico asignado (`doctorId = null` o vacío), el pipeline clasifica automáticamente la orden bajo `"Sin Médico"`, permitiendo medir qué porcentaje de la demanda es espontánea vs referenciada.

### 3. `GET /api/v1/reports/lab-tests-volume`
* **Parámetros Adicionales**: `source: str = "orders"` (admite `"orders"` o `"quotations"`), `limit: int = 10`.
* **Propósito**: Medir la demanda y rotación de pruebas clínicas individuales y paquetes (`isPack: true/false`).
* **Regla de Negocio**: Al consultar `source="quotations"`, evalúa los presupuestos emitidos para medir interés comercial y demanda proyectada.

### 4. `GET /api/v1/reports/pending-balances`
* **Propósito**: Control de cuentas por cobrar y morosidad de pacientes.
* **Pipeline**: Filtra órdenes donde `pendingAmount > 0` (`totalPrice > paidAmount`) y `isCancelled != True`.
* **Cálculo de Antigüedad**: Calcula `daysPending` en base al timestamp de creación de la orden (`(now_ms - orderDate) / (1000 * 60 * 60 * 24)`).

### 5. `GET /api/v1/reports/shifts-audit`
* **Parámetros Adicionales**: `only_discrepancies: bool = false`.
* **Propósito**: Auditoría de turnos cerrados de caja (`CashShift`).
* **Métricas**: Control de arqueo comparando el saldo calculado por el sistema (`cashBalance`) con el efectivo físico declarado por el cajero (`declaredCash`).
* **Diferencia**: `difference = declaredCash - cashBalance` (positivo: sobrante en caja; negativo: faltante).

---

## 🪙 3. Convención Monetaria y Timestamps

1. **Centavos Enteros (`int`)**: Toda cifra monetaria se almacena y transporta como entero en centavos (`10000 = $100.00`). Nunca se emplean flotantes en la capa de persistencia ni en las agregaciones.
2. **Timestamps en Milisegundos**: Las comparaciones de fechas en `$match` se ejecutan sobre enteros en milisegundos (`createdAt >= start_date` y `createdAt <= end_date`).
