from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class UserLoginSchema(BaseModel):
    username: str
    password: str


class ChangeUserSchema(BaseModel):
    banned_user: Optional[bool] = False
    energy: int
    premium_active: Optional[bool] = False
    use_referral_link: Optional[int] = None
    user_id: int
    personal_percent: int
    referral_bonus: int

    auto_renewal: Optional[bool] = False
    premium_dates: Optional[Dict[str, str]] = None


class PaymentSchema(BaseModel):
    type: str
    event: str
    object: Dict[str, Any]


class SpamData(BaseModel):
    spamText: str
    forPremium: bool = False
    forRegular: bool = False