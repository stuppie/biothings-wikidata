#!/usr/bin/env python

import sys
import biothings
import config
biothings.config_for_app(config)
import biothings.dataload.uploader
s = biothings.dataload.uploader.SourceManager()


def main(source):
    s.register_source("contrib.interpro.uploader")
    s.register_source("contrib.interpro.uploader_protein")
    s.register_source("contrib.interpro.uploader_dbinfo")
    s.register_source("contrib.mondo.uploader")
    s.upload_src(source)


if __name__ == "__main__":
    main(sys.argv[1])
