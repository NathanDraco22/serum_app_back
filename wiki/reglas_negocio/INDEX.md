---
type: index
title: Backend — Reglas de Negocio
description: Índice de documentos con las reglas de negocio del sistema de laboratorio clínico y caja.
tags: [backend, business_rules, index, lis]
timestamp: 2026-09-28T18:30:00Z
---

# 🩺 Reglas de Negocio — Índice

Documentación detallada sobre el comportamiento, validaciones y lógica de negocio del servidor.

| Documento | Descripción |
| :--- | :--- |
| **[Snapshot y Órdenes](snapshot_y_ordenes.md)** | Integridad histórica mediante Snapshots, por qué se congelan datos médicos y ciclo de vida de la Orden. |
| **[Catálogo de LabTests](catalogo_lab_tests.md)** | Pruebas individuales, perfiles/packs compuestos, tipos de datos (`numeric`, `boolean`, `text`) y rangos demográficos. |
| **[Caja y Kardex Financiero](caja_y_kardex.md)** | Libro contable inmutable, control de arqueo, desglose por métodos de pago y regla de montos en centavos. |
| **[Cotizaciones y Preventa](cotizaciones.md)** | Manejo de clientes casuales, aislamiento de datos y transición validada hacia orden formal. |
| **[Autenticación y Roles](autenticacion_y_roles.md)** | Sesiones JWT (HS256), refresh tokens, endpoint `/check-user` y segmentación por sucursales. |
