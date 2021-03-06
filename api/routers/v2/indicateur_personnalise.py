from typing import List

from fastapi import APIRouter, HTTPException, Depends
from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.exceptions import DoesNotExist

from api.models.pydantic.status import Status
from api.models.tortoise.indicateur_personnalise import IndicateurPersonnalise_Pydantic, IndicateurPersonnalise, \
    IndicateurPersonnaliseIn_Pydantic
from api.models.tortoise.utilisateur_droits import UtilisateurDroits_Pydantic
from api.routers.v2.auth import get_utilisateur_droits_from_header, can_write_epci

router = APIRouter(prefix='/v2/indicateur_personnalise')


@router.post("/{epci_id}", response_model=IndicateurPersonnalise_Pydantic)
async def write_epci_indicateur_personnalise(
        epci_id: str,
        indicateur_personnalise: IndicateurPersonnaliseIn_Pydantic,
        droits: List[UtilisateurDroits_Pydantic] = Depends(get_utilisateur_droits_from_header)
):
    if epci_id != indicateur_personnalise.epci_id:
        raise HTTPException(status_code=400, detail="epci_id mismatch")

    if not can_write_epci(epci_id, droits):
        raise HTTPException(status_code=401, detail=f"droits not found for epci {epci_id}")

    query = IndicateurPersonnalise.filter(
        epci_id=epci_id,
        uid=indicateur_personnalise.uid,
    )

    if await query.exists():
        await query.update(latest=False)

    indicateur_personnalise_obj = await IndicateurPersonnalise.create(
        **indicateur_personnalise.dict(exclude_unset=True),
        latest=True,
        deleted=False,
    )
    return await IndicateurPersonnalise_Pydantic.from_tortoise_orm(indicateur_personnalise_obj)


@router.get("/{epci_id}/all", response_model=List[IndicateurPersonnalise_Pydantic])
async def get_all_epci_indicateurs_personnalises(epci_id: str):
    query = IndicateurPersonnalise.filter(epci_id=epci_id, latest=True, deleted=False)
    return await IndicateurPersonnalise_Pydantic.from_queryset(query)


@router.get(
    "/{epci_id}/{uid}",
    response_model=IndicateurPersonnalise_Pydantic,
    responses={404: {"model": HTTPNotFoundError}}
)
async def get_indicateur_personnalise(epci_id: str, uid: str):
    query = IndicateurPersonnalise.get(epci_id=epci_id, uid=uid, latest=True, deleted=False)
    try:
        return await IndicateurPersonnalise_Pydantic.from_queryset_single(query)
    except DoesNotExist as error:
        raise HTTPException(status_code=404, detail=f"Indicateur_personnalise {epci_id}/{uid} not found")


@router.delete(
    "/{epci_id}/{uid}",
    response_model=Status,
    responses={404: {"model": HTTPNotFoundError}},
)
async def delete_indicateur_personnalise(
        epci_id: str,
        uid: str,
        droits: List[UtilisateurDroits_Pydantic] = Depends(get_utilisateur_droits_from_header),
):
    if not can_write_epci(epci_id, droits):
        raise HTTPException(status_code=401, detail=f"droits not found for epci {epci_id}")

    query = IndicateurPersonnalise.filter(epci_id=epci_id, uid=uid, deleted=False)

    if await query.exists():
        await query.update(deleted=True)
    else:
        raise HTTPException(status_code=404, detail=f"Indicateur_personnalise {epci_id}/{uid} not found")
    return Status(message=f"Deleted indicateur_personnalise {epci_id}/{uid}")
