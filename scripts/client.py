import json
import requests

import conf


class Account(object):

    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email

    @classmethod
    def from_data(cls, data):
        attrs = data['attributes']
        return cls(
            id=data['id'],
            name=attrs.get('name', ''),
            email=attrs.get('email'),
        )


class ExperimenterClient(object):

    BASE_URL = conf.JAM_HOST
    NAMESPACE = conf.JAM_NAMESPACE

    def __init__(self, access_token=None, jwt=None, url=None, namespace=None):
        self.access_token = access_token
        self.jwt = jwt
        self.BASE_URL = url or self.BASE_URL
        self.NAMESPACE = namespace or self.NAMESPACE

    def _make_request(self, method, *args, **kwargs):
        headers = kwargs.get('headers', {})
        headers['authorization'] = self.jwt
        kwargs['headers'] = headers
        return getattr(requests, method)(*args, **kwargs)

    def _fetch_all(self, response):
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

    def authenticate(self):
        res = requests.post(
            '{}/v1/auth/'.format(self.BASE_URL),
            data=json.dumps({
                'data': {
                    'type': 'users',
                    'attributes': {
                        'provider': 'osf',
                        'access_token': conf.OSF_ACCESS_TOKEN
                    }
                }
            })
        )
        return type(self)(
            access_token=self.access_token,
            jwt=res.json()['data']['attributes']['token'],
            url=self.BASE_URL,
            namespace=self.NAMESPACE
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

    def fetch_account(self, account_id):
        url = '{}/v1/id/documents/{}.accounts.{}'.format(
            self.BASE_URL,
            self.NAMESPACE,
            account_id
        )
        res = self._make_request('get', url)
        if res.status_code != 200:
            return None
        if res.json().get('data'):
            return res.json()['data']
        return None

    def delete_account(self, account):
        url = '{}/v1/namespaces/{}/collections/accounts/documents/{}'.format(
            self.BASE_URL,
            self.NAMESPACE,
            account.id.split('.')[-1]
        )
        return self._make_request('delete', url)

    def get_demographics_for_account(self, account_id):
        account = self.fetch_account(account_id)
        if account:
            return {
                key: value
                for key, value in account['attributes'].items()
                if 'demographics' in key
            }
        return None

    def fetch_accounts(self, query=None):
        url = '{}/v1/id/collections/{}.accounts/{}'.format(
            self.BASE_URL,
            self.NAMESPACE,
            '_search?' + query if query else 'documents'
        )
        return map(
            Account.from_data,
            self._fetch_all(self._make_request('get', url))['data']
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


def test():
    client = ExperimenterClient(access_token=conf.OSF_ACCESS_TOKEN).authenticate()  # noqa
    '''
    exps = client.fetch_experiments()
    for exp in exps:
        exp['sessions'] = client.fetch_sessions_for_experiment(exp)

    exp = exps[3]
    sess = exp['sessions'][0]
    res = client.set_session_feedback(sess, "Some test feedback")
    print """
    Feedback set to: {}
    on session: {}
    of experiment: {}
    """.format(
        res.json()['data']['attributes']['feedback'],
        sess['id'].split('.')[-1],
        exp['attributes']['title']
    )
    '''
    account_id = 'sam'
    print """
    Demographics for {}:
    {}
    """.format(account_id, json.dumps(
        client.get_demographics_for_account(account_id),
        indent=4
    ))

test() if __name__ == '__main__' else None
