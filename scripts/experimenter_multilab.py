"""
Functions to access/edit Lookit data via API.

Make sure to install requirements (`pip install requests`).
"""
from __future__ import print_function
from utils import printer, backup_and_save
import lookitpaths as paths

import argparse
import copy
import datetime
import json
import os
import pprint
import re
import sys
import random
import requests
import conf

#res = requests.get(
#    '{}/api/v1/studies/'.format(base_url, study),
#    headers=headers
#)
#studies = res.json()['data']
#for study in studies:
#    if study['attributes']['state'] == 'active':
#        print('{}: {}'.format(study['attributes']['name'], study['id']))
#

# for resp in responses:
#   demo = requests.get(
#     resp['relationships']['demographic_snapshot']['links']['related'],
#     headers=headers
#   ).json()
#   #printer.pprint(demo)
#   child = requests.get(
#     resp['relationships']['child']['links']['related'],
#     headers=headers
#   ).json()
#   #printer.pprint(child)
#   user = requests.get(
#     child['data']['relationships']['user']['links']['related'],
#     headers=headers
#   ).json()
#   #printer.pprint(user)


########
# Basic client logic
class ExperimenterClient(object):
    """
    Base class for experimenter requests
    """

    def __init__(self, jam_token=None, url=None, namespace=None):
        self.BASE_URL = conf.LOOKIT_HOST
        self.TOKEN = conf.LOOKIT_ACCESS_TOKEN
        self.session = requests.Session()
        self.session.headers.update({'Authorization': 'Token ' + self.TOKEN})

    def _url_for_collection(self, collection):
        return '{}/api/v1/{}/'.format(
            self.BASE_URL,
            collection
        )

    def fetch_collection_records(self, collection):
        """Fetch all records that are a member of the specified collection"""
        url = self._url_for_collection(collection)
        res = self.session.get(url)
        if res.status_code == 404:
            print('No results found for specified collection!')
            return []
        res = res.json()
        respLink = res['links']['next']
        hasMore = respLink is not None
        data = res['data']
        while hasMore:
            res = self.session.get(respLink).json()
            data = data + res['data']
            respLink = res['links']['next']
            hasMore = respLink is not None
        return data

    def set_session_feedback(self, session, feedback):
        """Add session feedback.
        session: dict, {'id': SESSIONID}
        feedback: string

        if successful, returns dict with structure:
        {
            'attributes': {'comment': feedback},
            'id': [feedback ID, new],
            'links': {'self': [feedback URL]},
            'relationships': {
                'researcher': { 'links': { 'related': [researcher URL]}},
                'response':   { 'links': { 'related': [response URL]}},
            'type': 'feedback'
        }
        """

        url = self._url_for_collection('feedback')

        feedbackdata = {
            "data": {
                "attributes": {
                     "comment": feedback
                },
               "relationships": {
                 "response": {
                   "data": {
                     "type": "responses",
                     "id": session['id']
                   }
                 }
               },
               "type": "feedback"
            }
        }

        return self.session.post(
            url,
            headers = {'Content-type': "application/vnd.api+json"},
            json = feedbackdata
        ).json()['data']

# TODO: check that this lines up with existing data
def update_session_data(experimentId, display=False):
    '''Get session data from the server for this experiment ID and save'''
    client = ExperimenterClient()
    exp = client.fetch_collection_records(
        'studies/{}/responses/'.format(experimentId)
    )
    backup_and_save(paths.session_filename(experimentId), exp)
    if display:
        printer.pprint(exp)
    print("Synced session data for experiment: {}".format(experimentId))

# TODO: implement this. Will need to get all user, demographic, child data and put together as currently in accounts.
#
# def update_account_data():
#   '''Get current account data from the server and save to the account file'''
#   client = ExperimenterClient.authenticate(conf.OSF_ACCESS_TOKEN, base_url=conf.JAM_HOST, namespace=conf.JAM_NAMESPACE)
#   accountData = client.fetch_collection_records('accounts')
#   print('Download complete. Found {} records'.format(len(accountData)))
#   allAccounts = {acc[u'id'].split('.')[-1]: acc for acc in accountData}
#   backup_and_save(paths.ACCOUNT_FILENAME, allAccounts)

# TODO: in coding.py, need to remove authentication and just do feedback
# TODO: clean up all experiment, session IDs (short/long form). Now have session IDs '70001813-076d-4cdc-a982-148e2d2a395c' instead  of "lookit.session583c892ec0d9d70082123d94s.583c8cc0c0d9d70081123d9e"
# TODO: deal with new names in attributes: 'exp_data', 'global_event_timings'
# TODO: deal with lack of study ID in attributes
# TODO: branch of lookit for new site code, then just switch between

if __name__ == '__main__':
    print("testing")
    client = ExperimenterClient()
    printer.pprint( client.set_session_feedback( {'id': "4f2b6eba-3523-4e4c-a3dc-312284bd9d51"}, "silly comment"))
    update_session_data('515c064a-4938-4f0d-b773-8ae84264ee84', display=True)
