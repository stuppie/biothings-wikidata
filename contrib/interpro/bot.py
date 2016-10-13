"""


# sparql query to track progress
http://tinyurl.com/hdr3jnl
"""


import argparse
import logging

from ProteinBoxBot_Core import PBB_Core, PBB_login
from ProteinBoxBot_Core.PBB_Core import WDApiError
from interproscan.WDHelper import WDHelper
from interproscan.local import WDUSER, WDPASS
from pymongo import MongoClient
from tqdm import tqdm

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
info_logger = logging.getLogger('info_logger')
info_logger.setLevel(logging.INFO)
info_handler = logging.FileHandler('info_logger.log')
info_handler.setFormatter(formatter)
info_logger.addHandler(info_handler)

exc_logger = logging.getLogger('exc_logger')
exc_handler = logging.FileHandler('exc_logger.log')
exc_handler.setFormatter(formatter)
exc_logger.addHandler(exc_handler)

interpro_version2wdid = {"59.0": "Q27135875"}  # make by hand, for now
UNIPROT = "P352"

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
    INTERPRO = "P2926"
    fast_run_base_filter = {INTERPRO: ''}
    ipr2wd = WDHelper().id_mapper(INTERPRO)
    login_instance = PBB_login.WDLogin(user=WDUSER, pwd=WDPASS)

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
        self.interpro_version = interpro_version
        if self.interpro_version not in interpro_version2wdid:
            raise ValueError("Must create new Interpro version wikidata item")
        self.interpro_version_wdid = interpro_version2wdid[self.interpro_version]
        self.reference = None

        # self.do_wdid_lookup()
        self.create_reference()

    def __repr__(self):
        return '{}: {}'.format(self.id, self.name)

    def __str__(self):
        return '{}: {}'.format(self.id, self.name)

    @classmethod
    def refresh_ipr_wd(cls):
        cls.ipr2wd = WDHelper().id_mapper(cls.INTERPRO)

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
        ref_stated_in = PBB_Core.WDItemID(self.interpro_version_wdid, 'P248',
                                          is_reference=True)  # stated in Interpro version XX.X
        ref_ipr = PBB_Core.WDString(self.id, IPRTerm.INTERPRO, is_reference=True)  # interpro ID
        self.reference = [ref_stated_in, ref_ipr]

    def create_item(self, perform_write=True):
        statements = [PBB_Core.WDExternalID(value=self.id, prop_nr=IPRTerm.INTERPRO, references=[self.reference]),
                      PBB_Core.WDItemID(value=self.type_wdid, prop_nr="P279", references=[self.reference])]

        wd_item = PBB_Core.WDItemEngine(item_name=self.name, domain='interpro', data=statements, append_value=['P279'],
                                        fast_run=True, fast_run_base_filter=IPRTerm.fast_run_base_filter)
        wd_item.set_label(self.name, lang='en')
        for lang, description in self.lang_descr.items():
            wd_item.set_description(description, lang=lang)
        wd_item.set_aliases([self.short_name, self.id])

        if wd_item.require_write and perform_write:
            self.try_write(wd_item)

        return wd_item

    def try_write(self, wd_item):
        create_new_item = wd_item.create_new_item
        try:
            wd_item.write(IPRTerm.login_instance)
        except WDApiError as e:
            exc_logger.exception("wdapierror " + self.id + " " + wd_item.wd_item_id)
            # raise e
        if create_new_item:
            info_logger.info("item_created " + self.id + " " + wd_item.wd_item_id)
        else:
            info_logger.info("item_updated " + self.id + " " + wd_item.wd_item_id)

    def create_relationships(self):
        self.do_wdid_lookup()

        statements = [PBB_Core.WDExternalID(value=self.id, prop_nr=IPRTerm.INTERPRO, references=[self.reference])]
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
        if wd_item.require_write:
            self.try_write(wd_item)


def create_interpro_items():
    ## insert all interpro items
    coll = IPR_COLL
    ipr_version = DBINFO_COLL.find_one("INTERPRO")['version']
    cursor = coll.find(no_cursor_timeout=True)
    for n, doc in tqdm(enumerate(cursor), total=cursor.count()):
        term = IPRTerm(**doc, interpro_version=ipr_version)
        term.create_item()
    cursor.close()


def create_ipr_relationships():
    coll = IPR_COLL
    ipr_version = DBINFO_COLL.find_one("INTERPRO")['version']
    terms = []
    for doc in coll.find():
        term = IPRTerm(**doc, interpro_version=ipr_version)
        terms.append(term)
    IPRTerm.refresh_ipr_wd()
    for term in tqdm(terms):
        term.create_relationships()


def create_uniprot_relationships():
    wc = 0
    coll = UNIPROT_COLL
    # only do uniprot proteins that are already in wikidata
    uniprot2wd = WDHelper().id_mapper(UNIPROT)
    cursor = coll.find({'_id': {'$in': list(uniprot2wd.keys())}}, no_cursor_timeout=True)
    for n, doc in tqdm(enumerate(cursor), total=cursor.count()):
        uniprot_id = doc['_id']
        ipr_version = DBINFO_COLL.find_one("INTERPRO")['version']
        statements = []
        # uniprot ID. needed for PBB_core to find uniprot item
        # statements.append(PBB_Core.WDExternalID(value=uniprot_id, prop_nr=UNIPROT))

        ## References
        # stated in Interpro version XX.X
        ref_stated_in = PBB_Core.WDItemID(interpro_version2wdid[ipr_version], 'P248', is_reference=True)
        ref_ipr = PBB_Core.WDString("http://www.ebi.ac.uk/interpro/protein/{}".format(uniprot_id), "P854",
                                    is_reference=True)
        reference = [ref_stated_in, ref_ipr]

        if doc['subclass']:
            for f in doc['subclass']:
                statements.append(PBB_Core.WDItemID(value=IPRTerm.ipr2wd[f], prop_nr='P279', references=[reference]))
        if doc['has_part']:
            for hp in doc['has_part']:
                statements.append(PBB_Core.WDItemID(value=IPRTerm.ipr2wd[hp], prop_nr='P527', references=[reference]))

        try:
            wd_item = PBB_Core.WDItemEngine(wd_item_id=uniprot2wd[uniprot_id], domain="proteins", data=statements,
                                            fast_run=True, fast_run_base_filter={UNIPROT: ""},
                                            append_value=["P279", "P527", "P361"])
        except KeyError as e:
            exc_logger.exception("wdid_not_found " + uniprot_id + " " + uniprot2wd[uniprot_id])
            print("wdid_not_found " + uniprot_id + " " + uniprot2wd[uniprot_id])
            continue

        if wd_item.require_write:
            wc += 1
            create_new_item = wd_item.create_new_item
            if create_new_item:
                raise ValueError("something bad happened")
            try:
                wd_item.write(IPRTerm.login_instance, edit_summary="add/update family and/or domains")
            except Exception as e:
                exc_logger.exception("write_error " + uniprot_id + " " + wd_item.wd_item_id + "\n" + str(e))
                continue
                # raise e
            if create_new_item:
                info_logger.info("item_created " + uniprot_id + " " + wd_item.wd_item_id)
            else:
                info_logger.info("item_updated " + uniprot_id + " " + wd_item.wd_item_id)
                print("item_updated " + uniprot_id + " " + wd_item.wd_item_id)
    cursor.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='run interpro wikidata import bot. If no options given, run all 3')
    parser.add_argument('--items', action='store_true', help='create/update interpro items')
    parser.add_argument('--rel', action='store_true', help='add inter-interpro relationships')
    parser.add_argument('--uniprot', action='store_true', help='add uniprot/protein to interpro relationships')
    args = parser.parse_args()

    if args.items:
        create_interpro_items()
    if args.rel:
        create_ipr_relationships()
    if args.uniprot:
        create_uniprot_relationships()

    if not (args.items or args.rel or args.uniprot):
        create_interpro_items()
        create_ipr_relationships()
        create_uniprot_relationships()
