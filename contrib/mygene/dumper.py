import biothings
import requests
from biothings.dataload.dumper import BaseDumper
from dateutil import parser

import config
from config import DATA_ARCHIVE_ROOT

biothings.config_for_app(config)


class MyGeneDumper(BaseDumper):
    SRC_NAME = "mygene"
    SRC_ROOT_FOLDER = DATA_ARCHIVE_ROOT

    def __init__(self, src_name=None, src_root_folder=None, no_confirm=True, archive=True):
        super().__init__(src_name, src_root_folder, no_confirm, archive)
        print(self.src_doc)
        self.current_timestamp = self.src_doc["release"] if self.src_doc.get('release', False) else None
        print(self.current_timestamp)
        self.new_timestamp = None

    def prepare_client(self):
        pass

    def dump(self, force=False):
        if force or self.remote_is_newer():
            self.release = self.new_timestamp
            self.logger.info("remote ({}) is newer than current ({})".format(self.new_timestamp, self.current_timestamp))
            self.post_dump()
            self.logger.info("Registering success")
            self.register_status("success", pending_to_upload=True)
        else:
            self.logger.info("remote ({}) is not newer than current ({})".format(self.new_timestamp, self.current_timestamp))

    def remote_is_newer(self):
        mygene_metadata = requests.get("http://mygene.info/v3/metadata").json()
        self.new_timestamp = parser.parse(mygene_metadata['timestamp'])
        if self.current_timestamp is None or self.new_timestamp > self.current_timestamp:
            return True


def main():
    dumper = MyGeneDumper()
    dumper.dump()


if __name__ == "__main__":
    main()



"""
{'SGD': 'S000003787',
 '_id': '853483',
 'accession': {'genomic': ['BK006943', 'BK006945', 'BK006946', 'NC_001142'],
  'protein': ['DAA08816',   'DAA09545',   'DAA09860',   'NP_012561',   'P0CX74',   'P0CX75',   'P0CX76'],
  'rna': 'NM_001181684'},
 'ensembl': [{'gene': 'YJR026W',
   'protein': 'YJR026W',
   'transcript': 'YJR026W'},
  {'gene': 'YLR227W-A', 'protein': 'YLR227W-A', 'transcript': 'YLR227W-A'},
  {'gene': 'YML040W', 'protein': 'YML040W', 'transcript': 'YML040W'}],
 'entrezgene': 853483,
 'genomic_pos': [{'chr': 'X', 'end': 474082, 'start': 472760, 'strand': 1},
  {'chr': 'XII', 'end': 594760, 'start': 593438, 'strand': 1},
  {'chr': 'XIII', 'end': 197950, 'start': 196628, 'strand': 1}],
 'go': {'BP': {'evidence': 'ISS',
   'id': 'GO:0032197',
   'pubmed': 9582191,
   'term': 'transposition, RNA-mediated'},
  'CC': [{'evidence': 'ISS',
    'id': 'GO:0000943',
    'pubmed': 9582191,
    'term': 'retrotransposon nucleocapsid'},
   {'evidence': 'IEA', 'id': 'GO:0005737', 'term': 'cytoplasm'}],
  'MF': [{'evidence': 'IEA', 'id': 'GO:0003723', 'term': 'RNA binding'},
   {'evidence': 'ISS',
    'id': 'GO:0003723',
    'pubmed': 9582191,
    'term': 'RNA binding'}]},
 'homologene': {'genes': [[4932, 850339],
   [4932, 850340],
   [4932, 856907]],
  'id': 68560},
 'interpro': {'desc': 'Retrotransposon Ty1 A, N-terminal',
  'id': 'IPR015820',
  'short_desc': 'Retrotransposon_Ty1A_N'},
 'locus_tag': 'YJR026W',
 'name': 'gag protein',
 'pfam': 'PF01021',
 'pir': 'S57044',
 'refseq': {'genomic': 'NC_001142',
  'protein': 'NP_012561',
  'rna': 'NM_001181684'},
 'symbol': 'YJR026W',
 'taxid': 559292,
 'type_of_gene': 'protein-coding',
 'uniprot': {'Swiss-Prot': ['P0CX74', 'P0CX75', 'P0CX76']}}
 """
