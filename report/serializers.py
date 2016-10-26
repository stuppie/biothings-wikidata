from collections import Counter

from rest_framework import generics

from .models import *
from rest_framework import serializers


class BotSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        return {
            'bot_name': obj.name,
            'maintainer': obj.maintainer.name,
            'email': obj.maintainer.email
        }

    class Meta:
        model = Bot


class BotRunSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        response = {
            'id': obj.pk,
            'bot_name': obj.bot.name,
            'run_id': obj.run_id,
            'run_name': obj.run_name,
            'maintainer': obj.bot.maintainer.name
        }
        logs = Log.objects.filter(bot_run__pk=obj.pk).order_by("time")
        started = logs.first().time
        ended = logs.last().time
        actions = dict(Counter(logs.values_list("action", flat=True)))
        response.update({
            "actions": actions,
            'started': started,
            'ended': ended
        })
        return response

    class Meta:
        model = BotRun


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