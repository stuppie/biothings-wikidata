import os
import os.path
import time
from datetime import datetime
from ftplib import error_perm

import biothings
import config
from biothings.dataload.dumper import FTPDumper

from config import DATA_ARCHIVE_ROOT

biothings.config_for_app(config)


class InterproDumper(FTPDumper):
    SRC_NAME = "interpro"
    FTP_HOST = 'ftp.ebi.ac.uk'
    CWD_DIR = 'pub/databases/interpro/'
    SRC_ROOT_FOLDER = DATA_ARCHIVE_ROOT

    def get_file_list(self):
        fli = []
        files = ["interpro.xml.gz", "protein2ipr.dat.gz"]
        for file_path in files:
            lastmodified = self.get_ftpfile_lastmodified(file_path)
            if lastmodified:
                fli.append((file_path, lastmodified))
            else:
                pass
        return fli

    def get_ftpfile_lastmodified(self, file_path):
        """return lastmodified for a given file on ftp server."""
        try:
            response = self.client.sendcmd('MDTM ' + file_path)
        except error_perm as e:
            self.logger.debug("Skip %s: %s" % (file_path, e))
            return None
        code, lastmodified = response.split()
        # 'last-modified': '20121128150000'
        lastmodified = int(time.mktime(datetime.strptime(lastmodified, '%Y%m%d%H%M%S').timetuple()))
        return lastmodified

    def remote_is_better(self, remote_info, localfile):
        remotefile, remote_lastmodified = remote_info
        local_lastmodified = int(os.stat(localfile).st_mtime)
        if remote_lastmodified > local_lastmodified:
            self.logger.debug("Remote file '%s' is newer (remote: %s, local: %s)" %
                              (remotefile, remote_lastmodified, local_lastmodified))
            return True
        else:
            self.logger.debug("'%s' is up-to-date, no need to download" % remotefile)
            return False

    def create_todump_list(self, force=False):
        self.to_dump = []
        remote_files = self.get_file_list()
        for remote_file, remote_lastmodified in remote_files:
            localfile = os.path.join(self.current_data_folder, self.CWD_DIR, remote_file)
            if force or not os.path.exists(localfile) or \
                    self.remote_is_better((remote_file, remote_lastmodified), localfile):
                # register new release (will be stored in backend)
                self.release = self.timestamp
                self.to_dump.append({"remote": remote_file, "local": localfile})


def main():
    dumper = InterproDumper()
    dumper.dump()


if __name__ == "__main__":
    main()
