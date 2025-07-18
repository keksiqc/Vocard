# ╔═════════════════════════════════════════════════════╗
# ║                       SETUP                         ║
# ╚═════════════════════════════════════════════════════╝
  # GLOBAL
  ARG APP_UID=1000 \
      APP_GID=1000

# ╔═════════════════════════════════════════════════════╗
# ║                       BUILD                         ║
# ╚═════════════════════════════════════════════════════╝
  # VOCARD
  FROM ghcr.io/astral-sh/uv:python3.12-alpine AS builder

  ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
  ENV UV_PYTHON_DOWNLOADS=0

  RUN set -ex; \
      apk --update --no-cache add \
      gcc \
      python3-dev \
      musl-dev \
      linux-headers;

  WORKDIR /app

  RUN --mount=type=cache,target=/root/.cache/uv \
      --mount=type=bind,source=uv.lock,target=uv.lock \
      --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
      uv sync --locked --no-install-project --no-dev

  COPY . /app

  RUN --mount=type=cache,target=/root/.cache/uv \
      uv sync --locked --no-dev


# ╔═════════════════════════════════════════════════════╗
# ║                       IMAGE                         ║
# ╚═════════════════════════════════════════════════════╝
  # HEADER
  FROM python:3.12-alpine

  ARG APP_UID \
      APP_GID

  WORKDIR /app

  COPY --from=builder --chown=${APP_UID}:${APP_GID} /app /app

  ENV PATH="/app/.venv/bin:$PATH"

  USER ${APP_UID}:${APP_GID}
  CMD ["python3", "-u", "main.py"]
