# Starview

**Live Demo:** [https://starview.app](https://starview.app)

---

## The night sky is incredible—if you know where to look.

Starview solves the #1 problem for stargazers: **finding quality dark sky locations**. Whether you're chasing meteor showers, photographing the Milky Way, or observing planets through a telescope, our community-driven platform helps you discover reviewed, photo-verified locations perfect for your next celestial adventure.

### The Problem

Stargazers face a common challenge: generic map applications don't provide the specific information needed to find exceptional viewing locations. Where is the nearest dark sky site? Which locations have minimal light pollution? Is it accessible? Worth the drive? These questions go unanswered by traditional mapping tools.

### The Solution

Starview is a specialized, community-driven platform built specifically for the stargazing community. Users can:

- **Discover locations** with detailed reviews from fellow stargazers
- **Read authentic experiences** from people who've actually visited
- **Browse photos** to see what each location offers
- **Save favorites** to build a personal stargazing trip list
- **Contribute knowledge** by sharing your own favorite spots

---

## Key Features

### Current Functionality

**Location Discovery**
- Browse community-submitted stargazing locations worldwide
- Search and filter by country, region, and rating
- View enriched location data (address, elevation, coordinates)
- Optimized map markers for exploring nearby spots

**Community Reviews**
- Detailed reviews with 1-5 star ratings
- Photo uploads (up to 5 images per review with automatic thumbnails)
- Upvote/downvote system to surface the best content
- Comment threads for community discussion

**User Profiles**
- Personal favorites collection for trip planning
- Review history and contribution tracking
- Profile customization with avatar uploads

**Content Moderation**
- Community reporting system for inappropriate content
- Vote-based content quality signals
- Spam prevention and rate limiting

### Future Vision

**Celestial Events Integration**
- Meteor shower calendars with location recommendations
- New moon periods for optimal Milky Way viewing
- Planetary alignment notifications
- Eclipse path tracking
- Community event coordination (star parties, group observations)

**Enhanced Discovery**
- Light pollution ratings (Bortle scale integration)
- Equipment-friendly filters (telescope accessible, power availability)
- Weather forecasts and sky condition predictions
- Advanced search (horizon visibility, altitude, accessibility)

**Mobile Experience**
- Native mobile applications
- Clear sky night notifications
- Offline location access
- Real-time sky condition updates

---

## Tech Stack

### Backend (Production-Ready)

**Framework & Core**
- **Django 5.1.13** - Web framework
- **Django REST Framework 3.15.2** - RESTful API
- **PostgreSQL 17.6** - Production database
- **Redis 7.0.0** - Caching and message broker
- **Celery 5.4.0** - Asynchronous task processing

**Security & Performance**
- **django-axes 8.0.0** - Account lockout protection (defends against brute force)
- **django-csp 4.0** - Content Security Policy headers
- **bleach 6.2.0** - HTML sanitization (XSS prevention)
- **Comprehensive rate limiting** - 5 throttle classes (login, content creation, voting, reporting)
- **99.3% query optimization** - N+1 elimination with strategic prefetching
- **Redis caching** - 10-60x faster response times

**Production Infrastructure**
- **Gunicorn 23.0.0** - WSGI server
- **Whitenoise 6.9.0** - Static file serving with compression
- **AWS SES** - Transactional email (custom domain: noreply@starview.app)
- **Render.com** - Hosting platform with automated deployments

**External Services**
- **Mapbox API** - Geocoding and elevation data for location enrichment
- **Custom tile server** - Map rendering (self-hosted)

### Architecture Highlights

**Service Layer Pattern**
- Separation of business logic from views and models
- LocationService, VoteService, ReportService, PasswordService
- Graceful degradation with external API failures

**Signal Handlers**
- Automatic file cleanup on model deletion
- Cascading deletions with orphaned file prevention
- Safe path validation (prevents directory traversal)

**Async Task Processing**
- Celery integration with FREE tier support (sync fallback)
- Location enrichment runs asynchronously (99.4% faster response: 2.5s → 0.015s)
- Configurable via `CELERY_ENABLED` environment variable

**Generic Relationships**
- ContentTypes framework for Vote and Report models
- DRY implementation (one Vote model for Reviews, Comments, future content)

**Custom Exception Handling**
- Consistent JSON error responses across all endpoints
- Production-safe error messages (hides internals when DEBUG=False)
- Automatic audit logging for security events

### Security Features

**Grade: A+ (98/100)**

**Implementation Highlights:**
- HTTPS enforced (HSTS enabled with 1-year max-age)
- Security headers (CSP, X-Frame-Options, X-Content-Type-Options)
- CSRF protection with trusted origins
- Account lockout (5 failed attempts = 1-hour lockout, username-based)
- XSS prevention (HTML sanitization with whitelisted tags)
- File upload validation (extension, MIME type, image verification)
- Coordinate validation (realistic latitude/longitude ranges)
- API timeouts (10-second limit on external calls)
- Rate limiting on all sensitive endpoints
- Audit logging (database + rotating file storage, JSON format)

**Test Coverage:**
- 80+ security and performance tests
- Phase 1: 44 security tests
- Phase 2: Performance optimization tests (query reduction verified)
- Phase 4: 31 infrastructure tests (account lockout, audit logging, error handling)
- Phase 5: 5 monitoring tests (health check endpoint)

### Performance Optimizations

**Query Optimization**
- 99.3% query reduction (548 → 4 queries on location list)
- Strategic use of `select_related()` and `prefetch_related()`
- Database annotations for aggregates (Count, Avg)
- Conditional serializers (list vs detail views)

**Response Optimization**
- Map markers endpoint: 97% smaller payload
- Info panel endpoint: 95% smaller payload
- Image optimization: automatic resize and thumbnail generation
- Pagination: 20 items per page

**Caching Strategy**
- Redis-backed caching (15-minute TTL)
- User-aware cache keys (authenticated vs anonymous)
- Smart invalidation on create/update/delete operations
- 10-60x performance gains on cached endpoints

**Database Indexes**
- Strategic indexes on frequently queried fields
- Compound indexes for complex queries
- Full-text search ready (PostgreSQL capabilities)

### API Architecture

**RESTful Design**
- Nested resources (locations → reviews → comments)
- Custom actions (vote, report, add_photos, map_markers)
- Pagination and filtering
- Consistent error responses

**Endpoints:**
- `/api/locations/` - CRUD operations
- `/api/locations/{id}/reviews/` - Nested reviews
- `/api/locations/{id}/reviews/{id}/comments/` - Nested comments
- `/api/favorite-locations/` - User favorites
- `/api/profile/` - User profile management
- `/health/` - Load balancer monitoring (database, cache, Celery status)

**Authentication:**
- Django session-based authentication
- Custom login/registration with audit logging
- Password reset flow with email verification
- Generic error messages (prevents user enumeration)

---

## Frontend

**Status:** In Development

**Planned Tech Stack:**
- To be determined

**Features:**
- Interactive map interface for location discovery
- Responsive design for mobile and desktop
- Photo gallery and review interfaces
- User authentication and profile management
- Real-time updates for votes and comments

---

## Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 17.6
- Redis 7.0+
- Virtual environment tool (venv)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/starview.git
   cd starview
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv djvenv
   source djvenv/bin/activate  # On Windows: djvenv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Start Redis (required for caching)**
   ```bash
   # macOS (Homebrew)
   brew services start redis

   # Linux
   sudo systemctl start redis

   # Verify connection
   redis-cli PING  # Should return PONG
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

8. **Optional: Start Celery worker (for async tasks)**
   ```bash
   celery -A django_project worker --loglevel=info
   ```

### Environment Variables

Required variables in `.env`:

```bash
# Django Core
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True  # False in production
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://localhost:8000

# Database
DB_ENGINE=postgresql
DB_NAME=starview_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Redis & Celery
REDIS_URL=redis://127.0.0.1:6379/1
CELERY_ENABLED=False  # True to enable async tasks

# External APIs
MAPBOX_TOKEN=your_mapbox_token
TILE_SERVER_URL=http://your-tile-server:3001

# Email (AWS SES)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_SES_REGION_NAME=us-east-2
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### Running Tests

```bash
# Security tests (Phase 1)
python .claude/backend/tests/phase1/test_rate_limiting.py
python .claude/backend/tests/phase1/test_file_upload.py
python .claude/backend/tests/phase1/test_xss_sanitization.py

# Performance tests (Phase 2)
python .claude/backend/tests/phase2/test_query_optimization.py
python .claude/backend/tests/phase2/test_redis_caching.py

# Infrastructure tests (Phase 4)
python .claude/backend/tests/phase4/test_account_lockout.py
python .claude/backend/tests/phase4/test_celery_tasks.py

# Health check tests (Phase 5)
python .claude/backend/tests/phase5/test_health_check.py
```

---

## Production Deployment

**Current Status:** Live at [https://starview.app](https://starview.app)

**Platform:** Render.com
- Web Service (Gunicorn)
- PostgreSQL Database (automated backups)
- Redis Cache
- Custom domain with SSL/TLS

**Security:**
- A+ grade on securityheaders.com
- All API keys rotated for production
- Environment variables secured in hosting dashboard
- DEBUG=False with production-safe error messages

**Monitoring:**
- Health check endpoint for load balancer monitoring
- Audit logging (database + rotating files)
- Django logging configured for errors and security events

---

## Project Status

**Backend:** 96% Complete (20/22 items)
- Production deployed and live
- Security audit complete (Phases 1-3: 100%)
- Infrastructure hardening (Phase 4: 83%)
- Monitoring (Phase 5: 50%)

**Remaining Backend Work:**
- Database index optimization (2 hours)
- Sentry integration for error tracking (1 hour, optional)

**Frontend:** Not started
- Architecture planning in progress
- Tech stack selection pending

---

## Documentation

**For Developers:**
- `.claude/README.md` - Documentation navigation guide
- `.claude/backend/ARCHITECTURE.md` - Complete backend architecture (631 lines)
- `.claude/backend/SECURITY_SUMMARY.md` - Security audit results (489 lines)
- `.claude/backend/PROGRESS.md` - Implementation timeline and testing
- `.claude/backend/CELERY_GUIDE.md` - Async task processing guide
- `.claude/frontend/API_GUIDE.md` - Complete API reference for frontend integration
- `.claude/documentation-style.md` - Code documentation standards

**Key Features:**
- Token-optimized for AI agents (56% reduction from original docs)
- Single source of truth (no redundancy)
- Organized by topic (backend/frontend)
- Comprehensive test coverage documentation

---

## Contributing

This is currently a solo developer project. Contributions, suggestions, and feedback are welcome!

**Areas for contribution:**
- Frontend development
- Mobile app development
- Celestial event data integration
- Light pollution data sources
- UI/UX design

---

## License

[To be determined]

---

## Contact

**Developer:** Alejandro Diaz
**Live Site:** [https://starview.app](https://starview.app)
**Project Repository:** [GitHub](https://github.com/adiazpar/starview)

---

## Acknowledgments

**Technologies:**
- Django and Django REST Framework communities
- Mapbox for geocoding and elevation APIs
- Render.com for hosting infrastructure
- Open source security tools (django-axes, django-csp, bleach)

**Inspiration:**
- The stargazing and amateur astronomy community
- Dark sky preservation efforts worldwide
- Astrophotography communities sharing knowledge and locations
