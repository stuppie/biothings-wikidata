import argparse
import os
import os.path

import biothings
from biothings.dataload.dumper import FTPDumper

import config
from config import DATA_ARCHIVE_ROOT

biothings.config_for_app(config)


class InterproDumper(FTPDumper):
    SRC_NAME = "interpro"
    FTP_HOST = 'ftp.ebi.ac.uk'
    CWD_DIR = 'pub/databases/interpro/'
    SRC_ROOT_FOLDER = DATA_ARCHIVE_ROOT
    FILES = ["interpro.xml.gz", "protein2ipr.dat.gz"]

    def create_todump_list(self, force=False):
        self.to_dump = []
        for file in self.FILES:
            new_localfile = os.path.join(self.new_data_folder, self.CWD_DIR, file)
            current_localfile = os.path.join(self.current_data_folder, self.CWD_DIR,
                                             file) if self.current_data_folder else new_localfile
            if force or not os.path.exists(current_localfile) or self.remote_is_better(file, current_localfile):
                self.release = self.timestamp
                self.to_dump.append({"remote": file, "local": new_localfile})
            else:
                print("Skipping: {}".format(current_localfile))


def main(force=False):
    dumper = InterproDumper()
    dumper.dump(force=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='run interpro dumper')
    parser.add_argument('--force', action='store_true', help='force new download')
    args = parser.parse_args()
    main(force=args.force)
