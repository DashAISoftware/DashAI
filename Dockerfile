# Stage 1: build frontend static assets
FROM node:22-alpine AS frontend
WORKDIR /app/DashAI/front
COPY DashAI/front/ ./
RUN corepack enable && yarn install --frozen-lockfile && yarn build

# Stage 2: Python backend serving the built frontend
FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/
WORKDIR /app
COPY . .
COPY --from=frontend /app/DashAI/front/build DashAI/front/build
RUN uv sync --locked --extra cpu --no-dev --no-cache
ENV PATH="/app/.venv/bin:$PATH"
ENV DASHAI_HOST=0.0.0.0
EXPOSE 8000
CMD ["python", "-m", "DashAI", "--no-browser"]
