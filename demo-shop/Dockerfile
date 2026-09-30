FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /srv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY shop ./shop
COPY loadgen ./loadgen

FROM python:3.12-slim
RUN useradd --uid 10001 --no-create-home shop
WORKDIR /srv
COPY --from=build /srv /srv
# v1 = healthy (0); build with --build-arg FAIL_RATE_DEFAULT=0.3 for the v2-bug image
ARG FAIL_RATE_DEFAULT=0
ENV PATH="/srv/.venv/bin:$PATH" PYTHONUNBUFFERED=1 FAIL_RATE=$FAIL_RATE_DEFAULT
USER 10001
EXPOSE 8000
CMD ["uvicorn", "shop.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
