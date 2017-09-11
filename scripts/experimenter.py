"""
All-in-one script for basic Lookit/Experimenter platform management and administration tasks

Make sure to install requirements (`pip install requests`), then run at the command line as `python experimenter.py`
  for help and options.
"""
from __future__ import print_function

import argparse
import copy
import datetime
import json
import os
import pprint
import re
import sys
import requests

# Prepackaged defaults for convenience when distributing this script to users
JAMDB_SERVER_URL = 'https://staging-metadata.osf.io'
JAMDB_NAMESPACE = 'lookit'

########
# Basic client logic
class ExperimenterClient(object):
    """
    Base class for experimenter requests
    """
    BASE_URL = JAMDB_SERVER_URL
    NAMESPACE = JAMDB_NAMESPACE

    def __init__(self, jam_token=None, url=None, namespace=None):
        self.jam_token = jam_token
        self.BASE_URL = url or self.BASE_URL
        self.NAMESPACE = namespace or self.NAMESPACE

    def _url_for_collection(self, collection):
        return '{}/v1/id/collections/{}.{}'.format(
            self.BASE_URL,
            self.NAMESPACE,
            collection
        )

    def _url_for_collection_records(self, collection):
        base_url = self._url_for_collection(collection)
        return base_url + '/documents/'

    def _make_request(self, method, *args, **kwargs):
        """Make a request with the appropriate authorization"""
        headers = kwargs.get('headers', {})
        headers['authorization'] = self.jam_token
        kwargs['headers'] = headers

        res = getattr(requests, method)(*args, **kwargs)
        if res.status_code >= 400:
            print('Request completed with error status code: ', res.status_code)
            print('Detailed response with error description is below')
            pprint.pprint(res.json(), indent=4)

        return res



    def _fetch_all(self, response):
        # TODO: Rewrite this as a generator
        res_json = response.json()

        try:
            data = res_json['data']
        except KeyError:
            return {
                'data': []
            }

        total = res_json['meta']['total']
        per_page = res_json['meta']['perPage']
        remainder = total - per_page
        page = 2
        while remainder > 0:
            response = self._make_request(
                response.request.method.lower(),
                response.request.url.split('?page=')[0],
                params={
                    'page': page
                }
            )
            data = data + response.json()['data']
            remainder = remainder - per_page
            page += 1
        res_json['data'] = data
        return res_json

    @classmethod
    def authenticate(cls, osf_token, base_url=None, namespace=None):
        """
        Perform the authentication flow, exchanging an OSF access token for a JamDB token

        :param osf_token:
        :param base_url:
        :param namespace:
        :return:
        """
        base_url = base_url or cls.BASE_URL
        namespace = namespace or cls.NAMESPACE

        res = requests.post(
            '{}/v1/auth/'.format(base_url),
            json={
                'data': {
                    'type': 'users',
                    'attributes': {
                        'provider': 'osf',
                        'access_token': osf_token
                    }
                }
            }
        )
        if res.status_code != 200:
            raise Exception('Authentication failed. Please provide a valid OSF personal access token')

        return cls(
            jam_token=res.json()['data']['attributes']['token'],
            url=base_url,
            namespace=namespace
        )

    def fetch_collection_records(self, collection):
        """Fetch all records that are a member of the specified collection"""
        url = self._url_for_collection_records(collection)
        res = self._make_request('get', url)
        if res.status_code == 404:
            print('No results found for specified collection!')
            return []
        else:
            return self._fetch_all(res)['data']

    def set_session_feedback(self, session, feedback):
        url = '{}/v1/id/documents/{}/'.format(
            self.BASE_URL,
            session['id']
        )
        return self._make_request(
            'patch',
            url,
            headers={
                'content-type': 'application/vnd.api+json; ext=jsonpatch',
            },
            data=json.dumps([{
                'op': 'add',
                'path': '/feedback',
                'value': feedback
            }])
        )

def update_session_data(experimentId, display=False):
	'''Get session data from the server for this experiment ID and save'''
	client = ExperimenterClient.authenticate(conf.OSF_ACCESS_TOKEN, base_url=conf.JAM_HOST, namespace=conf.JAM_NAMESPACE)
	exp = client.fetch_collection_records(paths.make_long_expId(experimentId))
	backup_and_save(paths.session_filename(experimentId), exp)
	if display:
		printer.pprint(exp)
	print "Synced session data for experiment: {}".format(experimentId)

def update_account_data():
	'''Get current account data from the server and save to the account file'''
	client = ExperimenterClient.authenticate(conf.OSF_ACCESS_TOKEN, base_url=conf.JAM_HOST, namespace=conf.JAM_NAMESPACE)
	accountData = client.fetch_collection_records('accounts')
	print('Download complete. Found {} records'.format(len(accountData)))
	allAccounts = {acc[u'id'].split('.')[-1]: acc for acc in accountData}
	backup_and_save(paths.ACCOUNT_FILENAME, allAccounts)
