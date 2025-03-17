from pydantic import BaseModel


class GPTAssistSchema(BaseModel):
    id: int = None
    title: str = None
    comment: str = None
    assistant_id: str
    energy_cost: int | float | str = 10
    premium_free: bool = False
    disable: bool = False
