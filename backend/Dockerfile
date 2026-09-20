FROM python:3.11-slim

# 1. Set working directory
WORKDIR /app

# 2. Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    pkg-config \
    libcairo2-dev \
    libpangocairo-1.0-0 \
    libglib2.0-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff-dev \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# 3. Copy dependency file first (for caching)
COPY requirements.txt .

# 4. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy application code
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY alembic.dev.ini .
COPY alembic.prod.ini .
COPY entrypoint.sh .

# 6. Make entrypoint executable
RUN chmod +x entrypoint.sh

# 7. Expose port
EXPOSE 8000

# 8. Use entrypoint script
ENTRYPOINT ["./entrypoint.sh"]

# 9. Run the app in production mode (no reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
