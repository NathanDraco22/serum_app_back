---
type: doc
title: Reglas de Negocio — Caja Registradora y Kardex Financiero
description: Gestión de cajas físicas, libro contable inmutable, control de arqueos y tratamiento de montos en centavos.
tags: [cash_register, kardex, transactions, finance, audit]
timestamp: 2026-09-28T18:30:00Z
---

# 💰 Caja Registradora y Kardex Financiero

El módulo financiero garantiza la trazabilidad absoluta del flujo de dinero y la prevención de fraudes mediante dos entidades sincronizadas: `CashRegister` y `CashTransaction`.

---

## 1. Reglas Fundamentales de Persistencia Financiera

1. **Montos Siempre en Centavos (`int`)**:
   - Todo campo de precio, cobro, balance o transacción debe ser un número entero (`int`) que representa centavos (ej. \$150.50 MXN = `15050`).
   - El uso de `float` está estrictamente prohibido para evitar errores de redondeo de punto flotante.
2. **Inmutabilidad Absoluta del Kardex (`CashTransaction`)**:
   - Una transacción guardada **nunca se edita ni se elimina**. No existen endpoints `PATCH` ni `DELETE` para `CashTransaction`.
   - Cualquier error o ajuste debe registrarse mediante una nueva transacción correctiva de contrapartida.
3. **El Saldo no se Edita a Mano**:
   - El balance de la caja no se asigna arbitrariamente; es la reconstrucción de los eventos inmutables.
   - Cada transacción estampa su `resultingBalance` (saldo resultante inmediatamente posterior a la operación).

---

## 2. Tipos de Flujo y Subtipos de Transacción

| Subtipo | `flowType` | Impacto en Balance | Descripción |
| :--- | :--- | :--- | :--- |
| **`opening`** | `"in"` | Aumenta | Fondo inicial al abrir la caja. Marca `isOpen = True`. |
| **`closing`** | `"out"` | Disminuye (a cero) | Retiro total para el arqueo de cierre. Marca `isOpen = False`. |
| **`income`** | `"in"` | Aumenta | Entradas extraordinarias (ej. abonos, fondo adicional). Requiere `concept`. |
| **`withdrawal`** | `"out"` | Disminuye | Salidas de dinero (ej. pago a proveedores, gastos menores). Requiere `concept`. |
| **`payment`** | `"in"` | Aumenta | Cobro asociado a una orden médica (`referenceId = order_id`). |

---

## 3. Segmentación de Saldos por Método de Pago

La entidad `CashRegister` mantiene el balance desglosado por:
- `cashBalance`: Efectivo físico disponible.
- `cardBalance`: Cobros mediante terminales bancarias.
- `transferBalance`: Cobros mediante transferencias electrónicas.
- `totalBalance`: Sumatoria total (`cashBalance + cardBalance + transferBalance`).

Las transacciones de salida (`withdrawal`) validan que exista saldo suficiente en el método específico del cual se pretende retirar los fondos.
