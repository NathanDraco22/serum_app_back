Core Business Rules: Sistema de LaboratorioEste documento define el núcleo absoluto del negocio. Aquí se establecen las reglas para el catálogo médico, la oferta comercial, el flujo de ventas temporales y el procesamiento inmutable de resultados.1. Entidad: LabTestObjetivo de la Entidad:Actuar como el diccionario médico global, estandarizado y puramente científico del laboratorio. Define qué se puede medir, cómo se mide y cuáles son los límites sanos basados en demografía.Problema que Resuelve:Evita la redundancia de datos y los errores ortográficos o médicos al crear paquetes. Evita que la lógica de cálculos de alertas se programe en el código (hardcode), delegándolo a una configuración de base de datos dinámica.Modelo Pydantic:from pydantic import BaseModel

class ReferenceValue(BaseModel):
    patientType: str
    gender: str
    minAgeDays: int
    maxAgeDays: int
    minValue: float
    maxValue: float

class LabTest(BaseModel):
    parameterName: str
    medicalClassification: str
    dataType: str
    unitOfMeasure: str
    referenceValues: list[ReferenceValue] = []
2. Entidad: ExamObjetivo de la Entidad:Es el "Preset" o paquete comercial (ej. Perfil Lipídico). Controla estrictamente la facturación y la organización del menú de ventas en recepción.Problema que Resuelve:Separa la responsabilidad financiera de la clínica. Permite que el laboratorio venda combos que agrupan pruebas de naturalezas médicas totalmente distintas en un solo producto, clonando (inyectando) la información de LabTest para evitar joins (búsquedas cruzadas) lentos en la base de datos.Modelo Pydantic:from pydantic import BaseModel

class IncludedTest(BaseModel):
    labTestId: str
    parameterName: str
    medicalClassification: str
    dataType: str
    unitOfMeasure: str
    referenceValues: list[ReferenceValue] = []

class Exam(BaseModel):
    name: str
    commercialCategory: str
    salePrice: float
    currency: str
    includedTests: list[IncludedTest] = []
3. Entidad: Quotation (Cotización)Objetivo de la Entidad:Manejar el proceso de preventa y presupuesto para clientes casuales (pacientes no confirmados) que solo están consultando precios.Problema que Resuelve:Evita la contaminación de la base de datos principal de Pacientes y Orders con datos basura o "órdenes abandonadas" que descuadrarían el arqueo de caja y las métricas médicas. Permite transicionar fluidamente de un cliente anónimo a un paciente formal.Modelo Pydantic:from pydantic import BaseModel

class QuotedExam(BaseModel):
    examId: str
    examName: str
    quotedPrice: float

class Quotation(BaseModel):
    clientName: str
    patientId: str | None = None
    exams: list[QuotedExam] = []
    totalAmount: float
    status: str = "pending"
    convertedToOrderId: str | None = None
4. Entidad: OrderObjetivo de la Entidad:Es el expediente transaccional. Es la única entidad del sistema donde habitan los resultados reales digitados por el personal y representa la confirmación de venta real.Problema que Resuelve:Resuelve el problema de la alteración histórica. Funciona como un Snapshot inmutable: al clonar los precios de venta y las referencias médicas al momento exacto de la creación de la orden, garantiza que si el catálogo de precios o reglas médicas cambia en el futuro, el historial de este paciente jamás se verá alterado o corrompido retroactivamente.Modelo Pydantic:from pydantic import BaseModel

class OrderTestResult(IncludedTest):
    resultValue: str | None = None
    alertFlag: str | None = None

class Order(BaseModel):
    patientId: str
    quotationId: str | None = None
    examId: str
    examName: str
    salePriceApplied: float
    status: str = "pending"
    results: list[OrderTestResult] = []
