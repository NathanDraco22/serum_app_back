---
type: doc
title: Reglas de Negocio — Turnos de Caja (CashShift) y Kardex Financiero
description: Gestión de turnos laborales por usuario ("la persona es la caja"), libro contable inmutable, control de arqueos y tratamiento de montos en centavos.
tags: [cash_shift, cash_register, kardex, transactions, finance, audit]
timestamp: 2026-10-03T09:00:00Z
---

# 💰 Turnos de Caja (`CashShift`) y Kardex Financiero

El módulo financiero garantiza la trazabilidad absoluta del flujo de dinero y la prevención de fraudes bajo la premisa de negocio: **"La persona es la caja"**. Los custodios (cajeros, químicos, recepcionistas) operan abriendo su propio turno de caja (`CashShift`), el cual encapsula sus cobros e historial contable individual y se audita mediante el libro inmutable de transacciones (`CashTransaction`).

---

## 1. Filosofía: "La Persona es la Caja"

1. **Apertura de Turno (`openShift`)**:
   - Cada operador que ingrese a registrar cobros abre su propio turno con un fondo inicial (`initialBalance` en centavos `int`).
   - El sistema valida que el usuario no tenga ya un turno en estado `"OPEN"`.
   - Se elimina la selección obligatoria de cajas fijas en el inicio de sesión.
2. **Operación Durante la Jornada**:
   - Cada cobro de orden médica genera una transacción en `CashTransaction` vinculada a su `shiftId` y `userId`.
   - El turno acumula atómicamente sus balances segmentados por método de pago (`cashBalance`, `cardBalance`, `transferBalance`, `totalBalance`).
3. **Cierre y Arqueo Individual (`closeShift`)**:
   - Al terminar su guardia o jornada laboral, el operador declara el efectivo contado físicamente (`declaredCash`).
   - El sistema calcula la diferencia automáticamente:
     $$\text{difference} = \text{declaredCash} - (\text{initialBalance} + \text{cashBalance})$$
   - El turno se sella con estado `"CLOSED"` y preserva el histórico completo de arqueos para auditoría gerencial sin modificar el documento del usuario.

---

## 2. Reglas Fundamentales de Persistencia Financiera

1. **Montos Siempre en Centavos (`int`)**:
   - Todo campo de precio, cobro, balance, fondo inicial, conteo físico o diferencia es un entero (`int`) que representa centavos (ej. \$150.50 MXN = `15050`).
   - Prohibido el uso de `float` para persistencia o cálculos acumulativos.
2. **Inmutabilidad Absoluta del Kardex (`CashTransaction`)**:
   - Una transacción guardada **nunca se edita ni se elimina**. No existen endpoints `PATCH` ni `DELETE` operativos para `CashTransaction`.
   - Las transacciones registran `shiftId`, `registerId` (opcional por compatibilidad), `branchId`, `flowType`, `subType`, `paymentMethod`, `amount`, `resultingBalance`, `concept`, `referenceId` y `performedBy`.
3. **El Saldo no se Edita a Mano**:
   - El balance del turno se calcula como resultado de las operaciones y se incrementa concurrentemente con operadores atómicos `$inc` en MongoDB.
   - Cada transacción estampa su `resultingBalance` (saldo total resultante inmediatamente posterior a la operación).

---

## 3. Tipos de Flujo y Subtipos de Transacción

| Subtipo | `flowType` | Impacto en Balance | Descripción |
| :--- | :--- | :--- | :--- |
| **`opening`** | `"in"` | Aumenta | Fondo inicial al abrir el turno. |
| **`closing`** | `"out"` | Disminuye (a cero) | Retiro total para el arqueo de cierre. |
| **`income`** | `"in"` | Aumenta | Entradas extraordinarias (ej. fondo adicional). Requiere `concept`. |
| **`withdrawal`** | `"out"` | Disminuye | Salidas de dinero (ej. gastos menores autorizados). Requiere `concept`. |
| **`payment`** | `"in"` | Aumenta | Cobro asociado a una orden médica (`referenceId = order_id`). |

---

## 4. Segmentación de Saldos por Método de Pago

La entidad `CashShift` mantiene el balance desglosado por:
- `cashBalance`: Efectivo físico cobrado durante el turno.
- `cardBalance`: Cobros mediante terminales bancarias.
- `transferBalance`: Cobros mediante transferencias electrónicas.
- `totalBalance`: Sumatoria total disponible en el turno (`initialBalance + cashBalance + cardBalance + transferBalance`).
