from serum.repos.v1.branches.models.branch_model import (
    BranchBioanalyst,
    BranchInDb,
    CreateBranch,
    UpdateBranch,
)


def test_branch_bioanalyst_model():
    # 1. Crear sucursal sin bioanalista (retrocompatibilidad)
    branch_data = {
        "name": "Sucursal Matriz",
        "address": "Calle Central #123",
        "phone": "555-0101",
    }
    create_dto = CreateBranch(**branch_data)
    assert create_dto.bioanalyst is None

    branch_db = BranchInDb(
        id="branch-001",
        createdAt=1700000000000,
        **create_dto.model_dump(),
    )
    assert branch_db.bioanalyst is None

    # 2. Crear sucursal con bioanalista
    bioanalyst_data = {
        "name": "Lic. Joselin Lopez",
        "title": "TECNOLOGO MEDICO",
        "code": "Codigo MINSA 88027",
    }
    bioanalyst = BranchBioanalyst(**bioanalyst_data)
    assert bioanalyst.name == "Lic. Joselin Lopez"
    assert bioanalyst.title == "TECNOLOGO MEDICO"
    assert bioanalyst.code == "Codigo MINSA 88027"

    create_with_bio = CreateBranch(
        **branch_data,
        bioanalyst=bioanalyst,
    )
    assert create_with_bio.bioanalyst is not None
    assert create_with_bio.bioanalyst.name == "Lic. Joselin Lopez"

    dumped = create_with_bio.model_dump()
    assert dumped["bioanalyst"]["title"] == "TECNOLOGO MEDICO"
    assert dumped["bioanalyst"]["code"] == "Codigo MINSA 88027"

    # 3. UpdateBranch con bioanalista
    update_dto = UpdateBranch(
        bioanalyst=BranchBioanalyst(
            name="Lic. Carlos Martinez",
            title="BIOANALISTA CLINICO",
            code="Codigo MINSA 99112",
        )
    )
    assert update_dto.bioanalyst is not None
    assert update_dto.bioanalyst.name == "Lic. Carlos Martinez"
