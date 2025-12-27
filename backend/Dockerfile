# mcr.microsoft.com/playwright/python:v1.41.0-jammy provides Python 3.11 + Playwright browsers
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Expose port (Render sets PORT env)
ENV PORT=8000

# Run with Shell to expand PORT variable
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"
