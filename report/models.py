from django.db import models


class Person(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    email = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return '{}'.format(self.name)


class Source(models.Model):
    # data source
    name = models.CharField(max_length=64)
    url = models.URLField(blank=True, null=True)
    release = models.CharField(blank=True, max_length=64)

    def __str__(self):
        return '{}: {}'.format(self.name, self.release)

    class Meta:
        unique_together = ("name", "release")


class Property(models.Model):
    name = models.CharField(max_length=64)
    id = models.CharField(max_length=10, primary_key=True)

    def __str__(self):
        return '{}: {}'.format(self.id, self.name)


class Domain(models.Model):
    # gene, protein, drug, disease, etc
    name = models.CharField(max_length=64, primary_key=True)
    properties = models.ManyToManyField(Property)

    def __str__(self):
        return '{}'.format(self.name)


class Bot(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    #data_source = models.ManyToManyField(Source)
    domain = models.ManyToManyField(Domain)
    maintainer = models.ForeignKey(Person)

    def __str__(self):
        return self.name


class BotRun(models.Model):
    bot = models.ForeignKey(Bot)
    run_id = models.CharField(max_length=64)
    run_name = models.CharField(max_length=64)
    started = models.DateTimeField()
    ended = models.DateTimeField()
    domain = models.ForeignKey(Domain, null=True)
    sources = models.ManyToManyField(Source)

    def __str__(self):
        return '{}: {}: {}'.format(self.bot, self.run_name, self.run_id)

    class Meta:
        unique_together = ("bot", "run_id", "run_name")
        ordering = ("run_id",)


class Log(models.Model):
    bot_run = models.ForeignKey(BotRun)
    wdid = models.CharField(max_length=20)
    time = models.DateTimeField()

    action = models.CharField(max_length=64)  # CREATE, UPDATE, ERROR
    external_id = models.CharField(max_length=255, null=True)
    external_id_prop = models.ForeignKey(Property, null=True)
    msg = models.CharField(max_length=255, null=True)  # an (optional) error message

    def __str__(self):
        return '{}'.format(self.wdid, self.bot_run.bot, self.action)


"""
Bot:
    name: MicrobeBot
    data_source = Entrez, Uniprot, etc. (optional)
    domain = genes, proteins (optional)
    maintainer = TP

BotRun:
    bot: MicrobeBot
    run_id: 20161025 (used to link to biothings)
    run_name: chlamydia_genes
    (bot, run_id, run_name) are unique_together
    started: datetime.datetime(2016, 10, 25, 11, 40, 24, 148298)
    ended: datetime.datetime(2016, 10, 26, 11, 40, 24, 148298)
    domain: gene (optional)

Log:
    bot_run: (MicrobeBot, 20161025, Chlamydia)
    wdid: Q123456
    time: datetime.datetime(2016, 10, 26, 11, 40, 24, 148298)
    action: {CREATE, UPDATE, ERROR, etc...}
    external_id: 856305 (optional)
    external_id_prop: P351 (optional)
    msg: missing stop position (optional)

"""
