from django.db import models


class Person(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    email = models.CharField(max_length=64, null=True)

    def __str__(self):
        return '{}'.format(self.name)


class Source(models.Model):
    # data source. e.g. Ensembl release 86
    name = models.CharField(max_length=64)
    url = models.URLField(null=True)
    release = models.CharField(null=True, max_length=64)

    def __str__(self):
        return '{}: {}'.format(self.name, self.release)

    class Meta:
        unique_together = ("name", "release")


class Property(models.Model):
    name = models.CharField(max_length=64)
    id = models.CharField(max_length=10, primary_key=True)

    def __str__(self):
        return '{}: {}'.format(self.id, self.name)


class Tag(models.Model):
    # gene, protein, drug, disease, microbial
    name = models.CharField(max_length=64, primary_key=True)

    def __str__(self):
        return '{}'.format(self.name)


class Item(models.Model):
    # Represents a wikidata item
    id = models.CharField(max_length=16, primary_key=True)
    name = models.CharField(max_length=64, null=True)

    def __str__(self):
        return '{}'.format(self.id)


class Task(models.Model):
    """
    A task is a "bot" that operates within a certain scope of items on a specific set of properties.

    e.g. A task that adds "encodes" property between microbial genes and proteins
    name: "microbial_encodes"
    tags: "microbial" "gene" "protein"
    properties: [ encodes:P123 ]
    maintainer: "GSS"

    The item scope can be determined from the log files
    """
    name = models.CharField(max_length=64, primary_key=True)
    tags = models.ManyToManyField(Tag)
    properties = models.ManyToManyField(Property)
    maintainer = models.ForeignKey(Person)

    def __str__(self):
        return self.name


class TaskRun(models.Model):
    """
    TaskRun: An instance of a Task that gets run

    e.g.
    task: "microbial_encodes"
    sources: ensembl version 86
    timestamp: 2016-10-26 11:11:11
    run_name: (optional)
    """
    task = models.ForeignKey(Task)
    sources = models.ManyToManyField(Source)
    timestamp = models.DateTimeField()
    name = models.CharField(max_length=64)

    def __str__(self):
        return '{}: {}: {}'.format(self.task.name, self.timestamp, self.name)

    class Meta:
        ordering = ("timestamp",)


class Log(models.Model):
    task_run = models.ForeignKey(TaskRun)
    wdid = models.ForeignKey(Item)
    timestamp = models.DateTimeField()
    action = models.CharField(max_length=64)  # CREATE, UPDATE, ERROR
    external_id = models.CharField(max_length=255, null=True)
    external_id_prop = models.ForeignKey(Property, null=True)
    msg = models.CharField(max_length=255, null=True)  # an (optional) error message

    def __str__(self):
        return '{}'.format(self.wdid, self.bot_run.bot, self.action)
