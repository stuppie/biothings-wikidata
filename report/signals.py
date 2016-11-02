import requests
from django.db.models.signals import post_save
from django.dispatch import receiver

from report.models import Property


@receiver(post_save, sender=Property)
def lookup_prop_name(sender, **kwargs):
    instance = kwargs['instance']
    url = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids={}&props=labels&languages=en&format=json".format(instance.id)
    response = requests.get(url).json()
    if 'missing' in response['entities'][instance.id]:
        return
    label = response['entities'][instance.id]['labels']['en']['value']
    Property.objects.filter(pk=instance.pk).update(name=label)