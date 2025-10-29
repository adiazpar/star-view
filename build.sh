#!/usr/bin/env bash
# ----------------------------------------------------------------------------------------------------- #
# This build.sh script runs on Render during deployment to set up the Django + React application.       #
#                                                                                                       #
# Purpose:                                                                                              #
# Automates deployment tasks that would normally require shell access: installing dependencies,         #
# building the React frontend, collecting static files, running migrations, and creating an initial     #
# superuser. This is essential for Render's free tier which doesn't provide interactive shell access.   #
#                                                                                                       #
# What it does:                                                                                         #
# 1. Installs Python dependencies from requirements.txt                                                 #
# 2. Installs Node.js dependencies and builds React production bundle                                   #
# 3. Collects static files (CSS, JS, images, React build) for production serving                        #
# 4. Runs database migrations to update schema                                                          #
# 5. Creates superuser if DJANGO_SUPERUSER_* environment variables are set                              #
#                                                                                                       #
# Usage:                                                                                                #
# - Render automatically runs this script during deployment                                             #
# - Set these environment variables in Render dashboard:                                                #
#   DJANGO_SUPERUSER_USERNAME=admin                                                                     #
#   DJANGO_SUPERUSER_EMAIL=admin@example.com                                                            #
#   DJANGO_SUPERUSER_PASSWORD=your-secure-password                                                      #
#   VITE_MAPBOX_TOKEN=your-mapbox-token                                                                 #
#                                                                                                       #
# Security Note:                                                                                        #
# The superuser creation only runs if credentials don't already exist in the database.                  #
# Django's createsuperuser command is idempotent - safe to run multiple times.                          #
# ----------------------------------------------------------------------------------------------------- #

# Exit on error
set -o errexit

echo "===================================="
echo "Starting Render build script..."
echo "===================================="

# Install Python dependencies
echo "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt

# Install Node.js dependencies and build React frontend
echo "Installing Node.js dependencies..."
cd frontend
npm ci  # Use 'npm ci' for faster, more reliable installs in CI/CD

echo "Building React production bundle..."
npm run build

echo "React build completed. Output in frontend/dist/"
cd ..

# Collect static files (CSS, JS, images, React build)
echo "Collecting static files..."
python3 manage.py collectstatic --no-input

# Run database migrations
echo "Running database migrations..."
python3 manage.py makemigrations
python3 manage.py migrate --no-input

# Create superuser if environment variables are set
# This uses Django's built-in command that reads from environment variables:
# - DJANGO_SUPERUSER_USERNAME
# - DJANGO_SUPERUSER_EMAIL
# - DJANGO_SUPERUSER_PASSWORD
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Checking if superuser needs to be created..."

    # Check if superuser already exists using Django shell
    USER_EXISTS=$(python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists())")

    if [ "$USER_EXISTS" = "False" ]; then
        echo "Creating superuser: $DJANGO_SUPERUSER_USERNAME"
        python manage.py createsuperuser --no-input --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL"
        echo "Superuser created successfully!"
    else
        echo "Superuser '$DJANGO_SUPERUSER_USERNAME' already exists, skipping creation"
    fi
else
    echo "Skipping superuser creation (environment variables not set)"
    echo "Set DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, and DJANGO_SUPERUSER_PASSWORD in Render dashboard"
fi

echo "===================================="
echo "Build script completed successfully!"
echo "===================================="
