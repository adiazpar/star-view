# PostgreSQL Migration Support

## Overview
Added configurable PostgreSQL support while maintaining SQLite compatibility. This change prepares the application for production deployment and provides better performance, concurrency, and data integrity.

## Why This Change Was Made

### Problems with SQLite in Production
- **Concurrency Limitations**: SQLite locks the entire database for writes, causing bottlenecks
- **No Network Access**: Can't connect from multiple servers or containers
- **Limited Data Types**: Fewer built-in data types compared to PostgreSQL
- **Scaling Issues**: Not suitable for high-traffic applications
- **Backup Complexity**: File-based backups are less reliable than database dumps

### Benefits of PostgreSQL
- **ACID Compliance**: Full transaction support with better data integrity
- **Concurrent Access**: Multiple users can read/write simultaneously
- **Advanced Features**: JSON fields, full-text search, GIS extensions
- **Production Ready**: Industry standard for web applications
- **Better Performance**: Optimized for complex queries and large datasets

## What Was Implemented

### 1. Database Configuration Changes

#### Environment Variables Added to `.env`
```bash
# Database Configuration
USE_POSTGRESQL=false          # Toggle between SQLite and PostgreSQL
DB_NAME=event_horizon_dev     # PostgreSQL database name
DB_USER=postgres              # PostgreSQL username
DB_PASSWORD=                  # PostgreSQL password
DB_HOST=localhost             # PostgreSQL host
DB_PORT=5432                  # PostgreSQL port
```

#### Settings Configuration (`django_project/settings/development.py`)
```python
# Development database - can be PostgreSQL or SQLite
if os.getenv('USE_POSTGRESQL', 'false').lower() == 'true':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'event_horizon_dev'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'TEST': {
                'NAME': 'test_' + os.getenv('DB_NAME', 'event_horizon_dev'),
            },
        }
    }
else:
    # Default to SQLite for development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'TEST': {
                'NAME': ':memory:'
            },
        }
    }
```

### 2. Production Configuration (`django_project/settings/production.py`)
```python
# Production database - PostgreSQL only
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'sslmode': 'require',  # SSL required for production
        },
    }
}
```

### 3. Dependencies Added (`requirements.txt`)
```
# Database
psycopg2-binary==2.9.9
```

## How to Use

### Option 1: Continue Using SQLite (Default)
```bash
# Install requirements (includes PostgreSQL driver)
source djvenv/bin/activate
pip install -r requirements.txt

# Keep using SQLite - no other changes needed
python manage.py runserver
```

### Option 2: Switch to PostgreSQL

#### Step 1: Install PostgreSQL
```bash
# On macOS with Homebrew
brew install postgresql
brew services start postgresql

# On Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# On Windows
# Download from https://www.postgresql.org/download/windows/
```

#### Step 2: Create Database
```bash
# Create database
createdb event_horizon_dev

# Or connect to PostgreSQL and create manually
psql -U postgres
CREATE DATABASE event_horizon_dev;
\q
```

#### Step 3: Configure Environment
```bash
# Edit .env file
USE_POSTGRESQL=true
DB_NAME=event_horizon_dev
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432
```

#### Step 4: Migrate Data
```bash
# Create migrations for model changes
python manage.py makemigrations

# Apply migrations to PostgreSQL
python manage.py migrate

# Optional: Transfer existing SQLite data
python manage.py dumpdata stars_app > sqlite_backup.json
python manage.py loaddata sqlite_backup.json
```

## Impact on Codebase

### Immediate Benefits
- **Zero Breaking Changes**: Existing SQLite setup continues to work
- **Environment Flexibility**: Easy switching between development and production databases
- **Docker Compatibility**: PostgreSQL works better in containerized environments
- **Team Development**: Multiple developers can use different database setups

### Future Benefits
- **Production Readiness**: Can deploy with PostgreSQL without code changes
- **Performance Improvements**: Better query optimization and concurrent access
- **Advanced Features**: Access to PostgreSQL-specific features when needed
- **Scalability**: Can handle much larger datasets and user loads

## Testing Strategy

### Local Development Testing
```bash
# Test with SQLite (current setup)
USE_POSTGRESQL=false python manage.py test

# Test with PostgreSQL (if installed)
USE_POSTGRESQL=true python manage.py test

# Test migrations work on both databases
python manage.py migrate --dry-run
```

### CI/CD Considerations
- Tests should run against both SQLite and PostgreSQL
- Migration files should be compatible with both databases
- Environment-specific settings should be tested

## Rollback Procedure

If PostgreSQL causes issues:

1. **Immediate Rollback**:
   ```bash
   # Change .env file
   USE_POSTGRESQL=false
   
   # Restart server
   python manage.py runserver
   ```

2. **Data Recovery**:
   - Your original `db.sqlite3` file is preserved
   - No data loss during testing phase
   - Can switch back and forth safely

## Common Issues and Solutions

### Issue: `psycopg2` Installation Fails
```bash
# Solution: Install build dependencies
# On macOS:
brew install postgresql

# On Ubuntu:
sudo apt-get install libpq-dev python3-dev

# Then reinstall
pip install psycopg2-binary
```

### Issue: PostgreSQL Connection Refused
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql
# or
sudo systemctl status postgresql

# Start if not running
brew services start postgresql
# or
sudo systemctl start postgresql
```

### Issue: Database Does Not Exist
```bash
# Create the database
createdb event_horizon_dev

# Or using SQL
psql -U postgres -c "CREATE DATABASE event_horizon_dev;"
```

## Best Practices

### Development
- Use SQLite for quick local development
- Use PostgreSQL for integration testing
- Keep both configurations tested and working

### Production
- Always use PostgreSQL in production
- Use connection pooling (CONN_MAX_AGE)
- Enable SSL connections
- Regular database backups

### Team Workflow
- Document which database team members are using
- Ensure migrations work on both databases
- Test performance with realistic data volumes

## Next Steps

1. **Immediate**: Install requirements and test current setup
2. **Optional**: Set up PostgreSQL locally for testing
3. **Future**: Configure PostgreSQL for staging/production environments
4. **Advanced**: Consider PostgreSQL-specific features (JSON fields, full-text search)

This migration strategy provides maximum flexibility while maintaining stability and preparing for future growth.