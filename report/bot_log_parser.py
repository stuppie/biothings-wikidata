import glob
import json
import os
from datetime import datetime, timedelta
from dateutil.parser import parse as dateutil_parse

import pandas as pd

from report.models import Person, TaskRun, Task, Tag, Item, Log, Property, Source


def initial_setup():
    # run once

    person, _ = Person.objects.get_or_create(name="GSS", email="gstupp@scripps.edu")

    entrez, _ = Property.objects.get_or_create(name="entrez_gene_id", id="P351")
    ensembl_gene, _ = Property.objects.get_or_create(name="ensembl_gene_id", id="P594")
    uniprot, _ = Property.objects.get_or_create(name="uniprot_id", id="P352")
    ensembl_prot, _ = Property.objects.get_or_create(name="ensembl_protein_id", id="P705")
    do, _ = Property.objects.get_or_create(name="disease_ontology_id", id="P699")
    mesh, _ = Property.objects.get_or_create(name="mesh_id", id="P486")
    refseq_genome_id, _ = Property.objects.get_or_create(name="refseq_genome_id", id="P2248")

    #get_or_create_task("YeastBot", "GSS", domains=["gene", "protein"])


def get_or_create_task(task_name, maintainer=None, tags=None, properties=None):
    """

    :param task_name:
    :type task_name: str
    :param maintainer:
    :type maintainer: str
    :param tags:
    :type tags: List[str]
    :param properties:
    :type properties: List[str]
    :return:
    """
    if not Task.objects.filter(name=task_name).exists():
        assert maintainer is not None
        task = Task.objects.create(name=task_name, maintainer=Person.objects.get(name=maintainer))
    else:
        task = Task.objects.get(name=task_name)
    for tag in tags:
        task.tags.add(Tag.objects.get_or_create(name=tag)[0])
    for property in properties:
        task.properties.add(Property.objects.get_or_create(id=property)[0])
    return task


def create_task_run(task, run_name, timestamp, sources=None):
    """

    :param task:
    :param run_name:
    :param timestamp:
    :param sources:  {"ensembl": 86, "entrez": "20161029", "uniprot": "20161006"}
    :return:
    """
    tr_qs = TaskRun.objects.filter(task=task, timestamp=timestamp)
    if tr_qs.exists():
        tr = next(tr_qs.iterator())
        print("Warning! Task {} already exists. continue?".format(tr))
        choice = input().lower()
        if choice in {'yes','y', 'ye', ''}:
            return tr
        else:
            return None
    else:
        task_run = TaskRun.objects.create(task=task, name=run_name, timestamp=timestamp)
    sources = sources if sources else dict()
    for source, release in sources.items():
        source_model, _ = Source.objects.get_or_create(name=source, release=release)
        task_run.sources.add(source_model)
    return task_run


def django_log_pd(task_run, row):
    item = Item.objects.get_or_create(id=row.wdid)[0]
    prop, created = Property.objects.get_or_create(id=row.prop)
    if created:
        print("Property created: {}".format(prop))
    if row.level == "ERROR":
        return Log(wdid=item, timestamp=row.timestamp, task_run=task_run, action=row.level, external_id=row.external_id,
                   external_id_prop=prop, msg=row.msg)
    else:
        return Log(wdid=item, timestamp=row.timestamp, task_run=task_run, action=row.msg, external_id=row.external_id,
                   external_id_prop=prop)


def parse_log(file_path):
    df = pd.read_csv(file_path, sep=",", names=['level', 'timestamp', 'external_id', 'msg', 'wdid', 'prop'],
                     dtype={'external_id': str}, comment='#', quotechar='"', skipinitialspace=True)
    df = df.apply(lambda x: x.str.strip())
    df.timestamp = pd.to_datetime(df.timestamp, format='%m/%d/%Y %H:%M:%S')
    return df


def process_log(file_path):

    # read header
    with open(file_path) as f:
        line = f.readline()
    if not line.startswith("#"):
        raise ValueError("Expecting header in log file")
    metadata = json.loads(line[1:])
    print(metadata)

    task = get_or_create_task(metadata['name'], maintainer=metadata['maintainer'], tags=metadata['tags'], properties=metadata['properties'])
    task_run = create_task_run(task, metadata['run_id'], dateutil_parse(metadata['timestamp']), sources=metadata.get('release', None))

    df = parse_log(file_path)
    log_items = list(df.apply(lambda row: django_log_pd(task_run, row), axis=1))
    Log.objects.bulk_create(log_items)


def process_logs(log_dir):
    for file_path in glob.glob(os.path.join(log_dir,"*.log")):
        process_log(file_path)

#process_logs("/home/gstupp/projects/biothings/wikidata/logs")