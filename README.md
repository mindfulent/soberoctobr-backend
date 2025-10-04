# Sober October Backend API

FastAPI backend for the Sober October habit tracking application.

## Features

- **Google OAuth 2.0 Authentication** with JWT tokens
- **RESTful API** with automatic OpenAPI documentation
- **PostgreSQL Database** with SQLAlchemy ORM
- **Database Migrations** with Alembic
- **Type Safety** with Pydantic schemas
- **CORS Support** for frontend integration

## Tech Stack

- **Python 3.11+**
- **FastAPI** - Modern web framework
- **SQLAlchemy 2.0** - Database ORM
- **PostgreSQL** - Database
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **Google OAuth 2.0** - Authentication

## Project Structure

```
soberoctobr-backend/
├── alembic/              # Database migrations
│   ├── versions/         # Migration files
│   └── env.py           # Alembic configuration
├── app/
│   ├── api/             # API route handlers
│   │   ├── auth.py      # Authentication endpoints
│   │   ├── users.py     # User management
│   │   ├── challenges.py # Challenge CRUD
│   │   ├── habits.py    # Habit management
│   │   └── entries.py   # Daily tracking
│   ├── core/            # Core utilities
│   │   ├── database.py  # Database connection
│   │   ├── security.py  # JWT handling
│   │   └── oauth.py     # Google OAuth
│   ├── models/          # SQLAlchemy models
│   │   ├── user.py
│   │   ├── challenge.py
│   │   ├── habit.py
│   │   └── daily_entry.py
│   ├── schemas/         # Pydantic schemas
│   │   ├── user.py
│   │   ├── challenge.py
│   │   ├── habit.py
│   │   ├── daily_entry.py
│   │   └── auth.py
│   ├── config.py        # Settings
│   └── main.py          # FastAPI app
├── tests/               # Test files
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variables template
```

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your configuration
# - DATABASE_URL: PostgreSQL connection string
# - SECRET_KEY: Generate a secure random key
# - GOOGLE_CLIENT_ID: From Google Cloud Console
# - GOOGLE_CLIENT_SECRET: From Google Cloud Console
```

### 3. Set Up Database

```bash
# Create database (PostgreSQL must be running)
createdb soberoctobr_db

# Run migrations
alembic upgrade head
```

### 4. Run Development Server

```bash
# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API will be available at:
# - http://localhost:8000
# - Docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/google` - Google OAuth login
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/logout` - Logout

### Users
- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/profile` - Update user profile

### Challenges
- `GET /api/v1/challenges` - List all challenges
- `POST /api/v1/challenges` - Create new challenge
- `GET /api/v1/challenges/{id}` - Get challenge details
- `PUT /api/v1/challenges/{id}` - Update challenge
- `DELETE /api/v1/challenges/{id}` - Delete challenge

### Habits
- `GET /api/v1/challenges/{id}/habits` - List challenge habits
- `POST /api/v1/challenges/{id}/habits` - Create habit
- `GET /api/v1/habits/{id}` - Get habit details
- `PUT /api/v1/habits/{id}` - Update habit
- `DELETE /api/v1/habits/{id}` - Archive habit

### Daily Entries
- `GET /api/v1/habits/{id}/entries` - Get habit entries
- `POST /api/v1/habits/{id}/entries` - Create/update entry
- `GET /api/v1/challenges/{id}/entries/{date}` - Get entries for date
- `PUT /api/v1/entries/{id}` - Update entry
- `DELETE /api/v1/entries/{id}` - Delete entry

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:5173/auth/callback`
5. Copy Client ID and Client Secret to `.env`

## Development

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Lint
flake8 .
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## Deployment

See `docs/technical-requirements.md` for DigitalOcean deployment configuration.

### Environment Variables for Production

- Set `ENVIRONMENT=production`
- Set `DEBUG=False`
- Use strong `SECRET_KEY`
- Configure production database URL
- Add production frontend URL to `CORS_ORIGINS`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## License

Proprietary - Sober October Habit Tracker
