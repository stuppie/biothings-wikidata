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
            'tags': obj.tag.all().values_list("name", flat=True)
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
            'bot_name': obj.bot.name,
            'run_id': obj.run_id,
            'run_name': obj.run_name,
            'maintainer': obj.bot.maintainer.name
        }
        # get started and ended time from logs associated with this run
        logs = Log.objects.filter(bot_run__pk=obj.pk).order_by("time")
        started = logs.first().time
        ended = logs.last().time

        # get counts of all actions from logs
        actions = dict(Counter(logs.values_list("action", flat=True)))
        actions['__total__'] = sum(actions.values())
        response.update({
            "actions": actions,
            'started': started,
            'ended': ended
        })

        # get sources used for this run
        response['sources'] = SourceSerializer(obj.sources.all(), many=True).data

        return response

    class Meta:
        model = TaskRun


class LogSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        return {
            #'bot_run': BotRunSerializer().to_representation(obj.bot_run),
            'bot_run': obj.bot_run.id,
            'wdid': obj.wdid,
            'time': obj.time,
            'action': obj.action,
            'external_id': obj.external_id,
            'external_id_prop': obj.external_id_prop.id,
            'msg': obj.msg
        }

    class Meta:
        model = Log