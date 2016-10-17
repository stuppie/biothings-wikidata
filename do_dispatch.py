'''
This module monitors src_dump collection in MongoDB, dispatch dataloading
.obs when new data files are available.

    python -u -m dataload/dispatch -d

    * with "-d" parameter, it will continue monitoring,
      without "-d", it will quit after all running jobs are done.

'''
import os
import os.path
import sys
import time
from subprocess import STDOUT, check_output

import biothings
from biothings.utils.common import safewfile, timesofar
from biothings.utils.mongo import get_src_dump

import config

biothings.config_for_app(config)
src_dump = get_src_dump()


def check_mongo():
    """Check for "pending_to_upload" flag in src_dump collection.
       And return a list of sources should be uploaded.
    """
    # filter some more: _id is supposed to be a user-defined string, not an ObjectId()
    src_dump = get_src_dump()
    return [src['_id'] for src in src_dump.find({'pending_to_upload': True}) if type(src['_id']) == str]


def dispatch_src_upload(src):
    src_doc = src_dump.find_one({'_id': src})
    datadump_logfile = src_doc.get('logfile', '')
    # TODO: logfile will be used by logging module, does the following interfer with it ?
    if datadump_logfile:
        upload_logfile = os.path.join(os.path.split(datadump_logfile)[0], '{}_upload.log'.format(src))
    else:
        upload_logfile = os.path.join(config.DATA_ARCHIVE_ROOT, '{}_upload.log'.format(src))

    log_f, logfile = safewfile(upload_logfile, prompt=False, default='O')
    p = Popen(['python', '-u', "upload.py", src],
              stdout=log_f, stderr=STDOUT, cwd=config.APP_PATH)
    p.log_f = log_f
    return p


def mark_upload_started(src):
    # TODO: unset pending_to_upload is done in uploader too, but we need to
    # keep it here as well as the time required for the uploader to unset it, dispatcher
    # may decide to run the same uploader again as the flag is still there. Ideally
    # this shouldn't be needed there
    src_dump.update({'_id': src}, {"$unset": {'pending_to_upload': "",
                                              'upload': ""}})


def get_process_info(running_processes):
    name_d = dict([(str(p.pid), name) for name, p in running_processes.items()])
    pid_li = name_d.keys()
    if pid_li:
        output = check_output(['ps', '-p', ' '.join(pid_li)])
        output = output.decode("utf8").split('\n')
        output[0] = '    {:<10}'.format('JOB') + output[0]  # header
        for i in range(1, len(output)):
            line = output[i].strip()
            if line:
                pid = line.split()[1]
                output[i] = '    {:<10}'.format(name_d.get(pid, '')) + output[i]
    return '\n'.join(output)


from subprocess import Popen
import dispatch

from config import DATA_WWW_ROOT_URL, DISPATCHER_SLEEP_TIME

try:
    from biothings.utils.hipchat import hipchat_msg
except:
    hipchat_msg = None


class DocDispatcher(object):
    def __init__(self):
        # define events
        self.source_update_available = dispatch.Signal(providing_args=["src_to_update"])
        self.source_upload_success = dispatch.Signal(providing_args=["src_name"])
        self.source_upload_failed = dispatch.Signal(providing_args=["src_name"])
        # and connect to handlers
        self.source_update_available.connect(self.handle_src_upload)
        self.source_upload_success.connect(self.handle_src_upload_success)
        self.source_upload_failed.connect(self.handle_src_upload_failed)

    running_processes_upload = {}
    idle = True

    def check_src_dump(self):
        src_to_update_li = check_mongo()
        if src_to_update_li:
            print('\nDispatcher:  found pending jobs ', src_to_update_li)
            for src_to_update in src_to_update_li:
                self.source_update_available.send(sender=self, src_to_update=src_to_update)

    def handle_src_upload(self, src_to_update, **kwargs):
        mark_upload_started(src_to_update)
        p = dispatch_src_upload(src_to_update)
        p.t0 = time.time()
        self.running_processes_upload[src_to_update] = p

    def check_src_upload(self):
        running_processes = self.running_processes_upload
        jobs_finished = []
        if running_processes:
            self.idle = True
            print('Dispatcher:  {} active job(s)'.format(len(running_processes)))
            print(get_process_info(running_processes))

        for src in running_processes:
            p = running_processes[src]
            returncode = p.poll()
            if returncode is None:
                p.log_f.flush()
            else:
                t1 = round(time.time() - p.t0, 0)
                jobs_finished.append(src)
                p.log_f.close()

                if returncode == 0:
                    msg = 'Dispatcher:  "{}" uploader finished successfully with code {} (time: {})'.format(src, returncode, timesofar(p.t0,t1=t1))
                    print(msg)
                    if hipchat_msg:
                        msg += '<a href="{}/log/dump/{}">dump log</a>'.format(DATA_WWW_ROOT_URL, src)
                        msg += '<a href="{}/log/upload/{}">upload log</a>'.format(DATA_WWW_ROOT_URL, src)
                        hipchat_msg(msg, message_format='html', color="green")
                    self.source_upload_success.send(self, src_name=src)
                else:
                    msg = 'Dispatcher:  "{}" uploader failed with code {} (time: {}s)'.format(src, returncode, t1)
                    print(msg)
                    if hipchat_msg:
                        hipchat_msg(msg, color="red")
                    self.source_upload_failed.send(self, src_name=src)

        for src in jobs_finished:
            del running_processes[src]

    def handle_src_upload_success(self, src_name, **kwargs):
        print("upload success: {}".format(src_name))
        if src_name == 'interpro':
            self.handle_interpro_bot()

    def handle_src_upload_failed(self, src_name, **kwargs):
        print("upload failed: {}".format(src_name))

    def handle_interpro_bot(self):
        # cleanup src and target collections
        # src_clean_archives(noconfirm=True)
        # target_clean_collections(noconfirm=True)
        conf = "interpro"
        t0 = time.time()
        p = Popen(['python', 'bot.py'], cwd=os.path.join(config.APP_PATH, "contrib/interpro"))
        returncode = p.wait()
        t = timesofar(t0)
        if returncode == 0:
            msg = 'Dispatcher:  "{}" builder finished successfully with code {} (time: {})'.format(conf, returncode, t)
            color = "green"
        else:
            msg = 'Dispatcher:  "{}" builder failed with code {} (time: {})'.format(conf, returncode, t)
            color = "red"
        print(msg)
        if hipchat_msg:
            msg += '<a href="{}/log/build/{}">build log</a>'.format(DATA_WWW_ROOT_URL, conf)
            hipchat_msg(msg, message_format='html', color=color)

    def run(self, args=[]):
        _flag = len(args) == 2
        while 1:
            self.idle = False
            self.check_src_dump()
            self.check_src_upload()
            # exit(1)
            if self.idle:
                sys.stdout.write('\b' * 50)
                for i in range(int(DISPATCHER_SLEEP_TIME * 10)):
                    sys.stdout.write('\b' * 2 + [chr(8212), '\\', '|', '/'][i % 4])
                    sys.stdout.flush()
                    time.sleep(0.1)
            else:
                time.sleep(DISPATCHER_SLEEP_TIME)
