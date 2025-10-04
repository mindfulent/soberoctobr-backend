# Sober October Backend

Backend API for the Sober October habit tracking application.

## Overview

This FastAPI-based backend provides the core functionality for tracking sobriety habits, managing user data, and providing analytics for the Sober October application.

## Features

- User authentication and authorization
- Habit tracking and management
- Progress analytics and reporting
- RESTful API endpoints
- Database integration with PostgreSQL
- Automated database migrations with Alembic

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Authentication**: JWT tokens
- **Testing**: pytest
- **Code Quality**: Black, Flake8, isort

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 13+
- pip or pipenv

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd soberoctobr-backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and other settings
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, you can access:
- Interactive API docs: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

## Development

### Code Style

This project uses:
- **Black** for code formatting
- **Flake8** for linting
- **isort** for import sorting

Run formatting and linting:
```bash
black .
flake8 .
isort .
```

### Testing

Run tests:
```bash
pytest
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

## Project Structure

```
soberoctobr-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection and session
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # API route handlers
│   ├── core/                # Core functionality (auth, security)
│   └── utils/               # Utility functions
├── alembic/                 # Database migrations
├── tests/                   # Test files
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
