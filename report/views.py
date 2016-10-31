from collections import Counter

from django.shortcuts import render
from rest_framework import filters

from rest_framework.views import APIView
from rest_framework.settings import api_settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets

from report.models import TaskRun, Task, Log
from report.serializers import TaskSerializer, TaskRunSerializer, LogSerializer


class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class TaskRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TaskRun.objects.all()
    serializer_class = TaskRunSerializer

    def get_queryset(self):
        queryset = TaskRun.objects.all()
        run_name = self.request.query_params.get('run_name', None)
        if run_name is not None:
            queryset = queryset.filter(run_name=run_name)
        task_name = self.request.query_params.get('task_name', None)
        if task_name is not None:
            queryset = queryset.filter(bot__name=task_name)

        return queryset

    def filter_queryset(self, queryset):
        queryset = super(TaskRunViewSet, self).filter_queryset(queryset)
        queryset = queryset.order_by("run_id")
        return queryset


@api_view(['GET'])
def botrun_summary(request, pk):
    print(request)
    botrun = TaskRun.objects.get(pk=pk)
    response = TaskRunSerializer().to_representation(botrun)
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