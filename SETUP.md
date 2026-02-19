# Quick Setup Guide

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] PostgreSQL installed and running
- [ ] Redis installed and running
- [ ] Google Gemini API key

## Installation Steps

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create and configure database:**
   ```bash
   createdb incident_management
   ```

3. **Create `.env` file:**
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   DB_NAME=incident_management
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=localhost
   DB_PORT=5432
   REDIS_URL=redis://localhost:6379/0
   GEMINI_API_KEY=your-gemini-api-key
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start Redis:**
   ```bash
   redis-server
   ```

7. **Start Celery worker (in new terminal):**
   ```bash
   celery -A incident_management worker -l info
   ```

8. **Start development server:**
   ```bash
   python manage.py runserver
   ```

## Testing

1. Visit http://localhost:8000
2. Sign up for a new account (creates a new company)
3. Create an incident with log files
4. Check that AI analysis runs (via Celery)

## Common Issues

**Database connection error:** Ensure PostgreSQL is running and credentials in `.env` are correct.

**Redis connection error:** Start Redis with `redis-server` or `brew services start redis` (macOS).

**Celery not processing:** Ensure Redis is running and Celery worker is started.

**Gemini API errors:** Verify API key is set correctly in `.env`.

