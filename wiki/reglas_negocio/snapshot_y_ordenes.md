---
type: doc
title: Reglas de Negocio — Snapshots y Ciclo de Vida de Órdenes
description: Justificación médica y técnica de los snapshots inmutables en órdenes y captura de resultados clínicos.
tags: [orders, snapshot, business_rules, results, medical]
timestamp: 2026-09-28T18:30:00Z
---

# 📋 Snapshots y Ciclo de Vida de Órdenes

## 1. El Concepto de Snapshot (Datos Congelados)

En un laboratorio clínico, la persistencia de datos **no puede depender de relaciones dinámicas tradicionales ni joins en runtime**. La información médica y financiera generada hoy debe ser **inmutable ante cambios futuros en los catálogos maestros**.

### ¿Por qué congelar datos físicamente en la Orden?

1. **Historial Clínico Inmutable**: La edad y el sexo del paciente al momento de la toma de muestra deben quedar congelados, pues de ellos dependen las interpretaciones médicas y rangos normales. Si un paciente actualiza sus datos años después en el catálogo, su historial médico pasado no debe modificarse.
2. **Rangos de Referencia Calibrados**: Si el laboratorio adquiere nueva maquinaria o reactivos y actualiza los rangos de normalidad (ej. glucosa de 70-100 a 74-106 mg/dL), las órdenes emitidas previamente deben seguir mostrando los rangos que estaban vigentes en la fecha del examen.
3. **Integridad Financiera**: Los precios del catálogo cambian con el tiempo. El precio efectivamente cobrado (`salePriceApplied`) debe congelarse en la orden para que un arqueo de caja de meses pasados jamás descuadre. Además, se congela el nivel de precio seleccionado (`priceLevel`: 1 para `salePrice` o 2 para `salePrice2`) como metadato de auditoría comercial.
4. **Alto Desempeño en Horas Pico**: Al almacenar todo en un solo documento MongoDB, se evitan `lookup`/joins complejos, garantizando consultas ultrarrápidas al emitir resultados o reportes.

---

## 2. Máquina de Estados de la Orden

Una orden médica transita por los siguientes estados:

```
[ pending / partiallyPaid ]
            ↓
       [ paid ]
            ↓
    [ in_process ]  (Bioanalista capturando resultados)
            ↓
     [ completed ]  (Resultados ingresados y verificados)
            ↓
     [ published ]  (Resultados entregados o disponibles para consulta)
```

---

## 3. Captura y Evaluación Automática de Resultados

Cuando se crea la orden:
1. Se clonan las estructuras de parámetros de cada `LabTest` individual (o de las pruebas hijas de un Pack) en el arreglo `results: list[OrderTestResult]`.
2. El bioanalista ingresa el valor en `resultValue`.
3. El sistema compara automáticamente el valor ingresado contra el rango de referencia congelado en la orden (`minValue` y `maxValue` para datos numéricos; `expectedQualitativeValue` para booleanos) y asigna el flag médico:
   - `NORMAL`: Dentro del rango de referencia.
   - `HIGH` / `LOW`: Por encima o por debajo de los límites.
   - `ABNORMAL`: En pruebas cualitativas donde el resultado difiere del esperado.

---

## 4. Modificación Arbitraria de Precios y Bloqueo de Órdenes (`isBlocked`)

Para mantener la flexibilidad comercial en ventanilla sin vulnerar el control financiero:

1. **Auditoría de Precios Originales (`originalPrice`)**:
   - Cada ítem de la orden (`OrderItem`) congela el precio original del catálogo (`originalPrice`, correspondiente a Precio 1 en centavos) junto con el precio cobrado (`salePriceApplied`).
2. **Detección Automática de Discrepancia**:
   - Si al emitir la orden cualquier ítem tiene `originalPrice > 0` y `salePriceApplied != originalPrice`, el sistema marca la orden automáticamente con:
     - `isBlocked: True`
     - `approval.requiresApproval: True`
     - `approval.isApproved: False`
3. **Restricciones de una Orden Bloqueada**:
   - **Prohibido el Cobro**: El cobro total o parcial (`pay_order`) es rechazado con la excepción `OrderIsBlocked` (HTTP 400 con código `ORDER_IS_BLOCKED`).
   - **Prohibida la Captura de Resultados Clínicos**: No se permite ingresar ni modificar resultados analíticos (`results`) en una orden bloqueada.
   - **Permitida la Eliminación**: Una orden bloqueada puede ser eliminada libremente siempre y cuando no tenga pagos registrados (`paidAmount == 0`).
4. **Flujo de Autorización y Desbloqueo (`accessLevel > 3`)**:
   - Un usuario con `accessLevel > 3` (Supervisor o Administrador) puede desbloquear la orden:
     - **En Ventanilla (Operador)**: El operador solicita autorización mediante el modal de credenciales de supervisor (`supervisorUsername`, `supervisorPassword`, `reason`).
     - **En Sesión de Supervisor**: Si el usuario autenticado activo ya posee `accessLevel > 3`, puede autorizar la orden con un solo clic o durante su creación.
   - Al aprobarse (`POST /api/v1/orders/{order_id}/approve`):
     - `isBlocked = False`
     - `approval.isApproved = True`
     - `approval.approvedBy = UserInfo(id, name)`
     - `approval.approvedAt = timestamp`
     - `approval.reason = motivo`
   - Una vez desbloqueada, la orden puede cobrarse y procesarse con total normalidad.
