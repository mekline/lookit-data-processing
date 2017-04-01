from sendgrid_client import EmailPreferences, SendGrid
from coding import *
from utils import printer
from updatefromlookit import update_account_data
import datetime
import numpy as np

if __name__ == '__main__':

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Send one-time announcement email about Lookit papers')
    parser.add_argument('--emails', help='Only send emails to these addresses (enter "all" to send to all eligible)',    action='append', default=['kimber.m.scott@gmail.com'])

    args = parser.parse_args()

    accounts = Experiment.load_account_data()

    # Get SendGrid object & unsubscribe group for notifications
    sg = SendGrid()
    groups = sg.groups()
    group = groups['resultsPublished']
    groupId = group['id']

    logfilename = '/Users/kms/lookit/scripts/logs/sentpaperannouncement.txt'

    with open(logfilename) as f:
        alreadySent = f.readlines()
    alreadySent = [x.strip() for x in alreadySent]
    print alreadySent

    logfile = open(logfilename, 'a+')

    nSent = 0

    # Go through accounts looking for people with birthdays in age range
    for (uname, acc) in accounts.items():

        name = acc['attributes']['name']
        recipient = acc['attributes']['email']

        isOldAccount = "migratedFrom" in acc['attributes'].keys()

        if isOldAccount:

            subject = 'Results published from Lookit study you participated in!'
            body = 'Hi ' + (name if name else uname) + ',<br><br>'
            body += "We're writing to let you know that the results of a study you and your child participated in on <a href='https://lookit.mit.edu/' target=_blank>Lookit</a> have been published! <br><br>Two papers describing our online replications of classic developmental studies are available in the first issue of the new open-access journal Open Mind. You can check them out here: <a href='http://www.mitpressjournals.org/toc/opmi/1/1' target=_blank>http://www.mitpressjournals.org/toc/opmi/1/1</a>. Thank you so much for participating - we couldn't have done this work without you!            <br><br>Happy Spring, <br><br>The Lookit team<br><br><hr>"

            if recipient in args.emails or 'all' in args.emails:
                print recipient
                print 'Recipient is unsubscribed from this list: {}'.format(
        recipient in sg.unsubscribes_for(group))
                print 'Already sent to recipient: {}'.format(
        recipient in alreadySent)

                if recipient not in alreadySent and recipient not in sg.unsubscribes_for(group):

                    print 'send email\n\n\n'
                    nSent += 1
                    status = sg.send_email_to(
                      recipient,
                      subject,
                      body,
                      group_id=groupId
                    )
                    if status == 200:
                        # Write email address to file
                        logfile.write(recipient + '\n')

    print nSent
    logfile.close()





