FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /srv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY app ./app

FROM python:3.12-slim
RUN useradd --uid 10001 --create-home opspilot
WORKDIR /srv
COPY --from=build /srv /srv
ENV PATH="/srv/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER 10001
CMD ["uvicorn", "app.main_api:app", "--host", "0.0.0.0", "--port", "8000"]
