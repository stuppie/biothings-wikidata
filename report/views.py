from collections import Counter

from django.shortcuts import render
from rest_framework import filters

from rest_framework.views import APIView
from rest_framework.settings import api_settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets

from report.models import TaskRun, Task, Log, Item
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
            queryset = queryset.filter(name=run_name)
        task_name = self.request.query_params.get('task_name', None)
        if task_name is not None:
            queryset = queryset.filter(task__name=task_name)

        return queryset

    def filter_queryset(self, queryset):
        queryset = super(TaskRunViewSet, self).filter_queryset(queryset)
        queryset = queryset.order_by("timestamp")
        return queryset


class LogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer

    def get_queryset(self):
        queryset = self.queryset
        wdid = self.request.query_params.get('wdid', None)
        level = self.request.query_params.get('level', None)
        task_name = self.request.query_params.get('task_name', None)
        run_name = self.request.query_params.get('run_name', None)
        run = self.request.query_params.get('run', None)
        msg = self.request.query_params.get('msg', None)
        if wdid is not None:
            queryset = queryset.filter(wdid=wdid)
        if level is not None:
            queryset = queryset.filter(level=level)
        if task_name is not None:
            queryset = queryset.filter(task_run__task__name=task_name)
        if run_name is not None:
            queryset = queryset.filter(task_run__name=run_name)
        if run is not None:
            queryset = queryset.filter(task_run=run)
        if msg is not None:
            queryset = queryset.filter(msg=msg)

        return queryset