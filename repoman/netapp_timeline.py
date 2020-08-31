from .timeline import Timeline
import os
from os import path, symlink
import requests


def unimplemented():
    raise Exception("NetappTimeline does not support this feature")

class NetappClient(object):
    def __init__(self, filer, user, password, volume_name):
        self._session = requests.Session()
        self._session.auth = (user, password)
        self._session.verify = False
        self._api = 'https://{0}/api'.format(filer)

        self.volume = self._get_volume(volume_name)
        
    def get(self, path, json=None):
        r = self._session.get(self._api + path, json=json)
        r.raise_for_status()
        return r

    def post(self, path, json=None):
        r = self._session.post(self._api + path, json=json)
        r.raise_for_status()
        return r

    def _get_volume(self, name):
        r = self.get('/storage/volumes?name={0}'.format(name))
        # Just fail if not found
        return r.json()['records'][0]['uuid']

    def list_snapshots(self):
        return self.get('/storage/volumes/{0}/snapshots'.format(self.volume)).json()

    def create_snapshot(self, snapshot_name):
        return self.post('/storage/volumes/{0}/snapshots'.format(self.volume), {'name': snapshot_name, 'comment': 'Created by repoman' })

    def delete_snapshot(self, snapshot_name):
        unimplemented()

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

    def __init__(self, source, destination):
        super().__init(name, source, destination, client = None)
        self._client = client
        self._snapshot_path = path.join(source, ".snapshots")

        if not path.exists(self._snapshot_path):
            raise Exception("Source '{0}' does not look like a Netapp volume (missing .snapshots directory)".format(source))

    def __str__(self):
        s = super().__str__()
        return s + "\nNetapp\n"

    def get_max_snapshots(self):
        return 128

    def set_excludes(self, excludes):
        pass

    def get_excludes(self):
        # unsupported
        return []

    def _save_cfgfile(self):
        # no configuration to save
        pass

    def _load_cfgfile(self):
        # no configuration to load
        pass


    def _link_snapshot(self, destination, netapp_snapshot_name):
        target = path.join(self._snapshot_path, netapp_snapshot_name)
        symlink(target, destination)

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
        netapp_snap_name = "rm-{0}-{1}".format(self.name, snapshot)
        self._client.create_snapshot(snap_name)
        self._link_snapshot(snapshot, netapp_snap_name)


    def create_snapshot(self, random_sleep_before_snapshot=None, sleep_after_snapshot=None):
        name = datetime.now().strftime("%Y.%m.%d-%H%M%S")
        self.create_named_snapshot(name)
        self.rotate_snapshots()

    def delete_snapshot(self, snapshot, skip_linked=False):
        unimplemented()

    #   implemented in base class
    #def expire_snapshots(self, older_than_days, dryrun=False):
    #def create_link(self, link, snapshot=None, max_offset=0, warn_before_max_offset=0):
    #def delete_link(self, link):
    #def update_link(self, link, snapshot=None):
    #def rotate_snapshots(self):

