from pydantic import BaseModel, Field


# -------------------------------------------------------------
# 1. Reporte Financiero (Facturado vs Cobrado)
# -------------------------------------------------------------


class PaymentMethodsBreakdown(BaseModel):
    cash: int = 0
    card: int = 0
    transfer: int = 0


class FinancialBranchReport(BaseModel):
    branchId: str
    branchName: str = ""
    totalBilled: int = 0
    totalCollected: int = 0
    pendingReceivables: int = 0
    ordersCount: int = 0
    transactionsCount: int = 0
    paymentMethods: PaymentMethodsBreakdown = Field(
        default_factory=PaymentMethodsBreakdown
    )


class FinancialSummaryReport(BaseModel):
    totalBilled: int = 0
    totalCollected: int = 0
    pendingReceivables: int = 0
    ordersCount: int = 0
    transactionsCount: int = 0
    paymentMethods: PaymentMethodsBreakdown = Field(
        default_factory=PaymentMethodsBreakdown
    )


class FinancialReportResponse(BaseModel):
    startDate: int
    endDate: int
    summary: FinancialSummaryReport
    byBranch: list[FinancialBranchReport]


# -------------------------------------------------------------
# 2. Reporte de Médicos Referentes (Top Doctors)
# -------------------------------------------------------------


class DoctorOrderItem(BaseModel):
    doctorId: str | None = None
    doctorName: str
    specialty: str = ""
    totalOrders: int = 0
    totalRevenue: int = 0


class TopDoctorsBranchReport(BaseModel):
    branchId: str
    branchName: str = ""
    doctors: list[DoctorOrderItem]


class TopDoctorsSummary(BaseModel):
    totalOrders: int = 0
    totalRevenue: int = 0
    topDoctors: list[DoctorOrderItem]


class TopDoctorsReportResponse(BaseModel):
    startDate: int
    endDate: int
    summary: TopDoctorsSummary
    byBranch: list[TopDoctorsBranchReport]


# -------------------------------------------------------------
# 3. Reporte de Volumen de Exámenes (Lab Tests / Packs)
# -------------------------------------------------------------


class LabTestVolumeItem(BaseModel):
    labTestId: str
    name: str
    category: str = ""
    isPack: bool = False
    timesOrdered: int = 0
    totalRevenue: int = 0


class LabTestsVolumeBranchReport(BaseModel):
    branchId: str
    branchName: str = ""
    tests: list[LabTestVolumeItem]


class LabTestsVolumeSummary(BaseModel):
    totalTestsCount: int = 0
    totalRevenue: int = 0
    topTests: list[LabTestVolumeItem]


class LabTestsVolumeReportResponse(BaseModel):
    startDate: int
    endDate: int
    source: str
    summary: LabTestsVolumeSummary
    byBranch: list[LabTestsVolumeBranchReport]


# -------------------------------------------------------------
# 4. Reporte de Cuentas por Cobrar (Saldos Pendientes)
# -------------------------------------------------------------


class PendingBalanceItem(BaseModel):
    orderId: str
    patientId: str
    patientName: str
    patientPhone: str = ""
    totalPrice: int
    paidAmount: int
    pendingAmount: int
    orderDate: int
    daysPending: int = 0


class PendingBalancesBranchReport(BaseModel):
    branchId: str
    branchName: str = ""
    totalPendingAmount: int = 0
    ordersCount: int = 0
    orders: list[PendingBalanceItem]


class PendingBalancesSummary(BaseModel):
    totalPendingAmount: int = 0
    ordersCount: int = 0


class PendingBalancesReportResponse(BaseModel):
    startDate: int
    endDate: int
    summary: PendingBalancesSummary
    byBranch: list[PendingBalancesBranchReport]


# -------------------------------------------------------------
# 5. Reporte de Auditoría de Turnos y Arqueos (CashShifts)
# -------------------------------------------------------------


class ShiftAuditItem(BaseModel):
    shiftId: str
    userId: str
    userName: str = ""
    openedAt: int
    closedAt: int | None = None
    initialBalance: int = 0
    cashBalance: int = 0
    cardBalance: int = 0
    transferBalance: int = 0
    totalBalance: int = 0
    declaredCash: int | None = None
    difference: int | None = None
    notes: str = ""


class ShiftsAuditBranchReport(BaseModel):
    branchId: str
    branchName: str = ""
    totalShifts: int = 0
    totalDiscrepancies: int = 0
    netDifference: int = 0
    shifts: list[ShiftAuditItem]


class ShiftsAuditSummary(BaseModel):
    totalShifts: int = 0
    totalDiscrepancies: int = 0
    netDifference: int = 0


class ShiftsAuditReportResponse(BaseModel):
    startDate: int
    endDate: int
    summary: ShiftsAuditSummary
    byBranch: list[ShiftsAuditBranchReport]
