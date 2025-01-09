# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем необходимые системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Добавляем Poetry в PATH
ENV PATH="/root/.local/bin:${PATH}"

# Копируем файлы проекта
COPY pyproject.toml poetry.lock ./

# Устанавливаем зависимости проекта с помощью Poetry (без установки текущего проекта)
RUN poetry install --no-root

# Копируем остальные файлы проекта
COPY . .

# Команда для запуска приложения
CMD ["poetry", "run", "python", "main.py"]