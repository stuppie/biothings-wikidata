import json
import os
from datetime import datetime

from ProteinBoxBot_Core import PBB_Core, PBB_login, PBB_Helpers
from dateutil.parser import parse as date_parse
from pymongo import MongoClient
from tqdm import tqdm

from local import WDUSER, WDPASS
from .IPRTerm import IPRTerm

__metadata__ = {'name': 'InterproBot_Items',
                'maintainer': 'GSS',
                'tags': ['interpro'],
                'properties': ["P279", "P2926", 'P527', 'P361']
                }


def main(version_info, log_dir="./logs", run_id=None, mongo_uri="mongodb://localhost:27017",
         mongo_db="wikidata_src", mongo_coll="interpro", debug=False):
    # data sources
    db = MongoClient(mongo_uri)[mongo_db]
    interpro_coll = db[mongo_coll]

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

    # create/update all interpro items
    terms = []
    cursor = interpro_coll.find(no_cursor_timeout=True)
    for n, doc in tqdm(enumerate(cursor), total=cursor.count()):
        doc['release_wdid'] = release_wdid
        term = IPRTerm(**doc)
        term.create_item(login)
        terms.append(term)
        if debug and n>100:
            break
    cursor.close()

    # create/update interpro item relationships
    IPRTerm.refresh_ipr_wd()
    for term in tqdm(terms):
        term.create_relationships(login)

    return os.path.join(log_dir, log_name)