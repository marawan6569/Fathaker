# Fathaker (فذكر) - Project Documentation for Claude

## Project Overview

**Fathaker** is an Islamic web platform dedicated to Quranic studies and resources. The name "فذكر" means "Remember" in Arabic, derived from Quranic verses. The platform provides:

- Live Quranic radio stations from around the world
- Complete Quran database with detailed metadata (114 Surahs, 6,236 verses)
- RESTful API for verse data
- User-friendly Arabic (RTL) interface
- Tag-based filtering and search capabilities

## Technology Stack

### Backend
- **Django 5.0.4** - Main web framework
- **Django REST Framework 3.15.1** - API development
- **Python 3.12** - Runtime environment
- **SQLite 3** - Database
- **django-taggit 5.0.1** - Tag management
- **Pillow 10.3.0** - Image processing

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
│   ├── context_processors.py  # Global template context
│
├── radio/                 # Radio stations module
│   ├── models.py          # Radio model with tags and ranking
│   ├── views.py           # RadiosList, RadioRankUp/Down
│   ├── admin.py           # Enhanced admin interface
│   ├── templates/         # Radio list page
│
├── verses/                # Quranic verses module
│   ├── models.py          # Surah and Verse models
│   ├── api_views.py       # VersesList API endpoint
│   ├── serializers.py     # DRF serializers
│   ├── admin.py           # Admin with filters
│
├── static/                # Static assets (CSS, JS, images)
├── media/                 # User uploads (radio images)
├── templates/base/        # Base templates
├── deployment/            # Docker & Nginx configs
```

## Key Components

### Radio Module
- **Model**: `Radio` with fields: name, stream_url, description, image, rank, tags
- **Ordering**: By `rank` field (manually managed via admin)
- **Admin Features**: Image preview, audio player, ranking controls, tag management
- **Views**:
  - `RadiosList` - Template view for browsing radios
  - `RadioRankUp/Down` - Admin-only APIs for ranking
- **Frontend**: Real-time search/filter by name or tags (`static/radio/js/radios.js`)

### Verses Module
- **Models**:
  - `Surah` - 114 Quranic chapters
  - `Verse` - Individual verses with metadata
- **Verse Fields**: verse_text (with/without diacritics), surah, verse_number, juz, page, quarter, sajda
- **API**: `/verses/api/verses_list` with optional `?page=X` parameter
- **Admin**: Searchable by text, filterable by surah/juz/page

### Core Module
- **NavLink Model**: Database-driven navigation (navbar, footer, social links)
- **Types**: `nav` (navbar), `footer`, `social`
- **Context Processor**: Injects nav/footer links into all templates
- **Homepage**: Redirects to radio list

## Development Guidelines

### Code Conventions

1. **File Paths**: Use absolute paths for all file operations
   ```python
   # ✅ Good
   /home/marwanmohamed/Documents/work/Fathaker/radio/models.py

   # ❌ Bad
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
   - Use custom admin actions when needed

5. **Frontend**:
   - All JavaScript in separate files (not inline)
   - Use Bootstrap classes for styling
   - Support RTL layout (Arabic interface)
   - Avoid jQuery - use vanilla JavaScript

6. **API Design**:
   - Use DRF for all APIs
   - Implement proper serializers
   - Add pagination for list endpoints
   - Use descriptive endpoint names

### Important Patterns

#### Admin Customization Example
```python
class RadioAdmin(admin.ModelAdmin):
    list_display = ['name', 'rank', 'image_preview', 'audio_player']
    list_filter = ['tags']
    search_fields = ['name', 'description']
    readonly_fields = ['image_preview', 'audio_player', 'rank_controls']
```

#### API View Example
```python
class VersesList(generics.ListAPIView):
    queryset = Verse.objects.all()
    serializer_class = VerseSerializer
    permission_classes = [permissions.AllowAny]
```

#### Context Processor Pattern
```python
def navbar_links(request):
    return {
        'nav_links': NavLink.objects.filter(type='nav'),
        'footer_links': NavLink.objects.filter(type='footer')
    }
```

## Environment Configuration

Required `.env` variables:
```env
SECRETKEY=<django-secret-key>
DEBUG=1  # 0 for production, 1 for development
ALLOWEDHOSTS=localhost,127.0.0.1
DEBLOYED=0  # 0 for development, 1 for production
TRUSTEDORIGINS=https://yourdomain.com  # Production only
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

- `/` → Redirects to radio list
- `/admin/` → Django admin interface
- `/radio/` → Radio stations listing
- `/radio/rank/up/<id>/` → Rank up API (admin only)
- `/radio/rank/down/<id>/` → Rank down API (admin only)
- `/verses/api/verses_list/` → Verses API with optional `?page=X`

## Known Issues & Recent Fixes

### Recent Development (from git history)
- **aa0ee01**: Fixed radio not working if user searched
- **c333dab**: Fixed commit issues after merge PR #12 (some code was deleted)
- **9ac8ad7**: Added filter by tags in Radio admin page

### Things to Watch For
1. **Merge Conflicts**: Be careful when merging PRs - previous merge deleted some code
2. **Search Functionality**: Recently fixed search in radio module
3. **Tag Filtering**: Implemented both in admin and frontend

## Database Schema Notes

### Radio Table
- `rank` field controls display order (lower = higher priority)
- Tags are managed via django-taggit (many-to-many)
- Image uploads go to `media/radio/`

### Verse Table
- Complete Quran data (6,236 verses)
- Two text versions: with and without diacritics (Tashkeel)
- Rich metadata: juz, page, quarter, sajda flag
- Foreign key to Surah model

### NavLink Table
- Flexible navigation system
- Supports internal Django URLs and external links
- Font Awesome icon integration
- Ordering controlled by `order` field

## Static Files Organization

```
static/
├── base/
│   ├── css/
│   │   ├── bootstrap.rtl.min.css  # Bootstrap RTL version
│   │   ├── header.css             # Navbar styling
│   │   └── footer.css             # Footer styling
│   ├── js/
│   │   ├── bootstrap.bundle.min.js
│   │   └── swiper-bundle.min.js
│   └── img/
│       ├── logo.png
│       └── favicon.ico
└── radio/
    ├── css/radios.css              # Radio card styling
    ├── js/radios.js                # Search/filter logic
    └── img/radio_placeholder.png
```

## Security Considerations

1. **Admin-Only Endpoints**: Radio ranking APIs require `IsAdminUser` permission
2. **CSRF Protection**: Django middleware enabled
3. **Environment Variables**: Sensitive keys in `.env` (never commit)
4. **Media Uploads**: Validated through Django's `ImageField`
5. **Input Sanitization**: Always use Django's built-in form validation

## Testing Guidelines

- Write tests for all new features
- Test both authenticated and unauthenticated access
- Test API endpoints with various parameters
- Test admin actions and custom methods
- Run tests before committing: `python manage.py test`

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
- Python Version: 3.12
- Django Version: 5.0.4

---

**Last Updated**: 2026-02-08
**Project Status**: Active Development
