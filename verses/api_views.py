from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from .models import Verse
from .serializers import VerseSerializer


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

