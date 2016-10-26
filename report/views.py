from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.settings import api_settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets

from report.models import BotRun, Bot
from report.serializers import BotSerializer, BotRunSerializer


class BotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Bot.objects.all()
    serializer_class = BotSerializer


class BotRunViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = BotRun.objects.all()
    serializer_class = BotRunSerializer

    def get_queryset(self):
        queryset = BotRun.objects.all()
        run_name = self.request.query_params.get('run_name', None)
        if run_name is not None:
            queryset = queryset.filter(run_name=run_name)
        return queryset