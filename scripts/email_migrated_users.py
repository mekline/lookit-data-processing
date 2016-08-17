import argparse
import logging
import requests

from client import ExperimenterClient, OSF_ACCESS_TOKEN
import conf

url = '{}/v1/id/collections/{}.accounts/_search?q=_exists_:migratedFrom'.format(conf.JAM_HOST, conf.JAM_NAMESPACE)  # noqa


def main(dry=True, debug=False, verbosity=0):
    verbosity = min(max(verbosity or 0, 0), 2)
    if verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    elif verbosity == 2:
        logging.basicConfig(level=logging.DEBUG)

    client = ExperimenterClient(access_token=OSF_ACCESS_TOKEN).authenticate()
    accounts = client.fetch_accounts('q=_exists_:migratedFrom')
    for account in accounts:
        logging.info('Sending password reset request to {} for account {} ({})'.format(account.email, account.name, account.id))  # noqa
        if not dry:
            res = requests.post(
                '{}/v1/id/collections/{}.accounts/user'.format(conf.JAM_HOST, conf.JAM_NAMESPACE),  # noqa
                {
                    "data": {
                        "type": "reset",
                        "attributes": {
                            "id": account.id
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
    parser.add_argument('-DR', '--dry', type=bool, default=True)
    parser.add_argument('-D', '--debug', type=bool, default=False)
    parser.add_argument('-V', '--verbosity', type=int, default=0, choices=(0, 1, 2))  # noqa
    args = parser.parse_args()
    main(**vars(args))
