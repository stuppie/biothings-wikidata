from collections import Counter

from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.settings import api_settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets

from report.models import BotRun, Bot, Log
from report.serializers import BotSerializer, BotRunSerializer, LogSerializer


class BotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Bot.objects.all()
    serializer_class = BotSerializer


class BotRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BotRun.objects.all()
    serializer_class = BotRunSerializer

    def get_queryset(self):
        queryset = BotRun.objects.all()
        run_name = self.request.query_params.get('run_name', None)
        if run_name is not None:
            queryset = queryset.filter(run_name=run_name)
        return queryset


@api_view(['GET'])
def botrun_summary(request, pk):
    print(request)
    botrun = BotRun.objects.get(pk=pk)
    response = BotRunSerializer().to_representation(botrun)
    logs = Log.objects.filter(bot_run__pk=pk)
    actions = dict(Counter(logs.values_list("action", flat=True)))

    #errors = LogSerializer(Log.objects.filter(action="ERROR"), many=True).data

    response.update({
        "actions": actions,
        #"errors": errors
    })
    return Response(response)


class LogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer

    def get_queryset(self):
        queryset = self.queryset
        wdid = self.request.query_params.get('wdid', None)
        action = self.request.query_params.get('action', None)
        bot_run = self.request.query_params.get('bot_run', None)
        if wdid is not None:
            queryset = queryset.filter(wdid=wdid)
        if action is not None:
            queryset = queryset.filter(action=action)
        if bot_run is not None:
            queryset = queryset.filter(bot_run=bot_run)

        return queryset