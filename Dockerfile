FROM python:3.12-slim

WORKDIR /app

# Устанавливаем необходимые системные зависимости
#RUN apt-get update && apt-get install -y --no-install-recommends \
#    curl \
#    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

#ENV PATH="/root/.local/bin:${PATH}"

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

COPY . .

CMD ["poetry", "run", "python", "main.py"]