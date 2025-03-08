from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserLoginSchema(BaseModel):
    username: str
    password: str