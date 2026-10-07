---
type: doc
title: Reglas de Negocio — Cotizaciones y Preventa
description: Reglas de negocio para presupuestos temporales, clientes casuales, datos de cliente y médico opcionales, tarifas congeladas y carácter estrictamente informativo.
tags: [quotations, presale, orders, business_rules, snapshots]
timestamp: 2026-10-06T18:00:00Z
---

# 📑 Cotizaciones y Preventa

## 1. Propósito de la Entidad `Quotation`

En recepción es común que personas consulten el precio de análisis sin confirmar su realización. Si por cada consulta se creara un expediente de paciente y una orden médica, la base de datos se saturaría de:
- Pacientes provisionales o incompletos.
- Órdenes abandonadas que distorsionarían las métricas clínicas.
- Saldos por cobrar ficticios que afectarían los reportes financieros.

La entidad `Quotation` actúa como una **zona de preventa temporal** que preserva la limpieza de los catálogos principales y permite emitir comprobantes impresos o en PDF con validez oficial garantizada.

---

## 2. Reglas de Negocio Clave

1. **Cliente Opcional / Texto Libre (`clientName` y `clientInfo`)**:
   - Para emitir una cotización no es obligatorio registrar un `patientId` en la base de datos.
   - El sistema admite un nombre provisional en texto libre o toma por defecto `"Cliente General"`.
   - Si se asocia un paciente registrado, se almacena su referencia en `patientId` y se congela su snapshot inmutable en `clientInfo: PatientInfo | None` (nombre, fecha de nacimiento, sexo, teléfono, dirección, cédula).
2. **Médico Referente Opcional (`doctorId` y `doctorInfo`)**:
   - El médico solicitante es opcional.
   - Si se asigna un médico referente, se registra su ID en `doctorId` y su snapshot en `doctorInfo: DoctorInfo | None` (nombre, especialidad, teléfono, cédula).
3. **Precios Congelados en la Cotización**:
   - Cada prueba o pack cotizado almacena su `quotedPrice` (en centavos `int`) al momento de cotizar para respetar la tarifa pactada durante la vigencia del presupuesto (15 días).
   - Se registra el nivel de tarifa aplicado (`priceLevel: 1` para regular o `2` para tarifa especial).
4. **Flujo Directo sin Resultados ni Cobro**:
   - A diferencia de una orden médica clínica, la cotización no genera parámetros de resultados vacíos (`OrderTestResult`) ni transacciones contables en el Kardex.
5. **Carácter Estrictamente Informativo (Sin Conversión a Orden)**:
   - Una cotización es exclusivamente un presupuesto informativo de venta y preventa con tarifas congeladas.
   - No transiciona ni se marca como convertida en el flujo operativo del sistema: *una cotización es solamente una cotización*.
   - Si el cliente decide contratar los servicios y realizarse los análisis, recepción genera una orden clínica formal desde el módulo de órdenes, asegurando el alta o selección formal del paciente, la recepción de muestras y el flujo clínico de resultados.
6. **Ventana de Consulta y Filtro Fijo de 30 Días (`QuotationFilterParams` y `QuotationQueryParams`)**:
   - Dado que las cotizaciones son presupuestos de vigencia temporal, las consultas por defecto están restringidas a un rango fijo de los **últimos 30 días** (`createdAt >= now - 30 días`).
   - Sigue la convención estándar del sistema mediante `QuotationFilterParams` en backend y `QuotationQueryParams` en Flutter (`branchId`, `patientId`, `doctorId`, `status`, `startDate`, `endDate`, `offset`, `limit`) con ordenamiento descendente por `createdAt`.
   - Tanto la API (`QuotationsCollection`) como la lógica del cliente (`QuotationQueryParams.last30Days()`) garantizan que el listado de cotizaciones se mantenga ágil y acotado al ciclo operativo vigente.

