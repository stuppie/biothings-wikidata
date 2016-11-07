#!/usr/bin/env python

import asyncio
import os

import asyncssh
import concurrent.futures
import sys
from functools import partial

executor = concurrent.futures.ProcessPoolExecutor(max_workers=2)
loop = asyncio.get_event_loop()
loop.set_default_executor(executor)

import config, biothings

biothings.config_for_app(config)

import contrib
import biothings.dataload.uploader as uploader
import biothings.dataload.dumper as dumper

# will check every 10 seconds for sources to upload
umanager = uploader.UploaderManager(poll_schedule='* * * * * */10', event_loop=loop)
umanager.register_sources(contrib.__sources_dict__)
umanager.poll()

dmanager = dumper.DumperManager(loop)
dmanager.register_sources(contrib.__sources_dict__)
dmanager.schedule_all()

from biothings.utils.hub import schedule

COMMANDS = {
    # dump commands
    "dm": dmanager,
    "dump": dmanager.dump_src,
    "dump_all": dmanager.dump_all,
    # upload commands
    "um": umanager,
    "upload": umanager.upload_src,
    "upload_all": umanager.upload_all,
    # admin/advanced
    "loop": loop,
    "executor": executor,
    "g": globals(),
    "sch": partial(schedule, loop),
}

passwords = {
    'guest': '',  # guest account with no password
}

from biothings.utils.hub import start_server

cwd = os.path.dirname(os.path.realpath(__file__))
server = start_server(loop, "wikidata hub", passwords=passwords, port=8022, commands=COMMANDS, keys=[os.path.join(cwd,'ssh_host_key')])

try:
    loop.run_until_complete(server)
except (OSError, asyncssh.Error) as exc:
    sys.exit('Error starting server: ' + str(exc))

loop.run_forever()
