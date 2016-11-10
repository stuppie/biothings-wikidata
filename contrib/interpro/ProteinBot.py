import json
import os
from datetime import datetime

from ProteinBoxBot_Core import PBB_Core, PBB_login, PBB_Helpers
from dateutil.parser import parse as date_parse
from pymongo import MongoClient
from tqdm import tqdm

from local import WDUSER, WDPASS
from .IPRTerm import IPRTerm

__metadata__ = {'name': 'InterproBot_Proteins',
                'maintainer': 'GSS',
                'tags': ['protein', 'interpro'],
                'properties': ["P279", "P527", "P361"]
                }

INTERPRO = "P2926"
UNIPROT = "P352"


def create_uniprot_relationships(login, release_wdid, collection, taxon=None):
    # only do uniprot proteins that are already in wikidata
    if taxon:
        uniprot2wd = PBB_Helpers.id_mapper(UNIPROT, (("P703", taxon),))
        fast_run_base_filter = {UNIPROT: "", "P703": taxon}
    else:
        uniprot2wd = PBB_Helpers.id_mapper(UNIPROT)
        fast_run_base_filter = {UNIPROT: ""}

    cursor = collection.find({'_id': {'$in': list(uniprot2wd.keys())}}, no_cursor_timeout=True)
    for doc in tqdm(cursor, total=cursor.count()):
        uniprot_id = doc['_id']
        statements = []
        # uniprot ID. needed for PBB_core to find uniprot item
        # statements.append(PBB_Core.WDExternalID(value=uniprot_id, prop_nr=UNIPROT))

        ## References
        # stated in Interpro version XX.X
        ref_stated_in = PBB_Core.WDItemID(release_wdid, 'P248', is_reference=True)
        ref_ipr = PBB_Core.WDString("http://www.ebi.ac.uk/interpro/protein/{}".format(uniprot_id), "P854",
                                    is_reference=True)
        reference = [ref_stated_in, ref_ipr]

        if doc['subclass']:
            for f in doc['subclass']:
                statements.append(PBB_Core.WDItemID(value=IPRTerm.ipr2wd[f], prop_nr='P279', references=[reference]))
        if doc['has_part']:
            for hp in doc['has_part']:
                statements.append(PBB_Core.WDItemID(value=IPRTerm.ipr2wd[hp], prop_nr='P527', references=[reference]))

        if uniprot_id not in uniprot2wd:
            print("wdid_not_found " + uniprot_id + " " + uniprot2wd[uniprot_id])
            PBB_Core.WDItemEngine.log("ERROR", PBB_Helpers.format_msg(uniprot_id, UNIPROT, None, "wdid_not_found"))

        wd_item = PBB_Core.WDItemEngine(wd_item_id=uniprot2wd[uniprot_id], domain="proteins", data=statements,
                                        fast_run=True, fast_run_base_filter=fast_run_base_filter,
                                        append_value=["P279", "P527", "P361"])

        if wd_item.create_new_item:
            raise ValueError("something bad happened")
        PBB_Helpers.try_write(wd_item, uniprot_id, INTERPRO, login, edit_summary="add/update family and/or domains")

    cursor.close()


def main(version_info, log_dir="./logs", run_id=None, mongo_uri="mongodb://localhost:27017",
         mongo_db="wikidata_src", mongo_coll="interpro_protein", taxon=None):
    # data sources
    db = MongoClient(mongo_uri)[mongo_db]
    collection = db[mongo_coll]

    if run_id is None:
        run_id = datetime.now().strftime('%Y%m%d_%H:%M')
    if log_dir is None:
        log_dir = "./logs"
    __metadata__['run_id'] = run_id
    __metadata__['timestamp'] = str(datetime.now())

    login = PBB_login.WDLogin(user=WDUSER, pwd=WDPASS)

    # handle version_info. parsed from interpro xml file. looks like:
    # { "_id" : "INTERPRO", "dbname" : "INTERPRO", "file_date" : "03-NOV-16", "version" : "60.0", "entry_count" : "29700" }
    version = version_info['version']
    pub_date = date_parse(version_info['file_date'])
    release = PBB_Helpers.Release(title="InterPro Release {}".format(version),
                                  description="Release {} of the InterPro database & software".format(version),
                                  edition_of_wdid="Q3047275",
                                  edition=version,
                                  pub_date=pub_date,
                                  archive_url="ftp://ftp.ebi.ac.uk/pub/databases/interpro/{}/".format(version))
    release_wdid = release.get_or_create(login)
    __metadata__['release'] = {
        'InterPro': {'release': version, '_id': 'InterPro', 'wdid': release_wdid, 'timestamp': str(pub_date)}}

    log_name = '{}-{}.log'.format(__metadata__['name'], __metadata__['run_id'])
    if PBB_Core.WDItemEngine.logger is not None:
        PBB_Core.WDItemEngine.logger.handles = []
    PBB_Core.WDItemEngine.setup_logging(log_dir=log_dir, log_name=log_name, header=json.dumps(__metadata__))

    create_uniprot_relationships(login, release_wdid, collection, taxon=taxon)

    return os.path.join(log_dir, log_name)
