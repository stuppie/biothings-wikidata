import argparse
import os
import os.path

import biothings
from biothings.dataload.dumper import FTPDumper

import config
from config import DATA_ARCHIVE_ROOT

biothings.config_for_app(config)


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False



class InterproDumper(FTPDumper):
    SRC_NAME = "interpro"
    FTP_HOST = 'ftp.ebi.ac.uk'
    CWD_DIR = 'pub/databases/interpro/current'
    SRC_ROOT_FOLDER = os.path.join(DATA_ARCHIVE_ROOT, SRC_NAME)
    FILES = ["interpro.xml.gz", "protein2ipr.dat.gz"]

    SCHEDULE = "* 0 * * *"

    def get_newest_info(self):
        release_folder = self.client.pwd()
        self.release = os.path.split(release_folder)[-1]

    def new_release_available(self):
        current_release = self.src_doc.get("release")
        if not current_release or float(self.release) > float(current_release):
            self.logger.info("New release '%s' found" % self.release)
            return True
        else:
            self.logger.debug("No new release found")
            return False

    def create_todump_list(self, force=False):
        self.get_newest_info()
        self.to_dump = []
        for file in self.FILES:
            new_localfile = os.path.join(self.new_data_folder, file)
            current_localfile = os.path.join(self.current_data_folder, file) if self.current_data_folder else new_localfile
            if force or not os.path.exists(current_localfile) or self.new_release_available():
                self.to_dump.append({"remote": file, "local": new_localfile})
            else:
                print("Skipping: {}".format(current_localfile))
        print(self.to_dump)


def main(force=False):
    dumper = InterproDumper()
    dumper.dump(force=False)
    dumper.create_todump_list()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='run interpro dumper')
    parser.add_argument('--force', action='store_true', help='force new download')
    args = parser.parse_args()
    main(force=args.force)
