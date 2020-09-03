from .timeline import Timeline
from datetime import datetime
import os
from os import path, symlink
import requests
import urllib3

import logging

log = logging.getLogger('repoman.netapp_timeline')

def unimplemented():
    raise Exception("NetappTimeline does not support this feature")

class NetappClient(object):
    def __init__(self, filer, user, password, volume_name, verify=False):
        self._session = requests.Session()
        self._session.auth = (user, password)
        self._session.verify = verify
        self._api = 'https://{0}/api'.format(filer)
        # We don't care:
        if not verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.volume = self._get_volume(volume_name)
        
    def get(self, path, json=None, params=None):
        r = self._session.get(self._api + path, json=json, params=params)
        r.raise_for_status()
        return r

    def post(self, path, json=None):
        r = self._session.post(self._api + path, json=json)
        r.raise_for_status()
        return r

    def delete(self, path, json=None):
        r = self._session.delete(self._api + path, json=json)
        r.raise_for_status()
        return r

    def _get_volume(self, name):
        r = self.get('/storage/volumes', params={'name': name})
        # Just fail if not found
        return r.json()['records'][0]['uuid']

    def _get_snapshot(self, name):
        r = self.get('/storage/volumes/{0}/snapshots'.format(self.volume), params={'name': name})
        # Just fail if not found
        return r.json()['records'][0]['uuid']

    def create_snapshot(self, snapshot_name):
        log.info("Creating netapp snapshot %s on volume %s", snapshot_name, self.volume)
        return self.post('/storage/volumes/{0}/snapshots'.format(self.volume), {'name': snapshot_name, 'comment': 'Created by repoman' })

    def delete_snapshot(self, snapshot_name):
        uuid = self._get_snapshot(snapshot_name)
        log.info("Deleting netapp snapshot %s on volume %s", snapshot_name, self.volume)
        return self.delete('/storage/volumes/{0}/snapshots/{1}'.format(self.volume, uuid))

class DummyNetappClient(object):
    def __init__(self, filer, user, password, volume_name):
        self.volume = path.join(filer, volume_name)
        
    def list_snapshots(self):
        return listdir(self.volume)

    def create_snapshot(self, snapshot_name):
        os.mkdir(path.join(self.volume, snapshot_name))

    def delete_snapshot(self, snapshot_name):
        os.rmdir(path.join(self.volume, snapshot_name))

class NetappTimeline(Timeline):
    def __init__(self, name, source, destination):
        super().__init__(name, source, destination)
        self._client = None # need to call login()
        self._snapshot_path = path.join(source, ".snapshot")

        if not path.exists(self._snapshot_path):
            raise Exception("Source '{0}' does not look like a Netapp volume (missing .snapshot directory)".format(source))

    def save(self):
        # touch a file
        open(path.join(self._destination, '.netapp.cfg'), 'a').close()
        tmp = self._client
        self._client = None
        super().save()
        self._client = tmp

    def login(self, filer, user, password, volume):
        self._client = NetappClient(filer, user, password, volume)

    def __str__(self):
        s = super().__str__()
        return s + "\nNetapp\n"

    def set_excludes(self, excludes):
        pass

    def get_excludes(self):
        # unsupported
        return []

    def _link_snapshot(self, destination, netapp_snapshot_name):
        target = path.join(self._snapshot_path, netapp_snapshot_name)
        destination = path.join(self._destination, destination)
        os.symlink(target, destination)

    def _netapp_name(self, snapshot_name):
        return "rm-{0}-{1}".format(self._name, snapshot_name)

    def create_named_snapshot(self, snapshot, source_snapshot=None):
        now = datetime.now()
        if source_snapshot:
            raise Exception("Specifying a source snapshot is unsupported")
        self._check_frozen()

        snapshot_path = os.path.join(self._destination, snapshot)
        self._snapshots[snapshot] = {
                'created': now,
                'path': snapshot_path,
                'links': []
        }
        self._lsnapshots.append(snapshot)
        self.save()
        netapp_snap_name = self._netapp_name(snapshot)
        self._client.create_snapshot(netapp_snap_name)
        self._link_snapshot(snapshot, netapp_snap_name)


    def create_snapshot(self, random_sleep_before_snapshot=None, sleep_after_snapshot=None):
        name = datetime.now().strftime("%Y.%m.%d-%H%M%S")
        self.create_named_snapshot(name)
        self.rotate_snapshots()

    # We need to override this private method only; the delete_snapshot logic in the base class is sufficient
    def _rm_snapshot(self, snapshot_name, deleted_snapshot):
        netapp_snap_name = self._netapp_name(snapshot_name)
        symlink = os.unlink(path.join(self._destination, snapshot_name))
        self._client.delete_snapshot(netapp_snap_name)



    #   implemented in base class
    #def delete_snapshot(self, snapshot, skip_linked=False):
    #def expire_snapshots(self, older_than_days, dryrun=False):
    #def create_link(self, link, snapshot=None, max_offset=0, warn_before_max_offset=0):
    #def delete_link(self, link):
    #def update_link(self, link, snapshot=None):
    #def rotate_snapshots(self):

