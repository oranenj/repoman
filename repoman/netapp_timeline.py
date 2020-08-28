from timeline import Timeline
from os import path
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

class NetappTimeline(Timeline):

    def __init__(self, source):
        # destination is *only* used to store the timeline configuration
        destination = path.join(source, '.timeline_config')
        super().__init(name, source, destination)

    def get_max_snapshots(self):
        return 128
    def set_excludes(self, excludes):
        unimplemented()
    def get_excludes(self):
        unimplemented()
    def create_named_snapshot(self, snapshot, source_snapshot=None):
        unimplemented()

    def create_snapshot(self, random_sleep_before_snapshot=None, sleep_after_snapshot=None):
        unimplemented()

    def delete_snapshot(self, snapshot, skip_linked=False):
        unimplemented()

    def expire_snapshots(self, older_than_days, dryrun=False):
        unimplemented()

    def create_link(self, link, snapshot=None, max_offset=0, warn_before_max_offset=0):
        unimplemented()

    def delete_link(self, link):
        unimplemented()

    def update_link(self, link, snapshot=None):
        unimplemented()

    def rotate_snapshots(self):
        unimplemented()

