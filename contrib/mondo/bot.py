"""
Will simply add umls IDs to diseases
Where disease it uniquely specified by its doid
"""

import argparse
import logging
import os
from datetime import datetime

import biothings
from ProteinBoxBot_Core import PBB_Core, PBB_login
from ProteinBoxBot_Core.PBB_Core import WDApiError
from tqdm import tqdm

import config
from WDHelper import WDHelper
from local import WDUSER, WDPASS

biothings.config_for_app(config)
from biothings.utils.mongo import get_src_dump, get_src_db
from bot_log_parser import parse_exc, parse_info

console = logging.StreamHandler()
console.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
info_logger = logging.getLogger('info_logger')
info_logger.setLevel(logging.INFO)
info_logger.addHandler(console)

exc_formatter = logging.Formatter('>%(asctime)s %(levelname)s %(message)s')
exc_logger = logging.getLogger('exc_logger')
exc_logger.addHandler(console)


class MondoBot:
    DOID_PROP = "P699"
    UMLS_PROP = "P2892"
    MONDO_WDID = "Q27468140"
    DOID2WD = WDHelper().id_mapper(DOID_PROP)

    def __init__(self, log_dir=None, date=None, dry_run=False):
        self.log_dir = log_dir if log_dir else os.getcwd()
        d = datetime.now()
        self.date = date if date else "".join(map(str, [d.year, d.month, d.day]))
        self.dry_run = dry_run
        self.login_instance = PBB_login.WDLogin(user=WDUSER, pwd=WDPASS)
        self.fast_run_base_filter = {self.DOID_PROP: ''}
        self.info_log_path = None
        self.exc_log_path = None
        self.reference = None
        self.setup_logging()
        self.collection = get_src_db().mondo
        src_dump = get_src_dump()
        src_doc = src_dump.find_one({'_id': 'mondo'}) or {}
        self.retrieved = src_doc.get("download", {}).get("started_at", False) or datetime.now()
        self.ref_url = "https://github.com/monarch-initiative/monarch-disease-ontology/raw/{}/src/mondo/mondo.obo".format(
            src_doc.get("release", "master"))
        self.create_reference()

    def setup_logging(self):
        self.info_log_path = os.path.join(self.log_dir, 'mondo_{}_wikidata_info.log'.format(self.date))
        info_handler = logging.FileHandler(self.info_log_path)
        info_handler.setFormatter(formatter)
        info_logger.addHandler(info_handler)

        self.exc_log_path = os.path.join(self.log_dir, 'mondo_{}_wikidata_exc.log'.format(self.date))
        exc_handler = logging.FileHandler(self.exc_log_path)
        exc_handler.setFormatter(exc_formatter)
        exc_logger.addHandler(exc_handler)

    def create_reference(self):
        ref_stated_in = PBB_Core.WDItemID(self.MONDO_WDID, 'P248', is_reference=True)
        ref_retrieved = PBB_Core.WDTime(self.retrieved.strftime('+%Y-%m-%dT00:00:00Z'), 'P813',
                                        is_reference=True)  # interpro ID
        #ref_archive_url = PBB_Core.WDUrl(self.ref_url, 'P1065', is_reference=True)
        #reference = [ref_stated_in, ref_retrieved, ref_archive_url]
        reference = [ref_stated_in, ref_retrieved]
        self.reference = reference

    def do_umls_statement(self, doid, umls_list, dry_run=False):
        statements = []
        for umls in umls_list:
            statements.append(PBB_Core.WDExternalID(value=umls, prop_nr=self.UMLS_PROP, references=[self.reference]))

        wd_item = PBB_Core.WDItemEngine(wd_item_id=self.DOID2WD[doid], domain='disease', data=statements,
                                        append_value=[self.UMLS_PROP], fast_run=True,
                                        fast_run_base_filter=self.fast_run_base_filter)

        # no item creation should be done
        if wd_item.create_new_item:
            raise ValueError("something bad happpened")

        if dry_run:
            if wd_item.require_write:
                info_logger.info(" ".join(["item_updated", doid, wd_item.wd_item_id]))

        if wd_item.require_write and not dry_run:
            self.try_write(wd_item, doid)

    def try_write(self, wd_item, doid):
        try:
            wd_item.write(self.login_instance)
        except WDApiError as e:
            exc_logger.exception(" ".join(["wdapierror", doid, wd_item.wd_item_id]) + "\n" + str(e))
        info_logger.info(" ".join(["item_updated", doid, wd_item.wd_item_id]))

    def run(self, dry_run=False, cheat=False):
        info_logger.info("run_start xxx xxx")
        cursor = self.collection.find(no_cursor_timeout=True)
        for n, doc in tqdm(enumerate(cursor), total=cursor.count(), miniters=100):
            if cheat and n % 100 != 0:
                continue
            doid = doc['_id']
            umls_list = [x[5:] for x in doc['equivalent_class'] if x.startswith("UMLS:")]
            if not umls_list:
                continue
            if doid not in self.DOID2WD:
                exc_logger.exception(" ".join(["doid_not_found", doid, "QXXXXX"]))
                continue
            self.do_umls_statement(doid, umls_list, dry_run=dry_run)
        cursor.close()

    def generate_report(self):
        item_updated, item_created = parse_info(self.info_log_path)
        df = parse_exc(self.exc_log_path)

        print("Number of items updated: {}".format(item_updated))
        print("Number of items created: {}".format(item_created))

        print("Errors: ")
        print(df)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='run doid - umls wikidata import bot')
    parser.add_argument('--dry-run', action='store_true',
                        help="don't actually do wikidata write. Keep logs as if write is happening")
    parser.add_argument('--log_dir', help='directory to store logs', type=str)
    parser.add_argument('--date', help='log date', type=str)
    parser.add_argument('--cheat', help='only run every hundredth doc', action='store_true')
    args = parser.parse_args()

    bot = MondoBot(log_dir=args.log_dir, date=args.date)
    bot.run(dry_run=args.dry_run, cheat=args.cheat)
    bot.generate_report()

    """
    {
        "_id" : "DOID:0050867",
        "equivalent_class" : [
            "OMIM:311150",
            "UMLS:C1839564",
            "MESH:C537568"
        ]
    }
    """