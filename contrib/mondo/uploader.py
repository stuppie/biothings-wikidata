import os

import biothings.dataload.uploader as uploader

from .query_owl import parse


class MondoUploader(uploader.BaseSourceUploader):
    name = "mondo"
    main_source = "mondo"

    def load_data(self, data_folder):
        return parse(os.path.join(data_folder, self.name, "mondo.owl"))

    @classmethod
    def get_mapping(self):
        return {}
