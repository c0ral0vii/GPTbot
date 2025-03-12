from src.db.models import Dialog
from src.db.orm.config_orm import ConfigORM
from src.db.orm.dialog_orm import DialogORM


async def _get_user_config_and_get_model(user_id: int, select_model: str):
    """Получение конфига пользователя и модели"""

    user_config = await ConfigORM.get_config(user_id=user_id)

    if select_model == "chatgpt":
        return user_config.gpt_select

    if select_model == "claude":
        return user_config.claude_select


async def _get_dialogs(user_id: int, select_model: str) -> list[Dialog]:
    """Получение диалогов для модели"""

    dialogs = await DialogORM.get_dialogs(
        user_id=user_id,
        select_model=select_model,
    )

    return dialogs


async def _get_dialog(dialog_id: int) -> Dialog:
    """Получение диалога"""

    dialog = await DialogORM.get_dialog(
        dialog_id=dialog_id,
    )

    return dialog


async def _create_new_dialog(user_id: int, select_model: str):
    """Создание нового диалога"""

    dialog = await DialogORM.create_dialog(user_id=user_id, select_model=select_model)

    return dialog
