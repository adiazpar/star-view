# Configuration Files

This directory contains all configuration files for development, testing, and deployment.

## Files Overview

- **`Dockerfile`** - Docker container configuration
- **`docker-compose.yml`** - Docker services orchestration  
- **`docker_settings.py`** - Django settings for Docker

## Root Directory Files (Required Locations)
- **`.pre-commit-config.yaml`** - Pre-commit hooks (must be in root for git)
- **`pytest.ini`** - Test configuration (must be in root for pytest)
- **`conftest.py`** - Pytest fixtures and test utilities (must be in root)

## Usage

### Pre-commit Hooks
```bash
# Install pre-commit (run once)
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

### Testing
```bash
# Run tests (pytest will automatically find config/pytest.ini)
pytest

# Run with coverage
pytest --cov=stars_app
```

### Docker
```bash
# Build and run (from root directory)
docker-compose -f config/docker-compose.yml up --build
```