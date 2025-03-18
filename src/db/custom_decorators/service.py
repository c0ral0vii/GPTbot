from functools import wraps

from src.db.database import async_session


def with_session(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        session = kwargs.get("session")
        new_session = False

        if session is None:
            session = async_session()
            kwargs["session"] = session
            new_session = True

        try:
            return await func(*args, **kwargs)
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            if new_session:
                await session.close()

    return wrapper
