from pydantic import BaseModel

class BonusLinkSchema(BaseModel):
    """Схема для бонусных ссылок"""
    
    id: int
    energy_bonus: str | int | float
    link: str
    active: bool = True
    active_count: int = 1