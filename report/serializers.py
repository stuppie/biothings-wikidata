import copy
from collections import Counter

from rest_framework import generics

from .models import *
from rest_framework import serializers


class TaskSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        return {
            'name': obj.name,
            'maintainer': obj.maintainer.name,
            'email': obj.maintainer.email,
            'tags': obj.tags.all().values_list("name", flat=True)
        }

    class Meta:
        model = Task


class SourceSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        return {
            'name': obj.name,
            'url': obj.url,
            'release': obj.release
        }

    class Meta:
        model = Source


class TaskRunSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        response = {
            'id': obj.pk,
            'name': obj.name,
            'task_name': obj.task.name,
            'timestamp': obj.timestamp,
            'maintainer': obj.task.maintainer.name
        }
        # get started and ended time from logs associated with this run
        logs = Log.objects.filter(task_run__pk=obj.pk).order_by("timestamp")
        started = logs.first().timestamp
        ended = logs.last().timestamp
        response.update({
            'started': started,
            'ended': ended
        })

        # get counts of all levels from logs
        levels = dict(Counter(logs.values_list("level", flat=True)))
        total = sum(levels.values())
        response['messages'] = {"counts": copy.copy(levels)}
        response['messages']["counts"]['__total__'] = total

        for level in levels:
            # get counts of all messages from logs that are type 'level'
            messages = dict(Counter(logs.filter(level=level).values_list("msg", flat=True)))
            response['messages'].update({level: messages})

        # get sources used for this run
        response['sources'] = SourceSerializer(obj.sources.all(), many=True).data

        return response

    class Meta:
        model = TaskRun


class LogSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        return {
            #'bot_run': BotRunSerializer().to_representation(obj.bot_run),
            'run_id': obj.task_run.id,
            'run_name': obj.task_run.name,
            'task_name': obj.task_run.task.name,
            'wdid': obj.wdid.id,
            'timestamp': obj.timestamp,
            'level': obj.level,
            'external_id': obj.external_id,
            'external_id_prop': obj.external_id_prop.id,
            'msg': obj.msg
        }

    class Meta:
        model = Log