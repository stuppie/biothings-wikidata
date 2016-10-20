import argparse
import os
import os.path

import biothings
import requests
from biothings.dataload.dumper import HTTPDumper
from bs4 import BeautifulSoup

import config
from config import DATA_ARCHIVE_ROOT

biothings.config_for_app(config)


def get_new_hash():
    page_url = "https://github.com/monarch-initiative/monarch-disease-ontology/blob/master/src/mondo/mondo.owl"
    res = requests.get(page_url)
    html = BeautifulSoup(res.text, "html.parser")
    return html.find(attrs={'class': 'commit-tease-sha'}).attrs['href'].split("/")[-1].strip()

# https://github.com/monarch-initiative/monarch-disease-ontology/raw/00fcf66cd2f7100d7ff69a6f0da3ee61efc43e63/src/mondo/mondo.owl

class MondoDumper(HTTPDumper):
    SRC_NAME = "mondo"
    SRC_ROOT_FOLDER = DATA_ARCHIVE_ROOT
    REMOTE_PATH = "https://github.com/monarch-initiative/monarch-disease-ontology/raw/master/src/mondo/mondo.owl"
    FILE = "mondo.owl"

    def __init__(self, src_name=None, src_root_folder=None, no_confirm=True, archive=True):
        super().__init__(src_name, src_root_folder, no_confirm, archive)
        self.new_hash = get_new_hash()
        self.release = self.src_doc.get("release", "")

    def create_todump_list(self, force=False):
        self.to_dump = []
        new_localfile = os.path.join(self.new_data_folder, self.SRC_NAME, self.FILE)
        current_localfile = os.path.join(self.current_data_folder, self.SRC_NAME,
                                         self.FILE) if self.current_data_folder else new_localfile
        if force or not os.path.exists(current_localfile) or (self.new_hash != self.release):
            self.release = self.new_hash
            self.to_dump.append({"remote": self.REMOTE_PATH, "local": new_localfile})
        else:
            print("Skipping: {}".format(current_localfile))


def main(force=False):
    dumper = MondoDumper()
    dumper.dump(force=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='run mondo dumper')
    parser.add_argument('--force', action='store_true', help='force new download')
    args = parser.parse_args()
    main(force=args.force)
