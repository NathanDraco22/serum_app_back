from serum.repos.v1.branches.models.branch_model import (
    AuxBioanalyst,
    BioanalystInfo,
    BranchBioanalyst,
    BranchInDb,
    CreateBranch,
    UpdateBranch,
)
from serum.repos.v1.common.models.user_info import UserInfo


def test_branch_bioanalyst_model():
    # 1. Crear sucursal sin bioanalista (retrocompatibilidad)
    branch_data = {
        "name": "Sucursal Matriz",
        "address": "Calle Central #123",
        "phone": "555-0101",
    }
    create_dto = CreateBranch(**branch_data)
    assert create_dto.bioanalyst is None
    assert create_dto.auxBio == []

    branch_db = BranchInDb(
        id="branch-001",
        createdAt=1700000000000,
        **create_dto.model_dump(),
    )
    assert branch_db.bioanalyst is None
    assert branch_db.auxBio == []

    # 2. Crear sucursal con bioanalista y bioanalistas auxiliares
    bioanalyst_data = {
        "name": "Lic. Joselin Lopez",
        "title": "TECNOLOGO MEDICO",
        "code": "Codigo MINSA 88027",
    }
    bioanalyst = BranchBioanalyst(**bioanalyst_data)
    assert bioanalyst.name == "Lic. Joselin Lopez"
    assert bioanalyst.title == "TECNOLOGO MEDICO"
    assert bioanalyst.code == "Codigo MINSA 88027"

    aux_bio = AuxBioanalyst(
        user=UserInfo(id="usr-123", name="Joselin Auxiliar"),
        bioanalyst=BioanalystInfo(
            name="Lic. Joselin Lopez",
            title="TECNOLOGO MEDICO",
            code="Codigo MINSA 88027",
            sealUrl="https://cdn.example.com/seals/aux_seal.png",
        ),
    )

    create_with_bio = CreateBranch(
        **branch_data,
        bioanalyst=bioanalyst,
        auxBio=[aux_bio],
    )
    assert create_with_bio.bioanalyst is not None
    assert create_with_bio.bioanalyst.name == "Lic. Joselin Lopez"
    assert len(create_with_bio.auxBio) == 1
    assert create_with_bio.auxBio[0].user.name == "Joselin Auxiliar"
    assert (
        create_with_bio.auxBio[0].bioanalyst.sealUrl
        == "https://cdn.example.com/seals/aux_seal.png"
    )

    dumped = create_with_bio.model_dump()
    assert dumped["bioanalyst"]["title"] == "TECNOLOGO MEDICO"
    assert dumped["bioanalyst"]["code"] == "Codigo MINSA 88027"
    assert len(dumped["auxBio"]) == 1
    assert dumped["auxBio"][0]["user"]["id"] == "usr-123"

    # 3. UpdateBranch con bioanalista y auxBio
    update_dto = UpdateBranch(
        bioanalyst=BioanalystInfo(
            name="Lic. Carlos Martinez",
            title="BIOANALISTA CLINICO",
            code="Codigo MINSA 99112",
            sealUrl="https://cdn.example.com/seals/carlos.png",
        ),
        auxBio=[aux_bio],
    )
    assert update_dto.bioanalyst is not None
    assert update_dto.bioanalyst.name == "Lic. Carlos Martinez"
    assert update_dto.bioanalyst.sealUrl == "https://cdn.example.com/seals/carlos.png"
    assert update_dto.auxBio is not None
    assert len(update_dto.auxBio) == 1
