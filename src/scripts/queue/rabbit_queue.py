import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, Callable, Optional, Tuple

import aio_pika
from aio_pika.abc import AbstractIncomingMessage, AbstractChannel, AbstractConnection

from src.config.config import settings
from src.scripts.answer_messages.answer_message import AnswerMessage
from src.utils.logger import setup_logger
from src.utils.redis_cache.redis_cache import redis_manager


class RabbitQueue:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.message_client = AnswerMessage()
        self.connection: Optional[AbstractConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self._is_connected = False
        self._consumers = set()
        self._lock = asyncio.Lock()

    async def connect(self, retry_count: int = 3, retry_delay: int = 5) -> Tuple[AbstractConnection, AbstractChannel]:
        """Устанавливает соединение с RabbitMQ с возможностью повторных попыток."""
        async with self._lock:
            if self._is_connected:
                return self.connection, self.channel

            attempt = 0
            last_exception = None

            while attempt < retry_count:
                attempt += 1
                try:
                    self.connection = await aio_pika.connect_robust(
                        settings.get_rabbit_link,
                        timeout=30,
                        client_properties={"connection_name": "rabbit_queue_service"}
                    )
                    self.channel = await self.connection.channel(publisher_confirms=True)
                    await self.init_queue()
                    self._is_connected = True
                    self.logger.info("Successfully connected to RabbitMQ")
                    return self.connection, self.channel

                except Exception as e:
                    last_exception = e
                    self.logger.error(f"Connection attempt {attempt} failed: {str(e)}")
                    if attempt < retry_count:
                        await asyncio.sleep(retry_delay)

            raise ConnectionError(f"Failed to connect after {retry_count} attempts") from last_exception

    async def stop(self):
        """Аккуратно закрывает все соединения и потребителей."""
        async with self._lock:
            if not self._is_connected:
                return

            try:
                # Отменяем всех потребителей
                for consumer_tag in self._consumers:
                    try:
                        await self.channel.basic_cancel(consumer_tag)
                    except Exception as e:
                        self.logger.warning(f"Error canceling consumer {consumer_tag}: {str(e)}")

                self._consumers.clear()

                if self.channel and not self.channel.is_closed:
                    await self.channel.close()
                    self.channel = None

                if self.connection and not self.connection.is_closed:
                    await self.connection.close()
                    self.connection = None

                self._is_connected = False
                self.logger.info("RabbitMQ connection closed successfully")

            except Exception as e:
                self.logger.error(f"Error during shutdown: {str(e)}")
                raise

    async def init_queue(self):
        """Инициализирует все необходимые очереди."""
        try:
            self.logger.info("Initializing queues")

            queues = [
                "chatgpt",
                "claude",
                "midjourney",
                "upscale_midjourney",
                "select_midjourney",
                "variation_midjourney",
                "referral",
            ]

            for queue_name in queues:
                await self.declare_queue(queue_name)
                self.logger.debug(f"Queue {queue_name} initialized")

        except Exception as e:
            self.logger.error(f"Error initializing queues: {str(e)}")
            await self.stop()
            raise

    async def declare_queue(self, queue_name: str, durable: bool = True) -> aio_pika.Queue:
        """Объявляет очередь с заданными параметрами."""
        try:
            if not self._is_connected:
                await self.connect()

            queue = await self.channel.declare_queue(
                queue_name,
                durable=durable,
                arguments={"x-max-priority": 10}
            )
            return queue
        except Exception as e:
            self.logger.error(f"Error declaring queue {queue_name}: {str(e)}")
            await self.stop()
            raise

    async def publish_message(
        self,
        queue_name: str,
        message: str = None,
        user_id: int = None,
        answer_message: int = None,
        priority: int = 0,
        retry_count: int = 3,
        **kwargs,
    ) -> None:
        """Публикует сообщение в очередь с обработкой ошибок и повторными попытками."""
        attempt = 0
        last_exception = None

        while attempt < retry_count:
            attempt += 1
            try:
                if not self._is_connected:
                    await self.connect()

                message_body = json.dumps({
                    "retry_count": 0,
                    "type": queue_name,
                    "message": message,
                    "answer_message": answer_message,
                    "user_id": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **kwargs,
                }).encode()

                queue = await self.declare_queue(queue_name)

                await self.channel.default_exchange.publish(
                    aio_pika.Message(
                        body=message_body,
                        priority=priority,
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    ),
                    routing_key=queue_name,
                    timeout=10
                )

                self.logger.debug(f"Published message to queue {queue_name}")
                return

            except Exception as e:
                last_exception = e
                self.logger.warning(f"Publish attempt {attempt} failed for queue {queue_name}: {str(e)}")
                if attempt < retry_count:
                    await asyncio.sleep(1)
                    await self.stop()  # Переподключаемся

        error_msg = f"Failed to publish message after {retry_count} attempts"
        self.logger.error(error_msg)
        raise RuntimeError(error_msg) from last_exception

    async def consume_messages(
        self,
        queue_name: str,
        callback: Callable,
        prefetch_count: int = 100,
        durable: bool = True
    ) -> None:
        """Запускает потребителя для очереди с обработкой ошибок."""
        try:
            if not self._is_connected:
                await self.connect()

            await self.channel.set_qos(prefetch_count=prefetch_count)
            queue = await self.declare_queue(queue_name, durable=durable)

            async def process_message(message: AbstractIncomingMessage) -> None:
                try:
                    body = json.loads(message.body.decode())
                    try:
                        await callback(body)
                        await message.ack()
                        
                        await self._key_delete_or_remove(
                            body.get("key", f"{body.get('user_id')}:generate")
                        )
                    except Exception as e:
                        await message.nack(requeue=False)
                        self.logger.error(f"Error processing message: {str(e)}")
                        
                        body["text"] = "Ошибка при отправке запроса"
                        await self.message_client.answer_message(body)
                        
                        await self.publish_message(
                            f"{queue_name}_errors",
                            message=body["message"],
                            answer_message=body["answer_message"],
                            user_id=body["user_id"],
                        )
                        
                        await self._key_delete_or_remove(
                            body.get("key", f"{body.get('user_id')}:generate")
                        )
                except json.JSONDecodeError as e:
                    await message.reject(requeue=False)
                    self.logger.error(f"Invalid JSON in message: {str(e)}")
                except Exception as e:
                    await message.reject(requeue=False)
                    self.logger.error(f"Unexpected error in message processing: {str(e)}")

            consumer_tag = await queue.consume(process_message)
            self._consumers.add(consumer_tag)
            self.logger.info(f"Started consuming messages from {queue_name}")

        except Exception as e:
            self.logger.error(f"Error setting up consumer for {queue_name}: {str(e)}")
            await self.stop()
            raise

    async def _key_delete_or_remove(self, key: str) -> None:
        """Удаляет или обновляет ключ в Redis."""
        try:
            data = await redis_manager.get(key)
            if isinstance(data, str):
                await redis_manager.delete(key)
            elif isinstance(data, dict):
                data["active_generate"] = max(0, data.get("active_generate", 0) - 1)
                await redis_manager.set(key, data, ttl=3600)
        except Exception as e:
            self.logger.error(f"Error updating Redis key {key}: {str(e)}")

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Возвращает статистику по всем очередям."""
        try:
            if not self._is_connected:
                await self.connect()

            queues = [
                "chatgpt", "claude", "midjourney",
                "upscale_midjourney", "select_midjourney",
                "variation_midjourney", "referral"
            ]

            stats = {}
            for queue_name in queues:
                try:
                    queue = await self.declare_queue(queue_name)
                    stats[queue_name] = {
                        "name": queue_name,
                        "message_count": queue.declaration_result.message_count,
                        "consumer_count": queue.declaration_result.consumer_count,
                        "status": "active" if queue.declaration_result.message_count > 0 else "empty"
                    }
                except Exception as e:
                    stats[queue_name] = {
                        "name": queue_name,
                        "error": str(e),
                        "status": "error"
                    }

            return stats
        except Exception as e:
            self.logger.error(f"Error getting queue stats: {str(e)}")
            await self.stop()
            raise

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


# Пример использования
model = RabbitQueue()


async def example_usage():
    async with RabbitQueue() as rabbit:
        # Публикация сообщения
        await rabbit.publish_message(
            queue_name="chatgpt",
            message="Hello world",
            user_id=123,
            answer_message=456,
            priority=5
        )
        
        # Подписка на сообщения
        async def message_handler(message: Dict):
            print(f"Received message: {message}")
        
        await rabbit.consume_messages("chatgpt", message_handler)
        
        # Бесконечное ожидание (в реальном коде используйте asyncio.Event)
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(example_usage())