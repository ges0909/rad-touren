# Stage 1: Build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY app/frontend/package.json app/frontend/package-lock.json* ./
RUN npm install
COPY app/frontend/ ./
RUN npm run build

# Stage 2: Backend + serve frontend
FROM python:3.12-slim
WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy shared lib (workspace dependency)
COPY lib/ /workspace/lib/
COPY pyproject.toml /workspace/pyproject.toml

# Copy backend project
COPY app/backend/ ./
RUN sed -i 's|workspace = true|path = "/workspace/lib"|' pyproject.toml

# Install dependencies
RUN uv sync --no-dev

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Copy steering files (needed at runtime for system prompt)
COPY .kiro/steering /workspace/.kiro/steering

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
