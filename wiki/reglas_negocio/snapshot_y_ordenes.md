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

Para mantener la flexibilidad comercial en ventanilla (descuentos especiales, convenios informales, promociones del día) sin vulnerar el control financiero ni la integridad del laboratorio:

### A. Auditoría de Precios Originales (`originalPrice`)
1. Cada ítem de la orden (`OrderItem`) congela tanto el precio efectivamente cobrado (`salePriceApplied`) como el precio base del catálogo (`originalPrice`, en centavos):
   ```python
   class OrderItem(BaseModel):
       labTestId: str
       name: str
       salePriceApplied: int      # Precio cobrado (en centavos)
       originalPrice: int = 0     # Precio oficial de catálogo 1 (en centavos)
   ```
2. Esto permite realizar comparaciones y reportes de auditoría en cualquier momento:
   $$\text{Diferencia / Descuento} = \text{originalPrice} - \text{salePriceApplied}$$

### B. Detección Automática de Discrepancia
Al crearse la orden (`OrdersRepository.create_order`):
- Si para cualquier ítem se cumple que `originalPrice > 0` y `salePriceApplied != originalPrice`, el sistema evalúa si la orden ya viene con una autorización válida de un supervisor:
  - **Si no viene autorizada**: El sistema asigna automáticamente:
    ```json
    {
      "isBlocked": true,
      "approval": {
        "requiresApproval": true,
        "isApproved": false,
        "approvedBy": null,
        "approvedAt": null,
        "reason": null
      }
    }
    ```
  - **Si el usuario activo al crear la orden tiene `accessLevel > 3`**: La orden se crea con `isBlocked: false` y el objeto `approval` pre-aprobado con sus datos de supervisor.

### C. Restricciones Operativas de una Orden Bloqueada
1. **Cobro Estrictamente Bloqueado**:
   - `OrderPaymentManager.pay_order` valida el estado antes de interactuar con la caja. Si `order.isBlocked == True`, interrumpe la transacción y lanza la excepción de dominio `OrderIsBlocked()`, la cual responde al cliente con:
     > **HTTP 400 Bad Request** con código `ORDER_IS_BLOCKED`: *"La orden se encuentra bloqueada por modificación de precio. Requiere autorización de un supervisor antes de poder registrar pagos."*
2. **Captura y Modificación de Resultados Clínicos Prohibida**:
   - En `OrdersController.update_order_by_id`, si se intenta actualizar el arreglo `results` y la orden está bloqueada (`isBlocked == True`), se rechaza la operación inmediatamente. El bioanalista no puede ingresar resultados analíticos hasta que un supervisor apruebe la orden.
3. **Eliminación Permitida para Órdenes sin Cobro**:
   - Para evitar bloqueos administrativos con órdenes erróneas o canceladas por el paciente en ventanilla, una orden bloqueada **puede ser eliminada** (`delete_order_by_id`) siempre y cuando no se haya registrado ningún cobro (`paidAmount == 0`).

---

### D. Flujo de Autorización y Desbloqueo (`POST /api/v1/orders/{order_id}/approve`)

El endpoint de autorización permite dos modalidades operativas:

#### Modalidad 1: Autorización en Ventanilla (Operador con Supervisor Presencial)
Cuando un operador de ventanilla (`accessLevel <= 3`) requiere autorización:
1. El frontend despliega el modal `SupervisorAuthDialog`.
2. El supervisor ingresa sus credenciales y un motivo opcional.
3. Se envía la petición:
   - **Endpoint**: `POST /api/v1/orders/{order_id}/approve`
   - **Body (`OrderApproveRequest`)**:
     ```json
     {
       "supervisorUsername": "dra.garcia",
       "supervisorPassword": "Password123",
       "reason": "Descuento autorizado por cortesía médica"
     }
     ```
4. **Ciclo de Verificación en el Servidor**:
   - Localiza al supervisor por `username`, `email` o `phone`.
   - Verifica que el usuario exista, esté activo (`isActive == True`) y no esté eliminado (`isDeleted == False`).
   - Verifica la contraseña mediante `SysPasswordHasher.verify_password`. Si es errónea $\to$ `HTTP 401 Unauthorized` (*"Credenciales de supervisor incorrectas"*).
   - Comprueba estrictamente que `accessLevel > 3`. Si el nivel es $\le 3 \to$ `HTTP 403 Forbidden` (*"El usuario no tiene nivel de acceso suficiente (> 3) para autorizar"*).
   - Actualiza MongoDB: `isBlocked = false`, `isApproved = true`, `approvedBy = UserInfo(id, name)`, `approvedAt = now()`, `reason = motivo`.

#### Modalidad 2: Autorización Remota o por Sesión Activa de Supervisor
Cuando el usuario que utiliza el sistema ya inició sesión con una cuenta con `accessLevel > 3`:
1. El frontend envía la petición al mismo endpoint sin credenciales en el body (o solo con el campo `reason` opcional).
2. El backend examina el header `Authorization: Bearer <token>`:
   - Decodifica los claims del JWT.
   - Extrae el `accessLevel`. Si `accessLevel > 3`, toma el `userId` y nombre del supervisor de la sesión activa y autoriza la orden en un solo clic.

---

### E. Resumen de Códigos HTTP del Endpoint `/approve`

| Código HTTP | Motivo | Detalle |
| :--- | :--- | :--- |
| **`200 OK`** | Aprobación exitosa | Retorna `OrderInDb` con `isBlocked: false` y metadatos de auditoría completos. |
| **`400 Bad Request`** | Error de negocio | Lanzado con `ORDER_IS_BLOCKED` en cobros o actualización de resultados. |
| **`401 Unauthorized`** | Credenciales inválidas | Usuario no encontrado o contraseña de supervisor incorrecta. |
| **`403 Forbidden`** | Nivel insuficiente | El usuario que intenta autorizar tiene `accessLevel <= 3`. |
| **`404 Not Found`** | Orden inexistente | No existe una orden con el `order_id` especificado. |

