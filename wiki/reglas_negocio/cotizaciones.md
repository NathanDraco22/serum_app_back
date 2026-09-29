---
type: doc
title: Reglas de Negocio — Cotizaciones y Preventa
description: Reglas de negocio para presupuestos temporales, clientes casuales y conversión controlada hacia órdenes médicas.
tags: [quotations, presale, orders, business_rules]
timestamp: 2026-09-28T18:30:00Z
---

# 📑 Cotizaciones y Preventa

## 1. Propósito de la Entidad `Quotation`

En recepción es común que personas consulten el precio de análisis sin confirmar su realización. Si por cada consulta se creara un expediente de paciente y una orden médica, la base de datos se saturaría de:
- Pacientes provisionales o incompletos.
- Órdenes abandonadas que distorsionarían las métricas clínicas.
- Saldos por cobrar ficticios que afectarían los reportes financieros.

La entidad `Quotation` actúa como una **zona de preventa temporal** que preserva la limpieza de los catálogos principales.

---

## 2. Reglas de Negocio Clave

1. **Cliente en Texto Libre (`clientName`)**:
   - Para emitir una cotización no es obligatorio registrar un `patientId`; basta con el nombre suministrado por el cliente.
2. **Precios Congelados en la Cotización**:
   - Cada prueba o pack cotizado almacena su `quotedPrice` (en centavos) al momento de cotizar para respetar la tarifa pactada durante la vigencia del presupuesto.
3. **Conversión Estricta a Orden**:
   - Para transformar una cotización en una orden médica real, **es obligatorio que el paciente esté formalmente registrado en la colección `patients`**.
   - El sistema bloquea cualquier conversión si el `patientId` no existe.
   - Una vez convertida, la cotización almacena la referencia en `convertedToOrderId` y actualiza su estado para evitar conversiones duplicadas.
