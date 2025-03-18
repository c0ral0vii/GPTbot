from fastapi import HTTPException
from fastapi.responses import JSONResponse

from src.api.models import BonusLinkSchema
from src.api.v1.routes import router
from src.db.orm.bonus_links_orm import BonusLinksOrm


@router.get("/bonuses")
async def get_all_bonuses():
    try:
        all_bonus_links = await BonusLinksOrm.get_all_bonuses()
        
        return JSONResponse(
            content={"items": all_bonus_links},
            status_code=200
        )
    except  Exception as e:
        raise HTTPException(status_code=500, 
                            detail=e)
    

@router.get("/bonuses/{id}/info")
async def get_info_bonuse(id: int):
    try:
        bonus_link = await BonusLinksOrm.get_bonus_link(
            link_id=id
        )
        
        return JSONResponse(
            content={},
            status_code=200
        )
    except:
        raise HTTPException(status_code=500)
    

@router.delete("/bonuses/{id}/delete")
async def delete_bonuse(id: int):
    try:

        return JSONResponse(
            content={},
            status_code=200
        )
    except:
        raise HTTPException(status_code=500)
    

@router.put("/bonuses/{id}/change")
async def change_bonuse(id: int):
    try:

        return JSONResponse(
            content={},
            status_code=200
        )
    except:
        raise HTTPException(status_code=500)
    

@router.post("/bonuses/create")
async def change_bonuse(bonus_link_data: BonusLinkSchema):
    try:
        new_bonus_link = await BonusLinksOrm.create_bonus_links(
            bonus_link_data.model_dump()
        )
        return JSONResponse(
            content={},
            status_code=201
        )
    except:
        raise HTTPException(status_code=500)