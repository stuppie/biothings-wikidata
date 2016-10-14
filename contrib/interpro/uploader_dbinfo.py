from .parser import release_info
import biothings.dataload.uploader as uploader


class InterproDbinfoUploader(uploader.BaseSourceUploader):

    name = "dbinfo"
    main_source = "interpro"

    def load_data(self, data_folder):
        info = release_info(data_folder)
        for x in info:
            yield x

    @classmethod
    def get_mapping(self):
        return {}