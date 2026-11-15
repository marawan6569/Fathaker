from django.conf import settings
from django.utils.cache import patch_vary_headers
import re


class NoStoreMiddleware:
    """Private by default; explicitly audited anonymous Quran JSON may use the CDN.

    Keep this outside SessionMiddleware so response cookie writes are visible.
    WhiteNoise remains outside it and owns static-asset cache headers.
    """
    MAX_PUBLIC_BYTES = 1024 * 1024

    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def public_endpoint(request):
        match = request.resolver_match
        if not match or match.namespace != 'verses':
            return False
        query = request.GET
        name, args = match.url_name, match.kwargs
        if name == 'mushaf_page_api':
            return (set(query) <= {'page'} and
                    ('page' not in query or (len(query.getlist('page')) == 1 and
                     re.fullmatch(r'[0-9]{1,3}', query['page']) is not None and
                     1 <= int(query['page']) <= 604)))
        if name == 'mutashabihat_by_ayah_api':
            return (set(query) == {'ayah'} and len(query.getlist('ayah')) == 1 and
                    re.fullmatch(r'S[1-9][0-9]{0,2}V[1-9][0-9]{0,2}', query['ayah']) is not None)
        if query:
            return False
        if name == 'verse_detail_api':
            return True
        if name == 'surah_verses_api':
            return 1 <= args['surah_id'] <= 114
        if name == 'verses_range_api':
            return (1 <= min(args['start'], args['end']) and
                    max(args['start'], args['end']) <= 6236 and
                    abs(args['start'] - args['end']) < 100)
        return name == 'mutashabihat_phrase_detail_api'

    def __call__(self, request):
        # Hosting rewrites Host to the Run service. Restore only our two known
        # public Hosting names, never an arbitrary client-controlled host.
        for header in ('HTTP_X_FH_REQUESTED_HOST', 'HTTP_X_FORWARDED_HOST'):
            host = request.META.get(header, '')
            if host in settings.FIREBASE_HOSTS and host in settings.ALLOWED_HOSTS:
                request.META['HTTP_HOST'] = host
                break
        response = self.get_response(request)
        ttl = settings.PUBLIC_API_CACHE_TTL
        cache_control = response.get('Cache-Control', '').lower()
        vary = response.get('Vary', '')
        safe = (
            ttl > 0 and request.method in ('GET', 'HEAD') and
            not request.META.get('HTTP_COOKIE') and
            'HTTP_AUTHORIZATION' not in request.META and
            not getattr(getattr(request, 'user', None), 'is_authenticated', False) and
            not response.cookies and not response.has_header('Set-Cookie') and
            not response.streaming and response.status_code == 200 and
            response.get('Content-Type', '').split(';')[0] == 'application/json' and
            not response.has_header('Content-Disposition') and
            'private' not in cache_control and 'no-store' not in cache_control and
            '*' not in vary and
            len(response.content) <= self.MAX_PUBLIC_BYTES and
            self.public_endpoint(request)
        )
        if safe:
            response['Cache-Control'] = f'public, max-age=0, s-maxage={ttl}'
            patch_vary_headers(response, ('Cookie', 'Authorization', 'Accept'))
        else:
            response['Cache-Control'] = 'private, no-store'
        return response
