FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies using UV
RUN uv sync --frozen

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/screenshots

# Run database migrations and start the bot
CMD ["sh", "-c", "uv run alembic upgrade head && uv run python main.py"]
