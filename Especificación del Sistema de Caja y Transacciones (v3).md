# **Documento Técnico: Módulo de Caja y Control Financiero (v3)**

**Nota de Diseño:** Todo campo monetario debe ser manejado como un **entero (int)** representando **centavos**.

## **1\. Modelos de Datos (Pydantic \- Centavos)**

### **1.1. CashRegister (Caja Física)**

class CashRegister(BaseModel):  
    branchId: str  
    name: str  
    isOpen: bool \= False  
    cashBalance: int \= 0  
    cardBalance: int \= 0  
    transferBalance: int \= 0  
    totalBalance: int \= 0  
    openedBy: UserInfo | None \= None

### **1.2. CashTransaction (El Kardex Refinado)**

class CashTransaction(BaseModel):  
    registerId: str  
    flowType: str         \# "in" | "out"  
    subType: str          \# "opening" | "closing" | "income" | "withdrawal" | "payment"  
    paymentMethod: str | None \= None  \# cash | card | transfer  
    amount: int           \# en centavos  
    resultingBalance: int \# en centavos  
    concept: str          \# Razón del movimiento  
    referenceId: str | None \= None  
    performedBy: UserInfo  
    createdAt: datetime \= datetime.now()

## **2\. Definición de Flujos y Subtipos**

* **Apertura de Caja (opening):** flowType: "in". Registra el fondo de caja inicial.  
* **Cierre de Caja (closing):** flowType: "out". Registra el retiro total para el arqueo final.  
* **Ingresos (income):** flowType: "in". Entradas de dinero no provenientes de una orden (ej. abonos, fondo adicional).  
* **Retiros (withdrawal):** flowType: "out". Salidas de dinero (ej. pago a proveedores, gastos menores).  
* **Pagos de Órdenes (payment):** flowType: "in". Cobros generados por una Order.

## **3\. Reglas de Negocio**

1. **Consistencia de Flujo:** \- Las transacciones in aumentan el totalBalance de la CashRegister.  
   * Las transacciones out disminuyen el totalBalance de la CashRegister.  
2. **Auditoría:** Cada movimiento debe obligatoriamente llevar un concept que explique el "por qué" (la razón) del movimiento, especialmente en los subtipos income y withdrawal.  
3. **Validación de Cierre:** El sistema debe verificar que la suma de todas las CashTransaction del día coincida con el resultingBalance final de la CashRegister.