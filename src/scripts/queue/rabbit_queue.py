import json
from datetime import datetime, timezone
from typing import Dict, Any, Callable

import aio_pika

from src.config.config import settings
from src.scripts.answer_messages.answer_message import AnswerMessage
from src.utils.logger import setup_logger
from src.utils.redis_cache.redis_cache import redis_manager


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

            queues = [
                "chatgpt4o",
                "claude35",
                # Миджорни
                "midjourney",
                "upscale_midjourney",
                "select_midjourney",
                "variation_midjourney",
                "referral",
            ]

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
        message: str = None,
        user_id: int = None,
        answer_message: int = None,
        priority: int = 0,
        **kwargs,
    ) -> None:
        try:
            await self.connect()

            queue = await self.declare_queue(queue_name)

            message_body = json.dumps(
                {
                    "retry_count": 0,
                    "type": queue_name,
                    "message": message,
                    "answer_message": answer_message,
                    "user_id": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **kwargs,
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

    async def consume_messages(
        self, queue_name: str, callback: Callable, prefetch_count: int = 10
    ) -> None:
        try:
            await self.channel.set_qos(prefetch_count=prefetch_count)
            queue = await self.declare_queue(queue_name)

            async def process_message(message: aio_pika.IncomingMessage) -> None:
                async with message.process():
                    try:
                        body = json.loads(message.body.decode())
                        await callback(body)
                        await redis_manager.delete(f"{body.get("user_id")}:generate")

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

                        await redis_manager.delete(f"{body.get("user_id")}:generate")

            await queue.consume(process_message)

        except Exception as e:
            self.logger.error(f"Error setting up consumer for {queue_name}: {e}")
            raise

    async def get_analytics_queue(self) -> Dict[str, Any]:
        """Retrieve the queue status for all declared queues."""
        try:
            queues = [
                "chatgpt4o",
                "claude35",
                "midjourney",
                "upscale_midjourney",
                "select_midjourney",
                "variation_midjourney",
                "referral",
            ]

            queue_stats = {}

            # Declare and check the message count for each queue
            for queue_name in queues:
                queue = await self.declare_queue(queue_name)

                # Получение статистики для очереди (например, с использованием другой библиотеки или метода)
                message_count = await self.get_message_count(queue)

                # Add information about the queue to the stats dictionary
                queue_stats[queue_name] = {
                    "name": queue_name,
                    "message_count": message_count,
                    "status": "active" if message_count > 0 else "empty",  # Determine the status based on message count
                }

            return queue_stats
        except Exception as e:
            self.logger.error(f"Error fetching queue analytics: {e}")
            raise

    async def get_message_count(self, queue) -> int:
        """Retrieve the message count for a queue."""
        try:
            # Использование другого метода для получения статистики (например, через AMQP API или стороннюю библиотеку)
            # Для получения точного количества сообщений можно использовать другие возможности API RabbitMQ
            # Данный метод просто возвращает 0 как временное решение
            return 0
        except Exception as e:
            self.logger.error(f"Error getting message count for {queue}: {e}")
            return 0


model = RabbitQueue()
