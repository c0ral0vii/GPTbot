import pytest
from unittest.mock import AsyncMock, patch
from src.scripts.spammer.service import TelegramBroadcaster


@pytest.mark.asyncio
async def test_send_message_success():
    broadcaster = TelegramBroadcaster("fake-token")
    broadcaster._bot.send_message = AsyncMock(return_value=True)

    success = await broadcaster.send_message(123456789, "Hello")
    assert success is True


@pytest.mark.asyncio
async def test_send_message_failure():
    broadcaster = TelegramBroadcaster("fake-token")
    broadcaster._bot.send_message = AsyncMock(side_effect=Exception("Send error"))

    success = await broadcaster.send_message(123456789, "Hello")
    assert success is False


@pytest.mark.asyncio
async def test_send_photo_success(tmp_path):
    photo = tmp_path / "photo.jpg"
    photo.write_text("fake image content")

    broadcaster = TelegramBroadcaster("fake-token")
    broadcaster._bot.send_photo = AsyncMock(return_value=True)

    success = await broadcaster.send_photo(123456789, str(photo), "caption")
    assert success is True


@pytest.mark.asyncio
async def test_broadcast_text(monkeypatch):
    broadcaster = TelegramBroadcaster("fake-token")
    broadcaster._get_user_ids = AsyncMock(return_value=[111, 222])
    broadcaster.send_message = AsyncMock(return_value=True)

    await broadcaster.broadcast(text="Broadcast test")
    broadcaster.send_message.assert_any_call(111, "Broadcast test")
    broadcaster.send_message.assert_any_call(222, "Broadcast test")


@pytest.mark.asyncio
async def test_broadcast_photo(monkeypatch, tmp_path):
    photo = tmp_path / "img.jpg"
    photo.write_text("img content")

    broadcaster = TelegramBroadcaster("fake-token")
    broadcaster._get_user_ids = AsyncMock(return_value=[333])
    broadcaster.send_photo = AsyncMock(return_value=True)

    await broadcaster.broadcast(photo_path=str(photo), caption="image caption")
    broadcaster.send_photo.assert_called_with(333, str(photo), "image caption")
