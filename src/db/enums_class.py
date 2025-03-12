from enum import Enum


class GPTConfig(Enum):
    GPT_VERSION_4o = "gpt-4o"
    GPT_VERSION_4o_mini = "gpt-4o-mini"
    GPT_VERSION_o1 = "o1"
    GPT_VERSION_45 = "gpt-4.5-preview"


class CLAUDEConfig(Enum):
    CLAUDE_VERSION_SONNET = "claude-3-5-sonnet-latest"
    CLAUDE_VERSION_HAIKU = "claude-3-5-haiku-latest"


# class ImageGPTConfig(Enum):
#     ...


class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
