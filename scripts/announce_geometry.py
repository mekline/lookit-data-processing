from sendgrid_client import EmailPreferences, SendGrid
from coding import *
from utils import printer
from experimenter import update_account_data
import datetime
import numpy as np
import geometryemaildata

if __name__ == '__main__':

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Send one-time announcement email for Lookit study')
    parser.add_argument('--emails', help='Only send emails to these addresses (enter "all" to send to all eligible)',    action='append', default=['kimber.m.scott@gmail.com'])

    args = parser.parse_args()

    accounts = Experiment.load_account_data()

    # Date/time to use for determining ages
    td = datetime.datetime.today()
    ageRangeDays = (198, 229)

    # Get SendGrid object & unsubscribe group for notifications
    sg = SendGrid()

    logfilename = '/Users/kms/lookit/scripts/logs/sentgeometryannouncement.txt'

    with open(logfilename) as f:
        alreadySent = f.readlines()
    alreadySent = [x.strip() for x in alreadySent]
    print "Already sent announcement to: {}".format(", ".join(alreadySent))

    logfile = open(logfilename, 'a+')

    nRecruit = 0
    nSent = 0

    geom = Experiment('c7001e3a-cfc5-4054-a8e0-0f5e520950ab')
    geomSubjects = list(set([paths.get_context_from_session(sess)['child'] for sess in geom.sessions]))

    oldSiteSubjects = geometryemaildata.oldSiteSubjects

    print "Existing subjects: {}".format(", ".join(geomSubjects))

    # Go through accounts looking for people with birthdays in age range
    for (uname, acc) in accounts.items():

        name = acc['attributes']['nickname']
        recipient = acc['attributes']['username']

        childProfiles = []
        for (id, prof) in acc['attributes']['children'].items():
            prof['id'] = id
            # Compute children's ages (deal with a few formats for birthdays)
            if prof['birthday'] is not None:
                prof['ageDays'] = float((td - datetime.datetime.strptime(prof['birthday'], '%Y-%m-%d')).total_seconds())/84600
                childProfiles.append(prof)

        # Make a list of only children in age range
        recruitChildren = [child for child in childProfiles if ageRangeDays[0] <= child['ageDays'] <= ageRangeDays[1]]

        # Make sure they have not already participated
        recruitChildren = [child for child in recruitChildren if child['id'] not in geomSubjects and child['former_lookit_profile_id'].split('.')[0] not in oldSiteSubjects]

        nRecruit += len(recruitChildren)

        if len(recruitChildren):

            # Generate the email message to send

            childNames = [child['given_name'].title() for child in recruitChildren]
            subject = 'New study for ' + ' and '.join(childNames) + ' on Lookit!'

            body = 'Hi ' + (name if name else uname) + ',<br><br>'
            body += "We're writing to invite " + ' and '.join(childNames) + " to participate in the new study 'Baby Euclid' on Lookit! This study for 7-month-olds (6 1/2 to 7 1/2 months) looks at babies' perception of shapes: we're interested in whether infants pick up on features essential to Euclidean geometry, like relative lengths and angles, even across changes in a shape's size and orientation. <br><br> In this 10-minute study, your baby watches short videos of two changing streams of triangles, one on each side of the screen. On one side, the triangles will be changing in shape and size, and on the other side, they will be changing in size alone. We measure how long your baby looks at each of the two streams of triangles to see which changes he or she finds more noticeable and interesting.            <br><br> To learn more or get started, visit <a href='https://lookit.mit.edu/studies/58cc039ec0d9d70097f26220' target=_blank>the study</a> on Lookit!<br><br>Happy experimenting! <br><br>The Lookit team<br><br><hr>"

            if recipient in args.emails or 'all' in args.emails:
                print recipient

                print 'Already sent to recipient: {}'.format(
        recipient in alreadySent)

                if recipient not in alreadySent and acc['attributes']['email_new_studies']:

                    nSent += 1

                    print 'send email\n\n\n'
                    status = sg.send_email_to(
                      recipient,
                      subject,
                      body
                    )
                    if status == 200:
                        # Write email address to file
                        logfile.write(recipient + '\n')

    print "n in age range, not yet participated: ", nRecruit
    print "n emails actually sent (not already sent, not unsubscribed):", nSent
    logfile.close()
