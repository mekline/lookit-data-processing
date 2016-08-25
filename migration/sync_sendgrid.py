import json

from scripts import sendgrid_client as SG

sg = SG.SendGrid()
ASM_GROUPS = sg.groups()


# h/t http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks-in-python
def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def sync_account(account, email_prefs):
    for gid, group in ASM_GROUPS.items():
        if email_prefs.get(gid, True):
            sg.subscribe_to(group, account['email'])
        else:
            sg.unsubscribe_from(group, account['email'])


def sync_all(accounts=None):
    accounts = accounts or json.load(open('./migration/output/accounts.json', 'r'))
    groups = {gid: [] for gid in ASM_GROUPS.keys()}
    for account in accounts:
        email_prefs = account['emailPreferences']
        for gid, group in ASM_GROUPS.items():
            if not email_prefs[gid]:
                groups[gid].append(account['email'])
    for gid, emails in groups.items():
        try:
            for chunk in chunks(emails, 100):
                sg.batch_unsubscribe_from(ASM_GROUPS[gid], [e for e in chunk])
        except Exception as err:  # noqa
            import ipdb
            ipdb.set_trace()


sync_all() if __name__ == '__main__' else None
