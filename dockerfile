# Use official Python image
FROM python:3.11-slim

# Prevents Python from writing pyc files and buffers logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside the container
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files
COPY . /app/

# Expose port 8000 for local Docker runs. Render provides PORT at runtime.
EXPOSE 8000

# Run migrations, collect static files, then start Gunicorn.
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn rent.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]
