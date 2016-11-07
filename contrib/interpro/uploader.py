import biothings.dataload.uploader as uploader

from .parser import parse_interpro_xml, release_info, parse_protein_ipr

"""
class InterproUploader(uploader.BaseSourceUploader):
    name = "interpro"
    main_source = "interpro"

    def load_data(self, data_folder):
        return parse_interpro_xml(data_folder)

    @classmethod
    def get_mapping(cls):
        return {}

"""
class InterproDbinfoUploader(uploader.BaseSourceUploader):
    name = "dbinfo"
    main_source = "interpro"

    def load_data(self, data_folder):
        return release_info(data_folder)

    @classmethod
    def get_mapping(cls):
        return {}

"""
class InterproProteinUploader(uploader.BaseSourceUploader):
    name = "interpro_protein"
    main_source = "interpro"

    def load_data(self, data_folder):
        ipr_items = parse_interpro_xml(data_folder)
        ipr_items = {x['_id']: x for x in ipr_items}
        return parse_protein_ipr(data_folder, ipr_items)

    @classmethod
    def get_mapping(cls):
        return {}
"""