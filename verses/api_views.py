from django.db.models import Q, Min
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from .models import Verse
from .serializers import VerseSerializer


# #1
@extend_schema_view(
    get=extend_schema(
        summary='List all verses or filter by page',
        parameters=[
            OpenApiParameter(
                name='page',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Filter by Quran page number (1-604)',
            ),
        ],
        responses=VerseSerializer(many=True),
    ),
)
class VersesList(ListAPIView):
    """
        Endpoint To Get all verses
        or get a page of quran using ?page=page_number
    """
    queryset = Verse.objects.all()
    serializer_class = VerseSerializer

    def list(self, request, *args, **kwargs):
        page = self.request.GET.get('page', None)
        query = self.get_queryset()
        if page:
            query = query.filter(page=page)

        return Response(VerseSerializer(query, many=True).data)


# #2
@extend_schema_view(
    get=extend_schema(
        summary='Search verses by keyword',
        parameters=[
            OpenApiParameter(
                name='q',
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Search keyword (matches verse text with or without tashkeel)',
            ),
        ],
    ),
)
class VersesSearch(ListAPIView):
    """Search verses by keyword using ?q=keyword"""
    serializer_class = VerseSerializer

    def get_queryset(self):
        q = self.request.GET.get('q', '')
        if not q:
            return Verse.objects.none()
        return Verse.objects.filter(
            Q(verse__icontains=q) | Q(verse_without_tashkeel__icontains=q)
        )


# #3
@extend_schema_view(
    get=extend_schema(
        summary='Get all verses of a surah, optionally filtered by keyword',
        parameters=[
            OpenApiParameter(
                name='surah_id',
                type=int,
                location=OpenApiParameter.PATH,
                description='Surah number (1-114)',
            ),
            OpenApiParameter(
                name='q',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Optional search keyword to filter verses within the surah',
            ),
        ],
    ),
)
class SurahVerses(ListAPIView):
    """Get all verses of a surah by surah id, optionally filtered by keyword using ?q=keyword"""
    serializer_class = VerseSerializer

    def get_queryset(self):
        surah_id = self.kwargs['surah_id']
        surah_prefix = f'S{surah_id}V'
        queryset = Verse.objects.filter(verse_pk__startswith=surah_prefix)
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(verse__icontains=q) | Q(verse_without_tashkeel__icontains=q)
            )
        return queryset


# #4
class VerseDetail(APIView):
    """Get a specific verse by surah id and verse number"""

    @extend_schema(
        summary='Get a specific verse',
        parameters=[
            OpenApiParameter(
                name='surah_id',
                type=int,
                location=OpenApiParameter.PATH,
                description='Surah number (1-114)',
            ),
            OpenApiParameter(
                name='verse_number',
                type=int,
                location=OpenApiParameter.PATH,
                description='Verse number within the surah',
            ),
        ],
        responses=VerseSerializer,
    )
    def get(self, request, surah_id, verse_number):
        verse_pk = f'S{surah_id}V{verse_number}'
        verse = get_object_or_404(Verse, verse_pk=verse_pk)
        return Response(VerseSerializer(verse).data)


# #5
@extend_schema_view(
    get=extend_schema(
        summary='Get verses by range',
        parameters=[
            OpenApiParameter(
                name='start',
                type=int,
                location=OpenApiParameter.PATH,
                description='Start verse number in Quran (1-6236)',
            ),
            OpenApiParameter(
                name='end',
                type=int,
                location=OpenApiParameter.PATH,
                description='End verse number in Quran (1-6236)',
            ),
        ],
    ),
)
class VersesRange(ListAPIView):
    """Get verses by number_in_quran range"""
    serializer_class = VerseSerializer

    def get_queryset(self):
        start = self.kwargs['start']
        end = self.kwargs['end']
        if start > end:
            start, end = end, start
        return Verse.objects.filter(number_in_quran__range=(start, end))


# #6
@extend_schema_view(
    get=extend_schema(
        summary='Search verses that start with given text',
        parameters=[
            OpenApiParameter(
                name='q',
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Letters the verse should start with (matches with or without tashkeel)',
            ),
        ],
    ),
)
class VersesStartsWith(ListAPIView):
    """Search verses that start with given letters using ?q=letters"""
    serializer_class = VerseSerializer

    def get_queryset(self):
        q = self.request.GET.get('q', '')
        if not q:
            return Verse.objects.none()
        return Verse.objects.filter(
            Q(verse__startswith=q) | Q(verse_without_tashkeel__startswith=q)
        )


# #7
@extend_schema_view(
    get=extend_schema(
        summary='Search verses that end with given text',
        parameters=[
            OpenApiParameter(
                name='q',
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Letters the verse should end with (matches with or without tashkeel)',
            ),
        ],
    ),
)
class VersesEndsWith(ListAPIView):
    """Search verses that end with given letters using ?q=letters"""
    serializer_class = VerseSerializer

    def get_queryset(self):
        q = self.request.GET.get('q', '')
        if not q:
            return Verse.objects.none()
        return Verse.objects.filter(
            Q(verse__endswith=q) | Q(verse_without_tashkeel__endswith=q)
        )


# #8 Mushaf Page API
@extend_schema_view(
    get=extend_schema(
        summary='Get mushaf page data for the Quran reader',
        parameters=[
            OpenApiParameter(
                name='page',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Mushaf page number (1-604), defaults to 1',
            ),
        ],
    ),
)
class MushafPageAPI(APIView):
    """Get enriched data for a mushaf page, including verses and surah headers."""

    def get(self, request):
        page_num = request.GET.get('page', 1)
        try:
            page_num = int(page_num)
        except (ValueError, TypeError):
            page_num = 1
        page_num = max(1, min(604, page_num))

        total_pages = 604

        verses = Verse.objects.filter(page=page_num).select_related('surah').order_by('number_in_quran')

        # Build enriched verse data with surah-start flags
        verses_data = []
        seen_surahs = set()
        surahs_on_page = []

        for v in verses:
            is_first_in_surah = v.number_in_surah == 1
            surah_id = v.surah_id

            if surah_id not in seen_surahs:
                seen_surahs.add(surah_id)
                surahs_on_page.append({
                    'id': surah_id,
                    'name': v.surah.name,
                })

            verses_data.append({
                'verse_pk': v.verse_pk,
                'verse': v.verse,
                'number_in_surah': v.number_in_surah,
                'number_in_quran': v.number_in_quran,
                'surah_id': surah_id,
                'surah_name': v.surah.name,
                'juz': v.juz,
                'the_quarter': v.the_quarter,
                'is_sajda': v.is_sajda,
                'is_first_in_surah': is_first_in_surah,
            })

        # Determine juz for this page
        juz = verses_data[0]['juz'] if verses_data else 1

        return Response({
            'page': page_num,
            'total_pages': total_pages,
            'juz': juz,
            'surahs_on_page': surahs_on_page,
            'verses': verses_data,
        })
