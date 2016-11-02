"""


# sparql query to track progress
http://tinyurl.com/hdr3jnl
"""

import argparse
import json
from datetime import datetime

from ProteinBoxBot_Core import PBB_Core, PBB_login, PBB_Helpers
from pymongo import MongoClient
from tqdm import tqdm

from local import WDUSER, WDPASS

__metadata__ = {'name': 'InterproBot',
                'maintainer': 'GSS',
                'tags': ['protein', 'interpro'],
                'properties': None
                }

interpro_version2wdid = {"59.0": "Q27135875"}  # TODO:
UNIPROT = "P352"
INTERPRO = "P2926"

# need to change
# data sources
db = MongoClient().wikidata_src
IPR_COLL = db.interpro
UNIPROT_COLL = db.interpro_protein
DBINFO_COLL = db.dbinfo


class IPRTerm:
    """
    Represents one interproscan term/item

    {'children': ['IPR020635'],
     'contains': ['IPR001824', 'IPR002011', 'IPR008266', 'IPR017441'],
     'description': 'InterPro Domain',
     'found_in': ['IPR009136','IPR012234','IPR020777'],
     'id': 'IPR001245',
     'name': 'Serine-threonine/tyrosine-protein kinase catalytic domain',
     'parent': 'IPR000719',
     'short_name': 'Ser-Thr/Tyr_kinase_cat_dom',
     'type': 'Domain',
     'type_wdid': 'Q898273'}

    """

    fast_run_base_filter = {INTERPRO: ''}
    ipr2wd = PBB_Helpers.id_mapper(INTERPRO)

    type2desc = {"Active_site": "InterPro Active Site",
                 "Binding_site": "InterPro Binding Site",
                 "Conserved_site": "InterPro Conserved Site",
                 "Domain": "InterPro Domain",
                 "Family": "InterPro Family",
                 "PTM": "InterPro PTM",
                 "Repeat": "InterPro Repeat"}
    type2wdid = {"Active_site": "Q423026",  # Active site
                 "Binding_site": "Q616005",  # Binding site
                 "Conserved_site": "Q7644128",  # Supersecondary_structure
                 "Domain": "Q898273",  # Protein domain
                 "Family": "Q417841",  # Protein family
                 "PTM": "Q898362",  # Post-translational modification
                 "Repeat": "Q3273544"}  # Structural motif

    def __init__(self, name=None, short_name=None, id=None, parent=None, children=None, contains=None,
                 found_in=None, type=None, description=None, interpro_version=None, **kwargs):
        self.name = name
        self.short_name = short_name
        self.id = id
        self.wdid = None
        self.parent = parent  # subclass of (P279)
        self.parent_wdid = None
        self.children = children  # not added to wd
        self.children_wdid = None
        self.contains = contains  # has part (P527)
        self.contains_wdid = None
        self.found_in = found_in  # part of (P361)
        self.found_in_wdid = None
        self.type = type
        self.type_wdid = IPRTerm.type2wdid[self.type]  # subclass of (from type2wdid)
        self.description = description
        if self.description is None and self.type:
            self.description = IPRTerm.type2desc[self.type]
        self.lang_descr = {'en': self.description}
        self.reference = None
        self.interpro_version = None
        self.interpro_version_wdid = None

        self.set_interpro_version(interpro_version)

        # self.do_wdid_lookup()
        self.create_reference()

    def __repr__(self):
        return '{}: {}'.format(self.id, self.name)

    def __str__(self):
        return '{}: {}'.format(self.id, self.name)

    @classmethod
    def refresh_ipr_wd(cls):
        cls.ipr2wd = PBB_Helpers.id_mapper(INTERPRO)

    def set_interpro_version(self, interpro_version):
        self.interpro_version = interpro_version
        if self.interpro_version not in interpro_version2wdid:
            raise ValueError("Must create new Interpro version wikidata item")
        self.interpro_version_wdid = interpro_version2wdid[self.interpro_version]

    def do_wdid_lookup(self):
        # this can only be done after all items have been created
        self.wdid = IPRTerm.ipr2wd[self.id]
        if self.parent:
            self.parent_wdid = IPRTerm.ipr2wd[self.parent]
        # children aren't added (reverse of parent relationship)
        if self.contains:
            self.contains_wdid = [IPRTerm.ipr2wd[x] for x in self.contains]
        if self.found_in:
            self.found_in_wdid = [IPRTerm.ipr2wd[x] for x in self.found_in]

    def create_reference(self):
        """ Create wikidata references for interpro
        This same reference will be used for everything. Except for a ref to the interpro item itself
        """
        # stated in Interpro version XX.X
        ref_stated_in = PBB_Core.WDItemID(self.interpro_version_wdid, 'P248', is_reference=True)
        ref_ipr = PBB_Core.WDString(self.id, INTERPRO, is_reference=True)  # interpro ID
        self.reference = [ref_stated_in, ref_ipr]

    def create_item(self, login):
        statements = [PBB_Core.WDExternalID(value=self.id, prop_nr=INTERPRO, references=[self.reference]),
                      PBB_Core.WDItemID(value=self.type_wdid, prop_nr="P279",
                                        references=[self.reference])]

        wd_item = PBB_Core.WDItemEngine(item_name=self.name, domain='interpro', data=statements,
                                        append_value=["P279"],
                                        fast_run=True, fast_run_base_filter=IPRTerm.fast_run_base_filter)
        wd_item.set_label(self.name, lang='en')
        for lang, description in self.lang_descr.items():
            wd_item.set_description(description, lang=lang)
        wd_item.set_aliases([self.short_name, self.id])

        PBB_Helpers.try_write(wd_item, self.id, INTERPRO, login)

        return wd_item

    def create_relationships(self, login):
        self.do_wdid_lookup()

        statements = [PBB_Core.WDExternalID(value=self.id, prop_nr=INTERPRO, references=[self.reference])]
        if self.parent:
            # subclass of
            statements.append(PBB_Core.WDItemID(value=self.parent_wdid, prop_nr='P279', references=[self.reference]))
        if self.contains:
            for c in self.contains_wdid:
                statements.append(PBB_Core.WDItemID(value=c, prop_nr='P527', references=[self.reference]))  # has part
        if self.found_in:
            for f in self.found_in_wdid:
                statements.append(PBB_Core.WDItemID(value=f, prop_nr='P361', references=[self.reference]))  # part of
        if len(statements) == 1:
            return

        wd_item = PBB_Core.WDItemEngine(item_name=self.name, domain='interpro', data=statements,
                                        append_value=['P279', 'P527', 'P361'],
                                        fast_run=True, fast_run_base_filter=IPRTerm.fast_run_base_filter)

        PBB_Helpers.try_write(wd_item, self.id, INTERPRO, login)


def create_interpro_items(login, interpro_version):
    # insert all interpro items
    cursor = IPR_COLL.find(no_cursor_timeout=True)
    for n, doc in tqdm(enumerate(cursor), total=cursor.count()):
        term = IPRTerm(**doc, interpro_version=interpro_version)
        term.create_item(login)
    cursor.close()


def create_ipr_relationships(login, interpro_version):
    terms = []
    for doc in IPR_COLL.find():
        term = IPRTerm(**doc, interpro_version=interpro_version)
        terms.append(term)
    IPRTerm.refresh_ipr_wd()
    for term in tqdm(terms):
        term.create_relationships(login)


def create_uniprot_relationships(login, interpro_version, taxon=None):
    # only do uniprot proteins that are already in wikidata
    if taxon:
        uniprot2wd = PBB_Helpers.id_mapper(UNIPROT, (("P703", taxon),))
        fast_run_base_filter = {UNIPROT: "", "P703": taxon}
    else:
        uniprot2wd = PBB_Helpers.id_mapper(UNIPROT)
        fast_run_base_filter = {UNIPROT: ""}

    cursor = UNIPROT_COLL.find({'_id': {'$in': list(uniprot2wd.keys())}}, no_cursor_timeout=True)
    for doc in tqdm(cursor, total=cursor.count()):
        uniprot_id = doc['_id']
        statements = []
        # uniprot ID. needed for PBB_core to find uniprot item
        # statements.append(PBB_Core.WDExternalID(value=uniprot_id, prop_nr=UNIPROT))

        ## References
        # stated in Interpro version XX.X
        ref_stated_in = PBB_Core.WDItemID(interpro_version2wdid[interpro_version], 'P248', is_reference=True)
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
            PBB_Core.WDItemEngine.log("ERROR",
                                      PBB_Helpers.format_msg(uniprot_id, "wdid_not_found", None, UNIPROT))

        wd_item = PBB_Core.WDItemEngine(wd_item_id=uniprot2wd[uniprot_id], domain="proteins", data=statements,
                                        fast_run=True, fast_run_base_filter=fast_run_base_filter,
                                        append_value=["P279", "P527", "P361"])

        if wd_item.create_new_item:
            raise ValueError("something bad happened")
        PBB_Helpers.try_write(wd_item, uniprot_id, INTERPRO, login, edit_summary="add/update family and/or domains")

    cursor.close()


def get_interpro_version():
    return DBINFO_COLL.find_one("INTERPRO")['version']


def main(log_dir="./logs", run_id=None, items=True, rel=True, uniprot=True, taxon=None):
    if run_id is None:
        run_id = datetime.now().strftime('%Y%m%d_%H:%M')
    if log_dir is None:
        log_dir = "./logs"
    __metadata__['run_id'] = run_id
    __metadata__['timestamp'] = str(datetime.now())

    interpro_version = get_interpro_version()
    __metadata__['release'] = {'InterPro': interpro_version}

    login = PBB_login.WDLogin(user=WDUSER, pwd=WDPASS)

    if items:
        __metadata__['name'] = 'InterproBot_Items'
        __metadata__['properties'] = ["P279", "P2926"]
        log_name = '{}-{}.log'.format(__metadata__['name'], run_id)
        if PBB_Core.WDItemEngine.logger is not None:
            PBB_Core.WDItemEngine.logger.handles = []
        PBB_Core.WDItemEngine.setup_logging(log_dir=log_dir, log_name=log_name, header=json.dumps(__metadata__))
        create_interpro_items(login, interpro_version)
    if rel:
        __metadata__['name'] = 'InterproBot_ItemRel'
        __metadata__['properties'] = ["P279", "P527", "P361"]
        log_name = '{}-{}.log'.format(__metadata__['name'], run_id)
        if PBB_Core.WDItemEngine.logger is not None:
            PBB_Core.WDItemEngine.logger.handles = []
        PBB_Core.WDItemEngine.setup_logging(log_dir=log_dir, log_name=log_name, header=json.dumps(__metadata__))
        create_ipr_relationships(login, interpro_version)
    if uniprot:
        __metadata__['name'] = 'InterproBot_Proteins'
        __metadata__['properties'] = ["P279", "P527", "P361"]
        log_name = '{}-{}.log'.format(__metadata__['name'], run_id)
        if PBB_Core.WDItemEngine.logger is not None:
            PBB_Core.WDItemEngine.logger.handles = []
        PBB_Core.WDItemEngine.setup_logging(log_dir=log_dir, log_name=log_name, header=json.dumps(__metadata__))
        create_uniprot_relationships(login, interpro_version, taxon)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='run interpro wikidata import bot. If no options given, run all 3')
    parser.add_argument('--items', action='store_true', help='create/update interpro items')
    parser.add_argument('--rel', action='store_true', help='add inter-interpro relationships')
    parser.add_argument('--uniprot', action='store_true', help='add uniprot/protein to interpro relationships')
    parser.add_argument('--log-dir', help='directory to store logs', type=str)
    parser.add_argument('--run-id', help='run_id', type=str)
    parser.add_argument('--taxon', help='limit protein<->interpro to taxon', type=str)

    args = parser.parse_args()

    if not (args.items or args.rel or args.uniprot):
        args.items = args.rel = args.uniprot = True

    main(args.log_dir, args.run_id, items=args.items, rel=args.rel, uniprot=args.uniprot, taxon=args.taxon)
