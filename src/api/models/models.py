from pydantic import BaseModel
from typing import Optional, List, Dict


class UserLoginSchema(BaseModel):
    username: str
    password: str


class ChangeUserSchema(BaseModel):
    banned_user: Optional[bool] = False
    energy: int
    premium_active: Optional[bool] = False
    referral_link: Optional[str]
    use_referral_link: Optional[str] = None
    user_id: int

    premium_dates: Optional[Dict[str, str]] = None
