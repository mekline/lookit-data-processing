import os
import json
import requests

import sendgrid
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

OSF_ACCESS_TOKEN = os.environ.get('OSF_ACCESS_TOKEN')
SENDGRID_KEY = os.environ.get('SENDGRID_KEY')

JAM_URL = os.environ.get('JAMDB_URL')
JAM_NAMESPACE = os.environ.get('JAMDB_NAMESPACE')

class EmailPreferences(object):

    ASM_MAPPING = {
        'Next Session': 'nextSession',
        'New Studies': 'newStudies',
        'Results Published': 'resultsPublished'
    }

    def __init__(self, nextSession, newStudies, resultsPublished):
        self.nextSession = nextSession
        self.newStudies = newStudies
        self.resultsPublished = resultsPublished


class Account(object):

    def __init__(self, id, name, email, emailPreferences):
        self.id = id
        self.name = name
        self.email = email
        self.emailPreferences = emailPreferences

    @classmethod
    def from_data(cls, data):
        attrs = data['attributes']
        return cls(
            id=data['id'],
            name=attrs.get('name', ''),
            email=attrs.get('email'),
            emailPreferences=EmailPreferences(
                nextSession=attrs.get('emailPreferencesNextSession', False),
                newStudies=attrs.get('emailPreferencesNewStudies', False),
                resultsPublished=attrs.get(
                    'emailPreferencesResultsPublished', False
                )
            )
        )

    @classmethod
    def update_email_preference_op(self, preference, value):
        return {
            op: 'replace',
            path: '/{0}'.format(preference),
            value: value
        }

class SendGrid(object):

    def __init__(self, apikey=None):
        self.sg = sendgrid.SendGridAPIClient(
            apikey=apikey or SENDGRID_KEY
        )

    def groups(self):
        res = self.sg.client.asm.groups.get()
        return {
            EmailPreferences.ASM_MAPPING[group['name']]: group
            for group in json.loads(res.response_body)
        }

    def unsubscribes_for(self, group):
        return json.loads(
            self.sg.client.asm.groups._(
                group['id']
            ).suppressions.get().response_body
        ) or []

    def unsubscribe_from(self, group, email):
        return self.batch_unsunscribe_from(group, [email])

    def batch_unsubscribe_from(self, group, emails):
        return json.loads(
            self.sg.client.asm.groups._(group['id']).suppressions.post(
                request_body={"recipient_emails": emails}
            ).response_body
        )

    def subscribe_to(self, group, email):
        return json.loads(
            self.sg.client.asm.groups._(group['id']).suppressions._(
                email
            ).delete().response_body
        )


class ExperimenterClient(object):

    BASE_URL = JAM_URL
    NAMESPACE = JAM_NAMESPACE

    def __init__(self, access_token=None, jwt=None):
        self.access_token = access_token
        self.jwt = jwt

    def _make_request(self, method, *args, **kwargs):
        headers = kwargs.get('headers', {})
        headers['authorization'] = self.jwt
        kwargs['headers'] = headers
        return getattr(requests, method)(*args, **kwargs)

    def _fetch_all(self, response):
        res_json = response.json()

        data = res_json['data']

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

    def authenticate(self):
        res = requests.post(
            '{}/v1/auth/'.format(self.BASE_URL),
            data=json.dumps({
                'data': {
                    'type': 'users',
                    'attributes': {
                        'provider': 'osf',
                        'access_token': OSF_ACCESS_TOKEN
                    }
                }
            })
        )
        return type(self)(
            access_token=self.access_token,
            jwt=res.json()['data']['attributes']['token']
        )

    def fetch_experiments(self):
        url = '{}/v1/id/collections/{}.experiments/documents/'.format(
            self.BASE_URL,
            self.NAMESPACE
        )
        return self._fetch_all(self._make_request('get', url))['data']

    def fetch_sessions_for_experiment(self, experiment):
        url = '{}/v1/id/collections/{}.session{}s/documents/'.format(
            self.BASE_URL,
            self.NAMESPACE,
            experiment['id'].split('.')[-1]
        )
        res = self._make_request('get', url)
        if res.status_code == 404:
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

    def fetch_accounts(self):
        url = '{}/v1/id/collections/{}.accounts/documents/'.format(
            self.BASE_URL,
            self.NAMESPACE
        )
        return filter(
            lambda a: bool(a.email),
            map(
                Account.from_data,
                self._fetch_all(self._make_request('get', url))['data']
            )
        )

    def update_accounts(self, updates):
        for id, ops in updates.iteritems():
            url = '{}/v1/id/documents/{}/'.format(
                self.BASE_URL,
                id
            )
            self._make_request(
                'patch',
                url,
                headers={
                    'content-type': 'application/vnd.api+json; ext=jsonpatch',
                },
                data=ops
            )

    def set_email_preferences(self):
        """
        For the 'first' sync. Assumes subscription groups are empty
        """
        sendgrid = SendGrid()
        groups = sendgrid.groups()
        accounts = list(self.fetch_accounts)
        for id, group in groups.iteritems():
            batch_unsubscribes = []
            for account in accounts:
                preference = getattr(account.emailPreferences, id, False)
                if not preference:
                    batch_unsubscribes.append(account.email)
            if batch_unsubscribes:
                sendgrid.batch_unsubscribe_from(group, batch_unsubscribes)

    def sync_email_preferences(self):
        """
        For all syncs after the initial one. Unsubscribes captured in sendgrid
        always get preference.

        TODO
        """
        sendgrid = SendGrid()
        groups = sendgrid.groups()
        accounts = list(self.fetch_accounts())
        account_updates = {}
        for id, group in groups.iteritems():
            unsubscribes = sendgrid.unsubscribes_for(group)
            batch_unsubscribes = []
            for account in accounts:
                preference = getattr(account.emailPreferences, id, False)
                if account.email in unsubscribes:
                    if preference:
                        updates = account_updates.get(account.id, [])
                        updates.append(Account.update_email_preference_op(
                            id,
                            False
                        ))
                else:
                    if not preference:
                        batch_unsubscribes.append(account.email)
                # if account.email in unsubscribes:
                #        sendgrid.subscribe_to(group, account.email)
                # else:
                #    if account.email not in unsubscribes:
                #        batch_unsubscribes.append(account.email)
            if batch_unsubscribes:
                sendgrid.batch_unsubscribe_from(group, batch_unsubscribes)
        if account_updates:
            self.update_accounts(account_updates)
