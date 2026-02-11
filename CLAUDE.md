# Fathaker (فذكر) - Project Documentation for Claude

## Project Overview

**Fathaker** is an Islamic web platform dedicated to Quranic studies and resources. The name "فذكر" means "Remember" in Arabic, derived from Quranic verses. The platform provides:

- Live Quranic radio stations from around the world
- Complete Quran database with detailed metadata (114 Surahs, 6,236 verses)
- Quran search with multiple modes (text search, starts-with, ends-with, by surah, page, range)
- Radio detail pages with likes and view tracking
- RESTful API with OpenAPI/Swagger documentation
- User-friendly Arabic (RTL) interface
- Tag-based filtering and search capabilities

## Technology Stack

### Backend
- **Django 5.0.4** - Main web framework
- **Django REST Framework 3.15.1** - API development
- **drf-spectacular 0.28.0** - OpenAPI schema & Swagger/ReDoc documentation
- **Python 3.10** - Runtime environment
- **SQLite 3** - Database
- **django-taggit 5.0.1** - Tag management
- **Pillow 10.3.0** - Image processing
- **python-dotenv 1.0.1** - Environment variable management

### Frontend
- **Bootstrap 5 RTL** - Responsive UI framework
- **Font Awesome 5.15.4** - Icons
- **Swiper.js** - Carousels/sliders
- **Vanilla JavaScript** - Client-side interactivity

### DevOps
- **Docker + Docker Compose** - Containerization
- **Gunicorn** - WSGI server
- **Nginx** - Reverse proxy
- **GitHub Actions** - CI/CD

## Project Structure

```
Fathaker/
├── fathaker/              # Django project configuration
│   ├── settings.py        # Main settings
│   ├── urls.py            # Root URL configuration
│   ├── wsgi.py/asgi.py    # Server entry points
│
├── core/                  # Core functionality
│   ├── models.py          # NavLink model (navigation)
│   ├── views.py           # Homepage redirect
│   ├── context_processors.py  # Global template context (navbar, footer, social links)
│
├── radio/                 # Radio stations module
│   ├── models.py          # Radio model with tags, ranking, likes, views, slugs
│   ├── views.py           # RadiosList, RadioDetail, RadioLike, RadioRankUp/Down
│   ├── admin.py           # Enhanced admin with image preview, audio player, rank controls
│   ├── urls.py            # UnicodeSlugConverter registered as 'uslug'
│   ├── templates/         # Radio list & detail pages
│
├── verses/                # Quranic verses module
│   ├── models.py          # Surah, Verse, and Audio models
│   ├── views.py           # QuranSearch template view
│   ├── api_views.py       # Multiple API endpoints (list, search, surah, detail, range, etc.)
│   ├── serializers.py     # DRF serializers
│   ├── admin.py           # Admin with filters and audio preview
│
├── static/                # Static assets (CSS, JS, images)
├── media/                 # User uploads (radio images)
├── templates/             # Base and app templates
├── deployment/            # Docker & Nginx configs
```

## Key Components

### Radio Module
- **Model**: `Radio` with fields: name, stream_url, description, image, rank, tags, slug, likes_count, views_count
- **Slug**: Unicode slugs (`allow_unicode=True`) auto-generated from name, with collision handling via counter suffix
- **Ordering**: By `rank` field (manually managed via admin)
- **Admin Features**: Image preview, audio player, ranking controls, tag management, likes/views (readonly), slug prepopulated
- **Views**:
  - `RadiosList` - Template view for browsing radios
  - `RadioDetail` - Detail page, auto-increments views_count via `F()` expression
  - `RadioLike` - POST API to increment likes_count (AllowAny)
  - `RadioRankUp/Down` - Admin-only APIs for ranking
- **Frontend**: Real-time search/filter by name or tags, player with fullscreen modal
- **Like Tracking**: Per-browser via localStorage key `fathaker_liked_radios` (no auth required)

### Verses Module
- **Models**:
  - `Surah` - 114 Quranic chapters (name with/without tashkeel)
  - `Audio` - Audio recitation files (name, url)
  - `Verse` - Individual verses with metadata
- **Verse Fields**: verse_pk (unique, format S{surah}V{verse}), verse (with diacritics), verse_without_tashkeel, surah (FK), number_in_surah, number_in_quran, juz, page, the_quarter, is_sajda, audio (M2M to Audio)
- **API Endpoints** (all under `/verses/api/`):
  - `verses_list` - All verses with optional `?page=X` filter
  - `search/?q=keyword` - Text search (with/without tashkeel)
  - `surah/<surah_id>/` - All verses for a surah
  - `verse/<surah_id>/<verse_number>/` - Single verse detail
  - `range/<start>/<end>/` - Verses by number_in_quran range
  - `starts-with/?q=text` - Verses starting with text
  - `ends-with/?q=text` - Verses ending with text
- **Quran Search Page**: `/verses/search/` - Client-side search UI with 6 modes (search, starts-with, ends-with, surah, page, range)
- **Admin**: Searchable by text, filterable by surah/juz/quarter/page/sajda, audio preview

### Core Module
- **NavLink Model**: Database-driven navigation (navbar, footer, social links)
- **Link Types**: `"0"` (navbar), `"1"` (footer links), `"2"` (footer social)
- **Context Processor**: `get_nav_links()` injects navbar_links, footer_links, footer_social into all templates
- **Homepage**: Redirects to radio list

## Development Guidelines

### Code Conventions

1. **File Paths**: Use absolute paths for all file operations
   ```python
   # Good
   /home/marwanmohamed/Documents/work/Fathaker/radio/models.py

   # Bad
   ./radio/models.py
   ```

2. **Models**:
   - Always include `__str__` method
   - Use `help_text` for clarity
   - Add `verbose_name` and `verbose_name_plural` for admin
   - Use `ordering` Meta attribute where needed

3. **Views**:
   - Use class-based views (CBV) for CRUD operations
   - Add permission classes for admin-only endpoints
   - Use Django messages framework for user feedback

4. **Admin**:
   - Customize `list_display`, `list_filter`, `search_fields`
   - Add `readonly_fields` for calculated/display-only fields
   - Use `@admin.register()` decorator for registration

5. **Frontend**:
   - All JavaScript in separate files (not inline, except template data injection)
   - Use Bootstrap classes for styling
   - Support RTL layout (Arabic interface)
   - Avoid jQuery - use vanilla JavaScript
   - JS data passed via inline script in template (e.g., radios array)
   - URL templates use `__SLUG__` placeholder, replaced in JS with actual slug

6. **API Design**:
   - Use DRF for all APIs
   - Implement proper serializers
   - Add pagination for list endpoints
   - Use descriptive endpoint names
   - Use drf-spectacular `@extend_schema` for API documentation

### Important Patterns

#### Unicode Slug Pattern
```python
# radio/urls.py registers UnicodeSlugConverter as 'uslug'
path('<uslug:slug>/', RadioDetail.as_view(), name='radio_detail')
```

#### Atomic Counter Increment
```python
# Use F() expressions for thread-safe counter updates
radio.views_count = F('views_count') + 1
radio.save(update_fields=['views_count'])
```

#### Migration Pattern for Non-Null Unique Fields
3-step approach for existing data:
1. Add field as nullable (0008)
2. Data migration to populate values (0009)
3. Make field non-null and unique (0010)

## Environment Configuration

Required `.env` variables:
```env
SECRETKEY=<django-secret-key>
DEBUG=1  # 0 for production, 1 for development
ALLOWEDHOSTS=localhost,127.0.0.1
DEBLOYED=0  # 0 for development, 1 for production
TRUSTEDORIGINS=https://yourdomain.com  # Production only
```

For local development without `.env` file:
```bash
DEBUG=1 SECRETKEY=test ALLOWEDHOSTS=localhost DEBLOYED=0 python manage.py runserver
```

## Common Tasks

### Running Development Server
```bash
python manage.py runserver
```

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Creating Superuser
```bash
python manage.py createsuperuser
```

### Running Tests
```bash
python manage.py test
```

### Collecting Static Files
```bash
python manage.py collectstatic
```

### Docker Deployment
```bash
docker-compose up -d
```

## URL Patterns

### Pages
- `/` → Redirects to radio list
- `/admin/` → Django admin interface
- `/radio/` → Radio stations listing
- `/radio/<slug>/` → Radio detail page (unicode slug)
- `/verses/search/` → Quran search page

### Radio APIs
- `/radio/rank/up/<id>/` → Rank up (admin only)
- `/radio/rank/down/<id>/` → Rank down (admin only)
- `/radio/api/<slug>/like/` → Like a radio (POST, public)

### Verses APIs
- `/verses/api/verses_list` → All verses, optional `?page=X`
- `/verses/api/search/?q=keyword` → Text search
- `/verses/api/surah/<surah_id>/` → Verses by surah
- `/verses/api/verse/<surah_id>/<verse_number>/` → Single verse
- `/verses/api/range/<start>/<end>/` → Verses by number_in_quran range
- `/verses/api/starts-with/?q=text` → Verses starting with text
- `/verses/api/ends-with/?q=text` → Verses ending with text

### API Documentation
- `/api/schema/` → OpenAPI schema (drf-spectacular)
- `/api/docs/` → Swagger UI
- `/api/redoc/` → ReDoc

## Database Schema Notes

### Radio Table
- `rank` field controls display order (lower = higher priority, unique)
- `slug` field: unicode slug auto-generated from name, unique, with collision counter suffix
- `likes_count` and `views_count` for engagement tracking
- Tags are managed via django-taggit (many-to-many)
- Image uploads go to `media/radio/`

### Verse Table
- Complete Quran data (6,236 verses)
- `verse_pk`: unique key in format `S{surah_id}V{verse_number}`
- Two text versions: with and without diacritics (Tashkeel)
- Rich metadata: juz, page, quarter, sajda flag
- Foreign key to Surah model
- Many-to-many relationship with Audio model

### Audio Table
- Audio recitation files with name and URL
- Linked to verses via M2M relationship

### NavLink Table
- Flexible navigation system
- Supports internal Django URLs and external links
- Font Awesome icon integration
- Link types: "0" (navbar), "1" (footer), "2" (social)

## Static Files Organization

```
static/
├── base/
│   ├── css/
│   │   ├── bootstrap.rtl.min.css  # Bootstrap RTL version
│   │   ├── header.css             # Navbar styling
│   │   ├── footer.css             # Footer styling
│   │   └── swiper-bundle.min.css  # Swiper library styles
│   └── js/
│       ├── bootstrap.bundle.min.js
│       └── swiper-bundle.min.js
│
├── radio/
│   ├── css/
│   │   ├── radios.css             # Radio card styling
│   │   └── radio_detail.css       # Radio detail page styling
│   └── js/
│       ├── radios.js              # Search/filter/player logic
│       └── radio_detail.js        # Detail page interactivity
│
└── verses/
    ├── css/
    │   └── quran_search.css       # Quran search page styling (RTL)
    └── js/
        └── quran_search.js        # Search interface with 6 modes
```

## Templates

```
templates/
├── base/
│   └── base.html              # Main base template (navbar, footer, blocks)
├── radio/
│   ├── radios_list.html       # Radio stations listing page
│   └── radio_detail.html      # Individual radio detail page
├── verses/
│   └── quran_search.html      # Quran search interface
└── core/
    └── home_page.html         # Homepage template
```

## Security Considerations

1. **Admin-Only Endpoints**: Radio ranking APIs require `IsAdminUser` permission
2. **CSRF Protection**: Django middleware enabled; CSRF token passed as template variable for API calls
3. **Environment Variables**: Sensitive keys in `.env` (never commit)
4. **Media Uploads**: Validated through Django's `ImageField`
5. **Input Sanitization**: Always use Django's built-in form validation
6. **HTML Escaping**: Frontend JavaScript escapes HTML in search results

## Testing

21 test cases across 3 test files:
- **Radio Tests** (14 tests): Model methods, list view, rank up/down with auth checks
- **Verses Tests** (4 tests): Model methods, API list and page filter
- **Core Tests** (3 tests): NavLink model, internal/external link resolution

Run tests: `python manage.py test`

## Deployment Checklist

- [ ] Set `DEBUG=0` in `.env`
- [ ] Configure `ALLOWEDHOSTS` with production domain
- [ ] Set `DEBLOYED=1` in `.env`
- [ ] Add `TRUSTEDORIGINS` for CSRF
- [ ] Run `collectstatic`
- [ ] Run migrations on production DB
- [ ] Set strong `SECRETKEY`
- [ ] Configure Nginx for static/media files
- [ ] Set up SSL certificate

## Git Workflow

- Main branch: `main`
- Create feature branches for new work
- Use descriptive commit messages
- Reference issue numbers when applicable (e.g., "close #10")
- Test thoroughly before merging PRs

## Contact & Resources

- Repository: GitHub (current repo)
- CI/CD: GitHub Actions (automatic tests on push/PR)
- Python Version: 3.10
- Django Version: 5.0.4
- API Documentation: `/api/docs/` (Swagger UI) or `/api/redoc/` (ReDoc)

---

**Last Updated**: 2026-02-11
**Project Status**: Active Development
