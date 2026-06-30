import os
import sys
import asyncio

CWD_PATH = os.getcwd()
SOURCE_PATH = os.path.join(CWD_PATH, "app")
sys.path.append(SOURCE_PATH)

os.environ["MONGO_URL"] = "mongodb://localhost:27017"

from services.mongo_service import MongoService
from repos.v1.lab_tests.lab_tests_repository import LabTestsRepository
from repos.v1.exams.exams_repository import ExamsRepository
from repos.v1.quotations.quotations_repository import QuotationsRepository
from repos.v1.orders.orders_repository import OrdersRepository
from repos.v1._shared_models import ReferenceValue, IncludedTest
from repos.v1.lab_tests.models.lab_test_model import CreateLabTest, UpdateLabTest
from repos.v1.exams.models.exam_model import CreateExam, UpdateExam
from repos.v1.quotations.models.quotation_model import CreateQuotation, UpdateQuotation, QuotedExam
from repos.v1.orders.models.order_model import CreateOrder, UpdateOrder, OrderTestResult


async def main():
    await MongoService().init_service()

    lt_repo = LabTestsRepository.get_instance()
    ex_repo = ExamsRepository.get_instance()
    qt_repo = QuotationsRepository.get_instance()
    or_repo = OrdersRepository.get_instance()

    # ===== 1. LabTest CRUD =====
    print("=== LabTest ===")
    ref = ReferenceValue(
        patientType="adult", gender="male",
        minAgeDays=6570, maxAgeDays=23725,
        minValue=70.0, maxValue=110.0,
    )
    lt = CreateLabTest(
        parameterName="Fasting Glucose",
        medicalClassification="Chemistry",
        dataType="float",
        unitOfMeasure="mg/dL",
        referenceValues=[ref],
    )
    created_lt = await lt_repo.create_lab_test(lt)
    print(f"  CREATE: {created_lt.id} - {created_lt.parameterName} [{created_lt.unitOfMeasure}] refs={len(created_lt.referenceValues)}")

    all_lt = await lt_repo.get_all_lab_tests()
    print(f"  GET ALL: {len(all_lt)} tests")

    found = await lt_repo.get_lab_test_by_id(created_lt.id)
    assert found is not None
    print(f"  GET BY ID: {found.parameterName} OK")

    updated = await lt_repo.update_lab_test_by_id(created_lt.id, UpdateLabTest(parameterName="Glucose (Fasting)"))
    assert updated.parameterName == "Glucose (Fasting)"
    print(f"  UPDATE: {updated.parameterName} OK")

    deleted = await lt_repo.delete_lab_test_by_id(created_lt.id)
    assert deleted.isDeleted is True
    print(f"  DELETE: isDeleted={deleted.isDeleted} OK")

    # ===== 2. Exam CRUD =====
    print("=== Exam ===")
    inc = IncludedTest(
        labTestId=created_lt.id,
        parameterName="Fasting Glucose",
        medicalClassification="Chemistry",
        dataType="float",
        unitOfMeasure="mg/dL",
        referenceValues=[ref],
    )
    exam = CreateExam(
        name="Perfil Lipidico Completo",
        commercialCategory="Quimica Clinica",
        salePrice=25050,
        currency="MXN",
        includedTests=[inc],
    )
    created_exam = await ex_repo.create_exam(exam)
    print(f"  CREATE: {created_exam.id} - {created_exam.name} price={created_exam.salePrice} tests={len(created_exam.includedTests)}")
    assert created_exam.salePrice == 25050
    assert isinstance(created_exam.salePrice, int)

    all_ex = await ex_repo.get_all_exams()
    print(f"  GET ALL: {len(all_ex)} exams")

    found_ex = await ex_repo.get_exam_by_id(created_exam.id)
    assert found_ex is not None
    print(f"  GET BY ID: {found_ex.name} OK")

    updated_ex = await ex_repo.update_exam_by_id(created_exam.id, UpdateExam(name="Perfil Lipidico Basico", salePrice=20000))
    assert updated_ex.name == "Perfil Lipidico Basico"
    assert updated_ex.salePrice == 20000
    print(f"  UPDATE: {updated_ex.name} price={updated_ex.salePrice} OK")

    deleted_ex = await ex_repo.delete_exam_by_id(created_exam.id)
    assert deleted_ex.isDeleted is True
    print(f"  DELETE: isDeleted={deleted_ex.isDeleted} OK")

    # ===== 3. Quotation CRUD =====
    print("=== Quotation ===")
    qe = QuotedExam(examId=created_exam.id, examName="Perfil Lipidico Basico", quotedPrice=20000)
    quot = CreateQuotation(
        clientName="Maria Garcia Lopez",
        patientId=None,
        exams=[qe],
        totalAmount=20000,
        status="pending",
    )
    created_qt = await qt_repo.create_quotation(quot)
    print(f"  CREATE: {created_qt.id} - {created_qt.clientName} total={created_qt.totalAmount} status={created_qt.status}")
    assert created_qt.totalAmount == 20000
    assert isinstance(created_qt.totalAmount, int)

    all_qt = await qt_repo.get_all_quotations()
    print(f"  GET ALL: {len(all_qt)} quotations")

    found_qt = await qt_repo.get_quotation_by_id(created_qt.id)
    assert found_qt is not None
    print(f"  GET BY ID: {found_qt.clientName} OK")

    updated_qt = await qt_repo.update_quotation_by_id(created_qt.id, UpdateQuotation(status="accepted", patientId="p-test-123"))
    assert updated_qt.status == "accepted"
    assert updated_qt.patientId == "p-test-123"
    print(f"  UPDATE: status={updated_qt.status} patientId={updated_qt.patientId} OK")

    deleted_qt = await qt_repo.delete_quotation_by_id(created_qt.id)
    assert deleted_qt.isDeleted is True
    print(f"  DELETE: isDeleted={deleted_qt.isDeleted} OK")

    # ===== 4. Order CRUD =====
    print("=== Order ===")
    order_result = OrderTestResult(
        labTestId=created_lt.id,
        parameterName="Glucose (Fasting)",
        medicalClassification="Chemistry",
        dataType="float",
        unitOfMeasure="mg/dL",
        referenceValues=[ref],
        resultValue="95.5",
        alertFlag="normal",
    )
    order = CreateOrder(
        patientId="p-test-123",
        quotationId=created_qt.id,
        examId=created_exam.id,
        examName="Perfil Lipidico Basico",
        salePriceApplied=20000,
        status="pending",
        results=[order_result],
    )
    created_or = await or_repo.create_order(order)
    print(f"  CREATE: {created_or.id} - exam={created_or.examName} results={len(created_or.results)}")
    assert created_or.salePriceApplied == 20000
    assert isinstance(created_or.salePriceApplied, int)

    all_or = await or_repo.get_all_orders()
    print(f"  GET ALL: {len(all_or)} orders")

    found_or = await or_repo.get_order_by_id(created_or.id)
    assert found_or is not None
    assert found_or.results[0].resultValue == "95.5"
    assert found_or.results[0].alertFlag == "normal"
    print(f"  GET BY ID: patientId={found_or.patientId} status={found_or.status}")
    print(f"    Result[0]: value={found_or.results[0].resultValue} alert={found_or.results[0].alertFlag} OK")

    updated_or = await or_repo.update_order_by_id(created_or.id, UpdateOrder(status="completed"))
    assert updated_or.status == "completed"
    print(f"  UPDATE: status={updated_or.status} OK")

    delete_or = await or_repo.delete_order_by_id(created_or.id)
    assert delete_or.isDeleted is True
    print(f"  DELETE: isDeleted={delete_or.isDeleted} OK")

    # ===== Final Summary =====
    print()
    print("=== FINAL STATE ===")
    all_lt = await lt_repo.get_all_lab_tests()
    all_ex = await ex_repo.get_all_exams()
    all_qt = await qt_repo.get_all_quotations()
    all_or = await or_repo.get_all_orders()
    print(f"  LabTests in DB: {len(all_lt)}")
    print(f"  Exams in DB: {len(all_ex)}")
    print(f"  Quotations in DB: {len(all_qt)}")
    print(f"  Orders in DB: {len(all_or)}")

    # Cleanup test data
    from services.mongo_collections.v1 import LabTestsCollection, ExamsCollection, QuotationsCollection, OrdersCollection
    await LabTestsCollection.get_instance()._collection.delete_many({})
    await ExamsCollection.get_instance()._collection.delete_many({})
    await QuotationsCollection.get_instance()._collection.delete_many({})
    await OrdersCollection.get_instance()._collection.delete_many({})
    print("  Test data cleaned up")

    print()
    print("===== ALL 4 ENTITIES FULL CRUD PASSED (int cents) =====")


if __name__ == "__main__":
    asyncio.run(main())
