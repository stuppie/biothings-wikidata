from .parser import parse_protein_ipr, parse_interpro_xml
import biothings.dataload.uploader as uploader


class InterproProteinUploader(uploader.BaseSourceUploader):

    name = "interpro_protein"
    main_source = "interpro"

    def load_data(self, data_folder):
        ipr_items = parse_interpro_xml(data_folder)
        ipr_items = {x['_id']: x for x in ipr_items}
        return parse_protein_ipr(data_folder, ipr_items)

    def get_mapping(self):
        return {}