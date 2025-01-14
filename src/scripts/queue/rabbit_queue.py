import json
from datetime import datetime, timezone
from typing import Dict, Any, Callable

import aio_pika
from aiogram import types, Bot
from psycopg.pq import error_message
from sqlalchemy.util import await_only

from src.config.config import settings
from src.scripts.answer_messages.answer_message import AnswerMessage
from src.utils.logger import setup_logger


class RabbitQueue:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.message_client = AnswerMessage()

    async def connect(self):
        self.connection = await aio_pika.connect_robust(
            settings.get_rabbit_link,
        )

        self.channel = await self.connection.channel()
        await self.init_queue()


    async def stop(self):
        if self.connection:
            await self.connection.close()

    async def init_queue(self):
        try:
            self.logger.info("Initializing queue")

            queues = ["chat_gpt", "claude", "midjourney",]

            for queue_name in queues:
                await self.declare_queue(queue_name)
                self.logger.info(f"Queue {queue_name} initialized")

        except Exception as e:
            self.logger.error(f"Error initializing queues: {e}")
            raise

    async def declare_queue(self, queue_name: str):
        try:
            queue = await self.channel.declare_queue(
                queue_name, arguments={"x-max-priority": 10}
            )
            return queue
        except Exception as e:
            self.logger.error(f"Error declaring queue {queue_name}: {e}")
            raise

    async def publish_message(
        self,
        queue_name: str,
        message: str,
        user_id: int,
        answer_message: int,
        priority: int = 0,
        **kwargs,
    ) -> None:
        try:
            await self.connect()

            queue = await self.declare_queue(queue_name)

            message_body = json.dumps(
                {
                    "retry_count": 0,
                    "message": message,
                    "answer_message": answer_message,
                    "user_id": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ).encode()

            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=message_body,
                    priority=priority,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=queue_name,
            )

            self.logger.info(f"Published message to queue {queue_name}")
        except Exception as e:
            self.logger.error(f"Error publishing message to {queue_name}: {e}")
            raise

    async def consume_messages(self, queue_name: str, callback: Callable, prefetch_count: int = 10) -> None:
        try:
            await self.channel.set_qos(prefetch_count=prefetch_count)
            queue = await self.declare_queue(queue_name)

            async def process_message(message: aio_pika.IncomingMessage) -> None:
                async with message.process():
                    try:
                        body = json.loads(message.body.decode())
                        await callback(body)
                    except Exception as e:
                        self.logger.error(f"Error processing message: {e}")
                        body["text"] = "Ошибка при отправке запроса"

                        await self.message_client.answer_message(body)

                        await self.publish_message(
                            f"{queue_name}_errors",
                            message=body["message"],
                            answer_message=body["answer_message"],
                            user_id=body["user_id"],
                        )

            await queue.consume(process_message)

        except Exception as e:
            self.logger.error(f"Error setting up consumer for {queue_name}: {e}")
            raise