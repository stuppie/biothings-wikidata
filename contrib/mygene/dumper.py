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