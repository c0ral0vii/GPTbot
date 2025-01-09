import asyncio
from src.scripts.antropic.claude_gpt import ClaudeGPT
from src.scripts.chat_gpt.chat_gpt_o1 import ChatGPT
from src.utils.logger import setup_logger
from src.utils.queue.rabbit_queue import RabbitQueue

class QueueWorker:
    def __init__(self):
        self.queue_service = RabbitQueue()

        self.claude = ClaudeGPT()
        self.chat_gpt = ChatGPT()

        self.logger = setup_logger(__name__)

    async def start(self):
        """Запуск воркера"""

        try:
            await self.queue_service.connect()

            queues = ["chat_gpt_o1", "claude", "gpt_assist",
                      "midjourney", "flux", "dall_e", "stable_diffusion",
                      "openai codex", "openai_whisper", "tts", "deepl", "speechmatics",
                      "openai_embeddings"]

            for queue_name in queues:
                await self.queue_service.declare_queue(queue_name)
                await self.queue_service.declare_queue(f"{queue_name}_errors")

            await self.queue_service.consume_messages(
                "chat_gpt_o1",
                self.chat_gpt.send_message,
            )

            await self.queue_service.consume_messages(
                "claude",
                self.claude.send_message,
            )

            self.logger.info("queue worker started successfully")

        except Exception as e:
            self.logger.error(f"Error starting parsing worker: {e}")
            raise


async def worker_start():
    worker = QueueWorker()
    await worker.start()

