# Use Python 3.12-slim as base
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create uploads folder and instance folder for SQLite
RUN mkdir -p uploads instance

# Expose port 5000
EXPOSE 5000

# Start application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
