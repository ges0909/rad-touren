# Stage 1: Build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend + serve frontend
FROM python:3.12-slim
WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy backend project
COPY backend/ ./

# Install dependencies via uv
RUN uv sync --no-dev

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Copy steering files and MCP servers (needed at runtime)
COPY ../.kiro/steering /app/steering
COPY ../mcp /app/mcp

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
