from src.scripts.answer_messages.answer_message import AnswerMessage
from src.scripts.antropic.claude_gpt import ClaudeGPT
from src.scripts.chat_gpt.chat_gpt import ChatGPT
from src.scripts.midjourney.service import MidjourneyService
from src.utils.logger import setup_logger
from src.scripts.queue.rabbit_queue import RabbitQueue


class QueueWorker:
    def __init__(self):
        self.queue_service = RabbitQueue()

        self.claude = ClaudeGPT()
        self.chat_gpt = ChatGPT()

        self.message_service = AnswerMessage()

        self.midjourney = MidjourneyService()

        self.logger = setup_logger(__name__)

    async def start(self):
        """Запуск воркера"""

        try:
            await self.queue_service.connect()

            queues = [
                "gpt_assistant",
                "chatgpt",
                "claude",
                # Миджорни
                "midjourney",
                "upscale_midjourney",
                "select_midjourney",
                "variation_midjourney",
                "referral",
            ]
            for queue_name in queues:
                await self.queue_service.declare_queue(queue_name)
                await self.queue_service.declare_queue(f"{queue_name}_errors")

            await self.queue_service.consume_messages(
                "gpt_assistant", self.chat_gpt.send_message_assistant
            )

            await self.queue_service.consume_messages(
                "chatgpt",
                self.chat_gpt.send_message,
            )

            await self.queue_service.consume_messages(
                "claude",
                self.claude.send_message,
            )

            await self.queue_service.consume_messages(
                "midjourney",
                self.midjourney.generate_photo,
            )

            await self.queue_service.consume_messages(
                "referral",
                self.message_service.send_referral_message,
            )

            await self.queue_service.consume_messages(
                "refresh_midjourney", self.midjourney.refresh_generate
            )

            await self.queue_service.consume_messages(
                "upscale_midjourney", self.midjourney.upscale_photo
            )

            await self.queue_service.consume_messages(
                "variation_midjourney", self.midjourney.vary_photo
            )

            self.logger.info("queue worker started successfully")

        except Exception as e:
            self.logger.error(f"Error starting parsing worker: {e}")
            raise


async def worker_start():
    worker = QueueWorker()
    await worker.start()
