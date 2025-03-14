import datetime
from src.scripts.answer_messages.answer_message import AnswerMessage
from src.db.orm.user_orm import UserORM

answer_model = AnswerMessage()
PREMIUM_TEXT = "Поздравляем с покупкой подписки! 🎉 Теперь у вас есть доступ ко всем премиум-услугам и эксклюзивным возможностям! 🚀 Наслаждайтесь улучшенным опытом и не стесняйтесь обращаться, если у вас возникнут вопросы. Мы рады, что вы с нами! 😊 \n\n 🟢На ваш баланс в скором времени будет зачислено 2500 ⚡ генераций 🎉"
PREMIUM_ENERGY_ADD = 2500


async def premium_notification(data) -> None:
    data["text"] = PREMIUM_TEXT

    await UserORM.add_energy(user_id=data["user_id"], count=PREMIUM_ENERGY_ADD)
    await UserORM.create_premium_user(user_id=data["user_id"])

    await answer_model.send_notification(data)
