import biothings.dataload.uploader as uploader
import requests

"""
Saccharomyces cerevisiae S288c: 559292
"""


def mygeneinfo_query(taxid):
    # Downloads the latest list of genes by taxid
    url = 'http://mygene.info/v2/query/'
    params = dict(q="__all__", species=taxid, entrezonly="true", size="100000", fields="all")
    data = requests.get(url=url, params=params).json()

    for x in data['hits']:
        yield x


class YeastUploader(uploader.BaseSourceUploader):

    tax_id = 559292

    name = "yeast"
    main_source = "mygene"

    def load_data(self, data_folder):
        return mygeneinfo_query(self.tax_id)

    @classmethod
    def get_mapping(cls):
        return {}

