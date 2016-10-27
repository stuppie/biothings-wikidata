import glob
import json
import os
from datetime import datetime, timedelta

import pandas as pd

from report.models import Person, BotRun, Bot, Domain, Log, Property, Source


def initial_setup():
    # run once

    person, _ = Person.objects.get_or_create(name="GSS", email="gstupp@scripps.edu")

    gene, _ = Domain.objects.get_or_create(name="gene")
    protein, _ = Domain.objects.get_or_create(name="protein")
    disease, _ = Domain.objects.get_or_create(name="disease")
    chromosome, _ = Domain.objects.get_or_create(name="chromosome")

    entrez, _ = Property.objects.get_or_create(name="entrez_gene_id", id="P351")
    ensembl_gene, _ = Property.objects.get_or_create(name="ensembl_gene_id", id="P594")
    uniprot, _ = Property.objects.get_or_create(name="uniprot_id", id="P352")
    ensembl_prot, _ = Property.objects.get_or_create(name="ensembl_protein_id", id="P705")
    do, _ = Property.objects.get_or_create(name="disease_ontology_id", id="P699")
    mesh, _ = Property.objects.get_or_create(name="mesh_id", id="P486")
    refseq_genome_id, _ = Property.objects.get_or_create(name="refseq_genome_id", id="P2248")

    gene.properties.add(entrez)
    gene.properties.add(ensembl_gene)
    protein.properties.add(uniprot)
    protein.properties.add(ensembl_prot)
    disease.properties.add(do)
    disease.properties.add(mesh)
    chromosome.properties.add(refseq_genome_id)

    get_or_create_bot("YeastBot", "GSS", domains=["gene", "protein"])


def get_or_create_bot(bot_name, maintainer=None, domains=None):
    if not Bot.objects.filter(name=bot_name).exists():
        assert maintainer is not None
        bot = Bot.objects.create(name=bot_name, maintainer=Person.objects.get(name=maintainer))
        for domain in domains:
            bot.domain.add(Domain.objects.get(name=domain))
    else:
        bot = Bot.objects.get(name=bot_name)
    return bot


def get_or_create_bot_run(bot, run_id, run_name, started=None, ended=None, domain=None, sources=None):
    if not started:
        started = datetime.now() - timedelta(minutes=1)
    if not ended:
        ended = datetime.now()
    bot_run, _ = BotRun.objects.get_or_create(bot=bot, run_id=run_id, run_name=run_name,
                                              defaults={'started': started, 'ended': ended,
                                                        'domain': Domain.objects.get(name=domain)})
    sources = sources if sources else dict()
    for source, release in sources.items():
        source_model, _ = Source.objects.get_or_create(name=source, release=release)
        bot_run.sources.add(source_model)
    return bot_run


def django_log_pd(bot_run, row):
    prop, created = Property.objects.get_or_create(id=row.prop)
    if created:
        print("Property created: {}".format(prop))
    if row.level == "ERROR":
        return Log(wdid=row.wdid, time=row.datetime, bot_run=bot_run, action=row.level, external_id=row.external_id,
                   external_id_prop=prop, msg=row.msg)
    else:
        return Log(wdid=row.wdid, time=row.datetime, bot_run=bot_run, action=row.msg, external_id=row.external_id,
                   external_id_prop=prop)


def parse_log(file_path):
    df = pd.read_csv(file_path, sep=",", names=['level', 'datetime', 'external_id', 'msg', 'wdid', 'prop'],
                     dtype={'external_id': str}, comment='#', quotechar='"', skipinitialspace=True)
    df = df.apply(lambda x: x.str.strip())
    df.datetime = pd.to_datetime(df.datetime, format='%m/%d/%Y %H:%M:%S')
    return df


def process_log(file_path):

    # read header
    with open(file_path) as f:
        line = f.readline()
    if not line.startswith("#"):
        raise ValueError("Expecting header in log file")
    metadata = json.loads(line[1:])
    print(metadata)

    bot = Bot.objects.get(name=metadata['bot_name'])
    bot_run = get_or_create_bot_run(bot, metadata['run_id'], metadata['run_name'], domain=metadata['domain'], sources=metadata.get('release', None))

    df = parse_log(file_path)
    #df = df.query("msg != 'SKIP'")
    log_items = list(df.apply(lambda row: django_log_pd(bot_run, row), axis=1))
    Log.objects.bulk_create(log_items)


def process_logs(log_dir):
    for file_path in glob.glob(os.path.join(log_dir,"*.log")):
        process_log(file_path)

#process_logs("/home/gstupp/projects/biothings/wikidata/logs")