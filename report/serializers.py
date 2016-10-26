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
        return {
            'bot_name': obj.bot.name,
            'run_id': obj.run_id,
            'run_name': obj.run_name,
            'started': obj.started,
            'ended': obj.ended
        }

    class Meta:
        model = BotRun