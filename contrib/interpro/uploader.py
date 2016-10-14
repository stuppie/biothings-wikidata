from .parser import parse_interpro_xml
import biothings.dataload.uploader as uploader


class InterproUploader(uploader.BaseSourceUploader):

    name = "interpro"
    main_source = "interpro"

    def load_data(self, data_folder):
        return parse_interpro_xml(data_folder)

    @classmethod
    def get_mapping(self):
        return {}