# Documento de Mapeo: Entidades, Rutas, Endpoints y Reglas de Negocio

---

## 1. Entidad: Branch (Sucursal)

| Campo | Valor |
|---|---|
| **Entidad** | Branch |
| **Ruta** | `/api/v1/branches` |
| **Endpoints** | `POST ""` — Crear sucursal<br>`GET ""` — Obtener todas las sucursales<br>`GET "/{branch_id}"` — Obtener sucursal por ID<br>`PATCH "/{branch_id}"` — Actualizar sucursal<br>`DELETE "/{branch_id}"` — Eliminar sucursal (soft delete) |

**Regla de Negocio:** Las sucursales (Branches) representan las sedes físicas del laboratorio. Segmentan las operaciones y los flujos de caja, permitiendo que cada sucursal tenga su propia caja, sus propios usuarios y sus propias órdenes. Los usuarios se vinculan a un `branch_id` específico.

**Problema que resuelve:** Un laboratorio puede tener múltiples ubicaciones físicas. Sin esta entidad, todas las operaciones (caja, usuarios, órdenes) estarían mezcladas, imposibilitando saber en qué sede se generó un ingreso, quién atendió al paciente o dónde se realizó una transacción de caja. Esto es crítico para auditorías financieras segmentadas y para la asignación de personal por sucursal.

---

## 2. Entidad: User (Usuario)

| Campo | Valor |
|---|---|
| **Entidad** | User |
| **Ruta** | `/api/v1/users` |
| **Endpoints** | `POST ""` — Crear usuario<br>`GET ""` — Obtener todos los usuarios<br>`GET "/{user_id}"` — Obtener usuario por ID<br>`PATCH "/{user_id}"` — Actualizar usuario<br>`DELETE "/{user_id}"` — Eliminar usuario (soft delete) |

**Regla de Negocio:** Los usuarios gestionan el acceso al sistema con roles definidos. Cada usuario está vinculado a un `branch_id` (sucursal), lo que determina su ámbito de operación. El sistema debe contar con un mecanismo de autenticación y autorización (roles) para restringir operaciones sensibles como apertura/cierre de caja o eliminación de registros.

**Problema que resuelve:** En un laboratorio clínico conviven recepcionistas, bioanalistas, administradores y gerentes. Cada rol tiene responsabilidades distintas. Sin un sistema de usuarios con roles y vinculación a sucursal, cualquier persona podría realizar operaciones fuera de su competencia (ej. un recepcionista modificando resultados de laboratorio) o acceder a datos de una sucursal que no le corresponde, generando riesgos de seguridad, integridad de datos y auditoría.

---

## 3. Entidad: Patient (Paciente)

| Campo | Valor |
|---|---|
| **Entidad** | Patient |
| **Ruta** | `/api/v1/patients` |
| **Endpoints** | `POST ""` — Crear paciente<br>`GET ""` — Obtener todos los pacientes<br>`GET "/{patient_id}"` — Obtener paciente por ID<br>`PATCH "/{patient_id}"` — Actualizar paciente<br>`DELETE "/{patient_id}"` — Eliminar paciente (soft delete) |

**Regla de Negocio:** El paciente es el expediente maestro con datos demográficos (nombre, edad, sexo, etc.). Es requisito obligatorio tener un paciente registrado formalmente antes de poder crear una orden (**Regla de Oro**: el sistema debe bloquear la conversión de cotización a orden si el `patient_id` no existe). Los datos del paciente se "congelan" (snapshot) dentro de la orden al momento de su creación para garantizar la integridad del historial clínico.

**Problema que resuelve:** Si un paciente cambia de nombre, edad o cualquier dato demográfico después de haberse realizado estudios, los reportes históricos no deben verse alterados. El snapshot dentro de la orden garantiza que el informe médico que se generó en una fecha específica refleje fielmente los datos del paciente en ese momento. Además, evita "órdenes huérfanas" sin un paciente formal, lo que descuadraría los registros médicos y financieros.

---

## 4. Entidad: Doctor (Médico)

| Campo | Valor |
|---|---|
| **Entidad** | Doctor |
| **Ruta** | `/api/v1/doctors` |
| **Endpoints** | `POST ""` — Crear médico<br>`GET ""` — Obtener todos los médicos<br>`GET "/{doctor_id}"` — Obtener médico por ID<br>`PATCH "/{doctor_id}"` — Actualizar médico<br>`DELETE "/{doctor_id}"` — Eliminar médico (soft delete) |

**Regla de Negocio:** Catálogo de médicos referentes que solicitan los estudios. Es un registro opcional (no obligatorio para crear una orden). Sirve como fuente de datos para reportes y estadísticas sobre qué médicos derivan más pacientes al laboratorio.

**Problema que resuelve:** Los laboratorios reciben órdenes médicas de distintos doctores externos. Sin un catálogo estandarizado, cada recepcionista podría escribir el nombre del médico de forma distinta ("Dr. Pérez", "Dr. Perez", "Doctor Pérez"), imposibilitando generar estadísticas confiables sobre médicos referentes, que son un indicador comercial clave para el laboratorio.

---

## 5. Entidad: LabTest (Prueba de Laboratorio)

| Campo | Valor |
|---|---|
| **Entidad** | LabTest |
| **Ruta** | `/api/v1/lab-tests` |
| **Endpoints** | `POST ""` — Crear prueba de laboratorio<br>`GET ""` — Obtener todas las pruebas<br>`GET "/{lab_test_id}"` — Obtener prueba por ID<br>`PATCH "/{lab_test_id}"` — Actualizar prueba<br>`DELETE "/{lab_test_id}"` — Eliminar prueba (soft delete) |

**Regla de Negocio:** Actúa como el diccionario médico global, estandarizado y puramente científico del laboratorio. Define qué se puede medir (parámetro), cómo se mide (unidad de medida) y cuáles son los límites sanos (`referenceValues`) basados en demografía (tipo de paciente, género, rango de edad en días). Los rangos de referencia se configuran dinámicamente en la base de datos, no en código.

**Problema que resuelve:** Evita la redundancia de datos y errores ortográficos o médicos al crear exámenes/paquetes. Si cada examen definiera sus propios parámetros manualmente, un mismo parámetro (ej. "Glucosa") podría escribirse de 5 formas distintas o tener rangos de referencia inconsistentes. Además, evita hardcodear la lógica de alertas médicas en el código fuente, delegándola a una configuración de base de datos que el personal médico puede actualizar sin necesidad de programadores.

---

## 6. Entidad: Exam (Examen / Paquete Comercial)

| Campo | Valor |
|---|---|
| **Entidad** | Exam |
| **Ruta** | `/api/v1/exams` |
| **Endpoints** | `POST ""` — Crear examen<br>`GET ""` — Obtener todos los exámenes<br>`GET "/{exam_id}"` — Obtener examen por ID<br>`PATCH "/{exam_id}"` — Actualizar examen<br>`DELETE "/{exam_id}"` — Eliminar examen (soft delete) |

**Regla de Negocio:** Es el "Preset" o paquete comercial (ej. "Perfil Lipídico", "Biometría Hemática"). Controla estrictamente la facturación y la organización del menú de ventas. Agrupa múltiples `LabTest` en un solo producto. Al crearse, clona (inyecta) la información de `LabTest` dentro del examen mediante `IncludedTest`, evitando joins lentos en MongoDB.

**Problema que resuelve:** Separa la responsabilidad financiera de la responsabilidad médica. El departamento comercial puede crear paquetes (exámenes) con precios sin tener que entender la ciencia detrás. Si se modifican los rangos de referencia de un `LabTest`, los exámenes existentes no se ven afectados porque ya tienen los datos clonados. Además, en horas pico, el sistema no necesita hacer joins entre colecciones para mostrar los parámetros de un examen, mejorando drásticamente el rendimiento.

---

## 7. Entidad: Quotation (Cotización)

| Campo | Valor |
|---|---|
| **Entidad** | Quotation |
| **Ruta** | `/api/v1/quotations` |
| **Endpoints** | `POST ""` — Crear cotización<br>`GET ""` — Obtener todas las cotizaciones<br>`GET "/{quotation_id}"` — Obtener cotización por ID<br>`PATCH "/{quotation_id}"` — Actualizar cotización<br>`DELETE "/{quotation_id}"` — Eliminar cotización (soft delete) |

**Regla de Negocio:** Maneja el proceso de preventa para clientes casuales que solo consultan precios. El cliente puede ser texto libre (sin registro formal). Tiene estado `pending` y puede convertirse a una orden real mediante `convertedToOrderId`. La cotización es un documento temporal que **no debe contaminar** el catálogo de pacientes ni las órdenes formales.

**Problema que resuelve:** En un laboratorio, muchas personas llegan preguntando precios sin llegar a comprar. Si cada consulta creara un paciente formal y una orden, la base de datos se llenaría de "órdenes abandonadas" que descuadrarían:
- El arqueo de caja (órdenes sin pagar que aparecen como pendientes)
- Las métricas médicas (pacientes fantasmas)
- Los reportes de productividad

La cotización actúa como un "buffer" de preventa que permite transicionar fluidamente de un cliente anónimo a un paciente formal solo cuando se confirma la compra.

---

## 8. Entidad: Order (Orden)

| Campo | Valor |
|---|---|
| **Entidad** | Order |
| **Ruta** | `/api/v1/orders` |
| **Endpoints** | `POST ""` — Crear orden<br>`GET ""` — Obtener todas las órdenes<br>`GET "/{order_id}"` — Obtener orden por ID<br>`PATCH "/{order_id}"` — Actualizar orden<br>`DELETE "/{order_id}"` — Eliminar orden (soft delete) |

**Regla de Negocio (la más crítica del sistema):** La orden es el **Snapshot inmutable**:
1. **Snapshot de datos del paciente**: Congela los datos demográficos al momento de creación.
2. **Snapshot de rangos de referencia**: Copia los `referenceValues` desde el examen para que cambios futuros en el catálogo no alteren diagnósticos pasados.
3. **Snapshot de precios**: Guarda `salePriceApplied` para que cambios tarifarios no descuadren arqueos históricos.
4. **Máquina de estados**: `Created → In Process → Completed → Published`.
5. Contiene embebidos los resultados (`OrderTestResult`) con valores y alertas médicas (`alertFlag`).
6. Al crearse, copia la estructura de parámetros desde Exams para que el bioanalista solo llene valores.

**Problema que resuelve:** Es la **entidad central del sistema** y resuelve el problema más complejo del LIS: la **alteración histórica**. En un laboratorio:
- **Médico**: Si un paciente se hizo una glucosa en 2024 con rango 70-100 mg/dL y en 2025 el laboratorio cambia su maquinaria y el rango pasa a 74-106 mg/dL, el reporte de 2024 debe seguir mostrando el rango original. Sin snapshot, el reporte histórico se "recalibraría" retrospectivamente, pudiendo mostrar alertas falsas (el valor 95 mg/dL aparecería como normal en 2024, pero si el rango cambia post-hoc, podría malinterpretarse).
- **Financiero**: Si un examen costaba C$500 en enero y subió a C$600 en marzo, los arqueos de enero deben reflejar C$500. Sin snapshot, recalcular los ingresos históricos con el precio actual daría un resultado incorrecto.
- **Rendimiento**: Al tener todo en un solo documento MongoDB, la generación de reportes no necesita joins, lo que es crítico en horas pico cuando el volumen de muestras es máximo.

---

## 9. Entidad: CashRegister (Caja Física)

| Campo | Valor |
|---|---|
| **Entidad** | CashRegister |
| **Ruta** | `/api/v1/cash-registers` |
| **Endpoints** | `POST ""` — Crear caja<br>`GET ""` — Obtener todas las cajas<br>`GET "/{cash_register_id}"` — Obtener caja por ID<br>`PATCH "/{cash_register_id}"` — Actualizar caja<br>`DELETE "/{cash_register_id}"` — Eliminar caja (soft delete) |

**Regla de Negocio:** Representa una caja física asociada a una sucursal. Mantiene saldos segmentados por método de pago (`cashBalance`, `cardBalance`, `transferBalance`, `totalBalance`). El estado `isOpen` indica si la caja está operativa. El campo `openedBy` registra qué usuario realizó la apertura. El balance de caja **no se edita directamente**; se reconstruye a partir de las transacciones del Kardex.

**Problema que resuelve:** Un laboratorio puede tener múltiples puntos de cobro en una misma sucursal (caja 1, caja 2). Sin una entidad que represente cada caja física, no se podría saber:
- Qué caja recibió cada pago
- Quién abrió/cerró cada caja
- Cuánto dinero hay en cada caja segmentado por método de pago

Esto es fundamental para la rendición de cuentas al final del día y para detectar discrepancias (sobrantes o faltantes) en cada caja individual.

---

## 10. Entidad: CashTransaction (Transacción de Caja / Kardex)

| Campo | Valor |
|---|---|
| **Entidad** | CashTransaction |
| **Ruta** | `/api/v1/cash-transactions` |
| **Endpoints** | `GET ""` — Obtener todas las transacciones (con filtros: `CashTransactionFilterParams`) |

**Nota importante:** Esta es la **única entidad que NO tiene CRUD completo**. Solo tiene un endpoint de consulta (GET ALL con filtros). No tiene POST, PATCH, ni DELETE porque está diseñada para ser **inmutable**.

**Regla de Negocio:** Es el libro contable inmutable (Kardex). Cada movimiento registra:
- `flowType`: "in" (aumenta saldo) o "out" (disminuye saldo)
- `subType`: "opening", "closing", "income", "withdrawal", "payment"
- `paymentMethod`: "cash", "card", "transfer"
- `amount`: monto en centavos
- `resultingBalance`: saldo resultante después de la transacción (crítico para auditoría)
- `concept`: razón obligatoria del movimiento
- `referenceId`: vínculo opcional a una orden

**Reglas inmutables:**
1. Las transacciones **nunca se editan ni eliminan**. Los errores se corrigen con nuevas transacciones de ajuste.
2. El saldo de caja es la reconstrucción de eventos inmutables.
3. Toda transacción debe llevar un `concept` que explique el "por qué".
4. El sistema debe verificar que la suma de transacciones del día coincida con el `resultingBalance` final.

**Problema que resuelve:** Este es el **mecanismo de auditoría financiera** del sistema. Resuelve tres problemas críticos:

1. **Trazabilidad absoluta**: Cualquier movimiento de dinero queda registrado para siempre. Si alguien preguntara "¿qué pasó en la caja 1 el 15 de marzo de 2024?", se puede reconstruir segundo a segundo cada transacción.

2. **Prevención de fraude/errores**: Como las transacciones no se pueden editar ni eliminar, es imposible "maquillar" un arqueo. Si se detecta un error, se hace una transacción de ajuste (ej. "corrección: sobrante de C$50") que deja evidencia de ambos eventos: el error y su corrección.

3. **Arqueo diario**: Al final del día, el sistema puede calcular automáticamente si el saldo declarado en caja coincide con la suma de transacciones, detectando sobrantes o faltantes de forma inmediata.

---

## Resumen de la Arquitectura por Módulos

| Módulo | Entidades | Propósito |
|---|---|---|
| **Clínico y Maestros** | Branch, User, Patient, Doctor, LabTest | Gestión de sedes, personal, pacientes, médicos referentes y diccionario médico |
| **Comercial** | Exam, Quotation | Paquetes de venta (exámenes) y preventa (cotizaciones) |
| **Transaccional** | Order | **Entidad central**: snapshot inmutable que integra datos clínicos, demográficos y financieros |
| **Financiero** | CashRegister, CashTransaction | Control de caja física y kardex contable inmutable para auditoría |
