### Guía de Conceptos: Arquitectura y Lógica de Negocio del Sistema de Laboratorio (LIS)

Esta guía establece los fundamentos arquitectónicos y las reglas de negocio para el desarrollo del LIS, centrando el diseño en la integridad de los datos médicos y la trazabilidad financiera mediante el uso de  **Snapshots** .

##### 1\. Introducción al Concepto de Snapshot (Información Congelada)

En el contexto de un laboratorio clínico, la persistencia de datos no puede depender de relaciones dinámicas tradicionales. Es imperativo asegurar que la información generada hoy sea inmutable ante cambios futuros en los catálogos maestros. Para ello, implementamos el concepto de  **Snapshot** .**Definición de Snapshot:**  Es la técnica de clonar y almacenar físicamente los datos relevantes (demografía del paciente, rangos de referencia y precios) dentro del documento de la Orden en el momento de su creación. Esto transforma la orden en una entidad autónoma que no depende de punteros externos para representar la realidad histórica del evento médico.Desde la perspectiva de un Arquitecto Senior, este enfoque es obligatorio por tres razones:

* **Historial Clínico:**  La edad y el sexo del paciente al momento de la prueba deben quedar "congelados", pues de ellos dependen las interpretaciones médicas posteriores.  
* **Rangos de Referencia:**  Si el laboratorio actualiza su maquinaria, los rangos de normalidad cambian. Sin un snapshot, los reportes antiguos mostrarían alertas erróneas basándose en valores nuevos.  
* **Integridad Financiera:**  Los precios en el catálogo fluctúan. Para un arqueo de caja auditable, la orden debe registrar el precio exacto cobrado, independientemente de actualizaciones tarifarias posteriores.Técnicamente, este desacoplamiento permite un  **Escalamiento Horizontal**  eficiente. Al evitar el uso de lookups o joins complejos en MongoDB durante las horas pico de la mañana (cuando el volumen de muestras es máximo), reducimos significativamente el overhead de CPU y garantizamos tiempos de respuesta constantes.

##### 2\. Por qué "Congelar" los Datos: Tabla de Justificación Médica y Financiera

La siguiente tabla contrasta el riesgo operativo de una arquitectura relacional pura frente a los beneficios de nuestra arquitectura basada en documentos independientes.| Escenario | Riesgo (Solo IDs) | Beneficio del Snapshot (Datos Congelados) || \------ | \------ | \------ || **Datos del Paciente** | Si se corrige un error ortográfico en el maestro de pacientes, se altera el reporte legal de hace 5 años. | El reporte histórico permanece fidedigno a la identidad del paciente en la fecha del examen. || **Rangos de Referencia** | Si la nueva maquinaria cambia el rango de Glucosa de  $70-100$  a  $74-106$  mg/dL, los resultados viejos se descalibran. | Los rangos se copian textualmente; las actualizaciones del catálogo no afectan la validez de diagnósticos pasados. || **Precios de Exámenes** | Si un examen sube de  $C\\$ 500$  a  $C\\$ 600$ , los arqueos históricos se descuadrarían al recalcular ingresos. | El precio aplicado se guarda en la orden, blindando el historial financiero en Córdobas (C$) contra fluctuaciones. |  
Esta estructura es la base de un sistema auditable y médicamente seguro.

##### 3\. Arquitectura de Colecciones en MongoDB

Para el MVP, hemos definido 9 colecciones organizadas en tres módulos lógicos. El objetivo es que la entidad central (Orders) sea el destino final de toda la información relevante.

##### Módulo Clínico y Maestros

* **Users** : Gestiona el acceso del personal con roles definidos y vinculación a un branch\_id específico.  
* **Branches** : Sedes físicas que segmentan las operaciones y flujos de caja.  
* **Patients** : Expediente maestro con datos demográficos que sirven de fuente para las órdenes.  
* **Doctors** : Catálogo de médicos referentes (registro opcional).  
* **Exams** : Plantillas maestras que definen parámetros, precios y los rangos de referencia (mínimos/máximos) para las alertas.

##### Módulo de Flujo Médico

* **Quotes** : Documentos temporales para prospectos donde el cliente puede ser texto libre.  
* **Orders** : La entidad central. Es el  **Snapshot**  definitivo. Contiene embebidos los resultados, datos del paciente y precios. Al alojar todo en un solo documento, eliminamos la necesidad de cruzar colecciones para la generación de reportes.

##### Módulo Financiero

* **CashSessions** : Estado operativo de las cajas (Abierta/Cerrada) por sucursal.  
* **CashTransactions**  **(Kardex)** : Libro contable inmutable. Cada movimiento registra el monto y, críticamente, el  **Saldo Resultante**  en Córdobas (C$). El balance de caja no se edita; se reconstruye a partir de estos eventos.

##### 4\. El Ciclo de Vida: De Cotización a Orden y Resultado

El flujo lógico debe garantizar que no existan huérfanos de datos ni inconsistencias financieras:

1. **Cotización:**  Registro de exámenes con cliente opcional (texto libre). Sirve para proyecciones de venta sin ensuciar el catálogo de pacientes.  
2. **Conversión:**  El backend debe clonar y enriquecer los datos.  **Regla de Negocio:**  El sistema debe bloquear la conversión si el paciente\_id no existe; es obligatorio registrar formalmente al paciente antes de generar la orden.  
3. **Procesamiento:**  El bioanalista captura resultados. El sistema debe comparar automáticamente el valor\_usuario contra el valor\_minimo y valor\_maximo almacenados en el snapshot para generar alertas de salud en tiempo real.  
4. **Cierre:**  El pago genera un registro en el  **Kardex** . Cada transacción debe estampar el saldo\_resultante (Suma/Resta del registro anterior) para asegurar la trazabilidad absoluta del arqueo.

##### 5\. Consideraciones Técnicas para la Implementación

Como equipo de desarrollo, deben asegurar que la implementación respete la integridad del snapshot mediante el siguiente checklist:

*   **Inyectar estructuras de resultados vacías:**  Al crear la Order, copiar la estructura de parámetros desde Exams para que el bioanalista solo llene valores.  
*   **Implementar Alertas de Salud:**  El backend debe realizar la lógica de computación (comparar valor ingresado vs rangos del snapshot) durante la fase de procesamiento.  
*   **Máquina de Estados de la Orden:**  Implementar estrictamente los estados: Created \-\> In Process \-\> Completed \-\> Published.  
*   **Vinculación de Caja:**  Todo pago debe estar ligado al \_id de la sesión de caja activa.  
*   **Inmutabilidad del Kardex:**  Una transacción guardada nunca se edita ni se elimina. Los errores se corrigen con nuevas transacciones de ajuste.  
*   **Exclusión de Inventario:**  En esta Fase 1, no se implementa manejo de reactivos. La complejidad de que un "kit" sirva para 100 pruebas y la merma por calibración harían inestable el MVP. Mantener la arquitectura limpia para una futura integración.

##### 6\. Resumen de Reglas de Oro para el Desarrollador

**1\. La Orden es un Snapshot:**  Nunca consumas datos de pacientes o rangos de exámenes desde colecciones externas para una orden ya creada. Si el dato no está en la orden, la arquitectura falló.**2\. No Fragmentar:**  Los resultados clínicos no viven en colecciones separadas. Viven dentro del arreglo de exámenes de la colección Orders para maximizar la velocidad de lectura.**3\. Arqueo Basado en el Kardex:**  El saldo de caja es la reconstrucción de eventos inmutables. El campo "Saldo Resultante" en cada transacción es la única fuente de verdad para auditorías.  
