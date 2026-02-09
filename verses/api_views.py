from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Verse
from .serializers import VerseSerializer


# #1
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
class SurahVerses(ListAPIView):
    """Get all verses of a surah by surah id"""
    serializer_class = VerseSerializer

    def get_queryset(self):
        surah_id = self.kwargs['surah_id']
        surah_prefix = f'S{surah_id:03d}'
        return Verse.objects.filter(verse_pk__startswith=surah_prefix)


# #4
class VerseDetail(APIView):
    """Get a specific verse by surah id and verse number"""

    def get(self, request, surah_id, verse_number):
        verse_pk = f'S{surah_id:03d}V{verse_number:03d}'
        verse = get_object_or_404(Verse, verse_pk=verse_pk)
        return Response(VerseSerializer(verse).data)


# #5
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


