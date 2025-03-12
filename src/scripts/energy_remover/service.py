from typing import Dict, Any, Literal
from src.db.orm.user_orm import UserORM


class EnergyService:
    async def upload_energy(
        self, data: Dict[str, Any], action: Literal["sum", "remove"] = None
    ) -> Dict[str, Any]:
        """Работа с энергией"""

        try:
            if action == "remove":
                text = await UserORM.remove_energy(data["user_id"], data["energy_cost"])
            else:
                text = await UserORM.add_energy(data["user_id"], data["energy_cost"])

            if text.get("error"):
                return {"error": text["error"], "text": text["text"]}

            return text["text"]

        except Exception as e:
            return {"text": "Возникла ошибка"}
