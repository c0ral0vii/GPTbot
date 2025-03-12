from enum import Enum

class GPTConfig(Enum):
    GPT_VERSION_4o = "chatgpt4o"

class CLAUDEConfig(Enum):
    CLAUDE_VERSION_SONNET = "claude37"
    CLAUDE_VERSION_HAIKU = "claude35"

class ImageGPTConfig(Enum):
    ...

class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"

