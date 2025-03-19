FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install poetry
RUN poetry install --no-root


CMD ["poetry", "run", "gunicorn", "run_admin_panel:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]