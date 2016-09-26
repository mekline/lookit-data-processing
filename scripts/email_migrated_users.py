import argparse
import logging
import requests

from client import Account, ExperimenterClient
import conf

url = '{}/v1/id/collections/{}.accounts/_search?q=_exists_:migratedFrom'.format(conf.JAM_HOST, conf.JAM_NAMESPACE)  # noqa


def main(dry=True, debug=False, verbosity=0, user=None):
    verbosity = min(max(verbosity, 0), 2)
    if verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    elif verbosity == 2:
        logging.basicConfig(level=logging.DEBUG)

    client = ExperimenterClient(access_token=conf.OSF_ACCESS_TOKEN).authenticate()

    if user:
        account_payload = client.fetch_account(user)
        user_account = Account.from_data(account_payload)
        accounts = [user_account]
    else:
        accounts = client.fetch_accounts('q=_exists_:migratedFrom')
    for account in accounts:
        logging.info(u'Sending password reset request to {} for account {} ({})'.format(
            account.email, account.name, account.id))
        if not dry:
            url = '{}/v1/id/collections/{}.accounts/user'.format(conf.JAM_HOST, conf.JAM_NAMESPACE)
            res = requests.post(
                url,
                json={
                    'data': {
                        'type': 'reset',
                        'attributes': {
                            # Send only item ID (namespace.collection.<item_id>)
                            'id': account.id.rsplit('.', 1)[-1]
                        }
                    }
                }
            )
            if res.status_code != 201:
                if debug:
                    import ipdb
                    ipdb.set_trace()
                else:
                    raise RuntimeError(res.json())

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry', action='store_true')
    parser.add_argument('--debug',
                        action='store_true',
                        help='Launch a python debugger for failed requests (developer tool)')
    parser.add_argument('-u', '--user',
                        type=str,
                        help='If specified, only perform migration on a single user account')
    parser.add_argument('-v',
                        '--verbosity',
                        type=int,
                        default=0,
                        choices=(0, 1, 2),
                        help='Log basic information (level 1) or in-depth messages (level 2)')
    # Actually consumed in another module, but parser fails with error if argument is not defined
    parser.add_argument('-c', '--config', type=str, help='Config file location')
    args = parser.parse_args()
    main(dry=args.dry,
         debug=args.debug,
         verbosity=args.verbosity,
         user=args.user)
