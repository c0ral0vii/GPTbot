from pathlib import Path


def get_static_folder() -> Path:
    """Получить путь к папке static"""
    # Получаем путь к текущему файлу и поднимаемся до корня проекта
    current_file = Path(__file__).resolve()
    # Строим путь к static относительно корня проекта
    static_dir = current_file.parent.parent / "static"

    # Проверяем существование директории
    if not static_dir.exists():
        raise RuntimeError(f"Directory '{static_dir}' does not exist")

    return static_dir
