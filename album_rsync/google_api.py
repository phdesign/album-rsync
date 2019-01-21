import webbrowser
import urllib.parse
import uuid
import logging
from functools import partial
import requests

PAGE_SIZE = 100
BASE_URL = 'https://photoslibrary.googleapis.com'
logger = logging.getLogger(__name__)

class GoogleApi:

    def __init__(self, config, resiliently):
        self._config = config
        self._resiliently = resiliently
        self._resilient_get = partial(self._resiliently.call, self._get)
        self._resilient_post = partial(self._resiliently.call, self._post)
        self._resilient_download = partial(self._resiliently.call, self._download)
        self._resilient_upload = partial(self._resiliently.call, self._upload)
        self._access_token = None
        self._refresh_token = None

    def list_albums(self):
        return self._walk(self._resilient_get, f'{BASE_URL}/v1/albums', {}, 'albums')

    def create_album(self, title):
        data = {'album': {'title': title}}
        return self._resilient_post(f'{BASE_URL}/v1/albums', data=data)

    def get_media_in_folder(self, album_id):
        data = {
            'albumId': album_id,
            'pageSize': PAGE_SIZE
        }
        return self._walk(self._resilient_post, f'{BASE_URL}/v1/mediaItems:search', data, 'mediaItems')

    def download(self, url, dest):
        self._resilient_download(url, dest)

    def upload(self, src_path, file_name, folder_id):
        upload_token = self._resilient_upload(f'{BASE_URL}/v1/uploads', src_path, file_name)
        data = {
            'newMediaItems': [
                {
                    'description': '',
                    'simpleMediaItem': {
                        'uploadToken': upload_token
                    }
                }
            ]
        }
        if folder_id:
            data['albumId'] = folder_id
        self._resilient_post(f'{BASE_URL}/v1/mediaItems:batchCreate', data=data)

    @staticmethod
    def _walk(func, url, data, prop):
        while True:
            resp = func(url, data)
            data['pageToken'] = resp['nextPageToken'] if 'nextPageToken' in resp else None
            if prop not in resp:
                break

            for item in resp[prop]:
                yield item

            if not data['pageToken']:
                break

    def _get(self, url, params=None):
        resp = self._authenticated_call(requests.get, url, params=params)
        resp.raise_for_status()
        return resp.json()

    def _post(self, url, data):
        resp = self._authenticated_call(requests.post, url, json=data)
        resp.raise_for_status()
        return resp.json()

    def _download(self, url, dest):
        resp = self._authenticated_call(requests.get, url, stream=True)
        resp.raise_for_status()
        with open(dest, 'wb') as f:
            for chunk in resp:
                f.write(chunk)

    def _upload(self, url, src_path, file_name):
        data = open(src_path, 'rb').read()
        headers = {
            'Content-Type': 'application/octet-stream',
            'X-Goog-Upload-File-Name': file_name,
            'X-Goog-Upload-Protocol': 'raw'
        }
        resp = self._authenticated_call(requests.post, url, data=data, headers=headers)
        resp.raise_for_status()
        upload_token = resp.text
        return upload_token

    def _authenticated_call(self, func, *args, **kwargs):
        self._authenticate()

        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['Authorization'] = 'Bearer ' + self._access_token
        resp = func(*args, **kwargs)
        if resp.status_code == 401:
            logger.info('refreshing token...')
            self._get_refresh_token()
            kwargs['headers']['Authorization'] = 'Bearer ' + self._access_token
            resp = func(*args, **kwargs)
        return resp

    def _get_refresh_token(self):
        data = {
            'client_id': self._config.google_api_key,
            'client_secret': self._config.google_api_secret,
            'refresh_token': self._refresh_token,
            'grant_type': 'refresh_token'
        }
        resp = self._resiliently.call(requests.post, 'https://www.googleapis.com/oauth2/v4/token', data=data)
        result = resp.json()
        self._access_token = result['access_token']
        self._config.save_tokens(self._config.PATH_GOOGLE, {
            'access_token': self._access_token,
            'refresh_token': self._refresh_token
        })

    def _authenticate(self):
        if self._access_token:
            return

        tokens = self._config.load_tokens(self._config.PATH_GOOGLE)
        if not tokens or not tokens['refresh_token']:
            challenge = "{}{}".format(uuid.uuid4().hex, uuid.uuid4().hex)
            url = self._build_auth_url(challenge)
            webbrowser.open(url)
            print("Please enter the OAuth verifier tag once logged in:")
            auth_code = input("> ")
            tokens = self._get_token(auth_code, challenge)
            self._config.save_tokens(self._config.PATH_GOOGLE, {
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token']
            })

        self._access_token = tokens['access_token']
        self._refresh_token = tokens['refresh_token']

    def _build_auth_url(self, challenge):
        params = {
            'client_id': self._config.google_api_key,
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
            'response_type': 'code',
            'scope': 'https://www.googleapis.com/auth/photoslibrary',
            'code_challenge': challenge
        }
        base_url = 'https://accounts.google.com/o/oauth2/v2/auth?'
        return base_url + urllib.parse.urlencode(params)

    def _get_token(self, auth_code, challenge):
        data = {
            'code': auth_code,
            'client_id': self._config.google_api_key,
            'client_secret': self._config.google_api_secret,
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
            'grant_type': 'authorization_code',
            'code_verifier': challenge
        }
        resp = self._resiliently.call(requests.post, 'https://www.googleapis.com/oauth2/v4/token', data=data)
        resp.raise_for_status()
        return resp.json()
