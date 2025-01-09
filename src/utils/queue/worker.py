from src.scripts.antropic.claude_gpt import ClaudeGPT
from src.utils.logger import setup_logger
from src.utils.queue.rabbit_queue import RabbitQueue


class QueueWorker:
    def __init__(self):
        self.queue_service = RabbitQueue()

        self.claude = ClaudeGPT()

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
                ...
            )

            await self.queue_service.consume_messages(
                "claude",
                ...
            )

            self.logger.info("Parsing worker started successfully")

        except Exception as e:
            self.logger.error(f"Error starting parsing worker: {e}")
            raise
