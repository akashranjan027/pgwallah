FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8070

# Development target
FROM python:3.11-slim as development
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8070
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8070", "--reload"]
