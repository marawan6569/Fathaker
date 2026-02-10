from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.db.models import F
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework import status, serializers
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from core.models import NavLink
from .models import Radio


class RadioRankDown(APIView):
    allowed_methods = ['get']
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='Move radio rank down',
        description='Swap the radio with the one below it. Admin only. Redirects back to the referring page.',
        parameters=[
            OpenApiParameter(name='id', type=int, location=OpenApiParameter.PATH, description='Radio ID'),
        ],
        responses={302: None},
    )
    def get(self, request, *args, **kwargs):
        try:
            radio_id = self.kwargs.get("id", None)
            radio = Radio.objects.get(id=radio_id)
            prev_radio = Radio.objects.get(rank=radio.rank + 1)

            current_rank = radio.rank
            prev_rank = prev_radio.rank

            radio.rank = - 1
            prev_radio.rank = -2
            radio.save()
            prev_radio.save()

            radio.rank = prev_rank
            prev_radio.rank = current_rank
            radio.save()
            prev_radio.save()

            messages.success(request, f'{radio.name} rank changed from {current_rank} to {prev_rank} successfully.')
        except Exception as e:
            messages.error(request, f'Failed to swap ranks.\n Errors: {e}')

        referer = request.META.get('HTTP_REFERER')
        return redirect(referer if referer else reverse("admin:radio_radio_changelist"))


class RadioRankUp(APIView):
    allowed_methods = ['get']
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='Move radio rank up',
        description='Swap the radio with the one above it. Admin only. Redirects back to the referring page.',
        parameters=[
            OpenApiParameter(name='id', type=int, location=OpenApiParameter.PATH, description='Radio ID'),
        ],
        responses={302: None},
    )
    def get(self, request, *args, **kwargs):
        try:
            radio_id = self.kwargs.get("id", None)
            radio = Radio.objects.get(id=radio_id)
            next_radio = Radio.objects.get(rank=radio.rank - 1)

            current_rank = radio.rank
            next_rank = next_radio.rank

            radio.rank = - 1
            next_radio.rank = -2
            radio.save()
            next_radio.save()

            radio.rank = next_rank
            next_radio.rank = current_rank
            radio.save()
            next_radio.save()

            messages.success(request, f'{radio.name} rank changed from {current_rank} to {next_rank} successfully.')
        except Exception as e:
            messages.error(request, f'Failed to swap ranks.\n Errors: {e}')

        referer = request.META.get('HTTP_REFERER')
        return redirect(referer if referer else reverse("admin:radio_radio_changelist"))


class RadiosList(TemplateView):
    template_name = "radio/radios_list.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data()
        data['radios'] = Radio.objects.all().prefetch_related("tags")
        data['current_page_link'] = get_object_or_404(NavLink, name="radios_list")
        return data


class RadioDetail(TemplateView):
    template_name = "radio/radio_detail.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        radio = get_object_or_404(Radio, slug=self.kwargs['slug'])
        Radio.objects.filter(pk=radio.pk).update(views_count=F('views_count') + 1)
        radio.refresh_from_db()
        data['radio'] = radio
        data['current_page_link'] = get_object_or_404(NavLink, name="radios_list")
        return data


class RadioLike(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Like a radio station',
        description='Increment the like count for a radio station. Returns the updated like count.',
        parameters=[
            OpenApiParameter(name='slug', type=str, location=OpenApiParameter.PATH, description='Radio slug'),
        ],
        request=None,
        responses=inline_serializer(
            name='RadioLikeResponse',
            fields={'likes_count': serializers.IntegerField()},
        ),
    )
    def post(self, request, slug):
        radio = get_object_or_404(Radio, slug=slug)
        Radio.objects.filter(pk=radio.pk).update(likes_count=F('likes_count') + 1)
        radio.refresh_from_db()
        return Response({'likes_count': radio.likes_count}, status=status.HTTP_200_OK)
