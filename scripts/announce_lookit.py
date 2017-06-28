from sendgrid_client import EmailPreferences, SendGrid
from coding import *
from utils import printer
from updatefromlookit import update_account_data
import datetime
import numpy as np

if __name__ == '__main__':

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Send one-time announcement email for Lookit study')
    parser.add_argument('--emails', help='Only send emails to these addresses (enter "all" to send to all eligible)',    action='append', default=['kimber.m.scott@gmail.com'])

    args = parser.parse_args()

    # update_account_data()

    accounts = Experiment.load_account_data()

    # Date/time to use for determining ages
    td = datetime.datetime.today()

    ageRangeDays = (4.0 * 365/12, 365)

    # Check that these children DIDN'T participate in the pilot...
    pilot = Experiment('57bc591dc0d9d70055f775db')
    pilotSubjects = list(set([sess['attributes']['profileId'] for sess in pilot.sessions])) # full profile ID, e.g. kim2.zwmst

    # Get SendGrid object & unsubscribe group for notifications
    sg = SendGrid()
    groups = sg.groups()
    group = groups['newStudies']
    groupId = group['id']

    logfilename = '/Users/kms/lookit/scripts/logs/sentlookitannouncement' + datetime.datetime.today().strftime("%y%m%d%H%M%S") + '.txt'
    logfile = open(logfilename, 'w')

    nRecruit = 0

    # Go through accounts looking for people with birthdays in age range
    for (uname, acc) in accounts.items():

        name = acc['attributes']['name']
        recipient = acc['attributes']['email']
        childProfiles = [prof for prof in acc['attributes']['profiles'] if not prof['birthday'] == None]

        # Compute children's ages (deal with a few formats for birthdays)
        for (iP, prof) in enumerate(childProfiles):
            try:
                prof['ageDays'] = float((td - datetime.datetime.strptime(prof['birthday'], '%Y-%m-%dT%H:%M:%S')).total_seconds())/84600
            except ValueError:
                prof['ageDays'] = float((td - datetime.datetime.strptime(prof['birthday'], '%Y-%m-%dT%H:%M:%S.%fZ')).total_seconds())/84600
            childProfiles[iP] = prof

        # Make a list of only children in age range
        recruitChildren = [child for child in childProfiles if ageRangeDays[0] <= child['ageDays'] <= ageRangeDays[1]]

        # Also restrict to those who did NOT participate in the pilot
        recruitChildren = [child for child in recruitChildren if child['profileId'] not in pilotSubjects]

        nRecruit += len(recruitChildren)

        if len(recruitChildren):
            #print (uname, recruitChildren)

            # Generate the email message to send

            childNames = [child['firstName'].title() for child in recruitChildren]
            subject = 'New study for ' + ' and '.join(childNames) + ' on Lookit!'

            body = 'Hi ' + (name if name else uname) + ',<br><br>'
            body += "We're writing to invite " + ' and '.join(childNames) + " to participate in the new study 'Your baby the physicist' on Lookit! This study looks at infants' expectations about basic physics principles like gravity and inertia. Children between 4 and 12 months old who have not already participated in the 'Baby physics pilot' study are eligible to participate. <br><br> Sessions take about 15 minutes and involve watching pairs of videos of physical events, one on the left and on the right of your computer monitor. Your child chooses where to look--at the event that's more likely (like a ball falling down) or less likely (a ball falling up)? <br><br> Using many of these video pairs and looking for consistent trends, we should be able to build up a detailed picture of your child's beliefs about how the physical world works. This study will be one of the first to look in detail not just at infants' abilities collectively, but at individual differences in their expectations and styles of responding. <br><br>You can complete as many or as few sessions as you want with your child. Our goal--unprecedented in cognitive development research--is to observe as many participants as possible over at least 15 sessions each. If you complete all 15 sessions, we'll be able to send you a personalized report about your child's looking patterns once video coding is done!<br><br> To learn more or get started, visit <a href='https://lookit.mit.edu' target=_blank>Lookit</a>!<br><br>Happy Thanksgiving, <br><br>The Lookit team<br><br><hr>"

            print recipient
            print 'Recipient is unsubscribed from this list: {}'.format(
        recipient in sg.unsubscribes_for(group))

#             if recipient in args.emails or 'all' in args.emails:
#                 print 'send email\n\n\n'
#                 status = sg.send_email_to(
#                   recipient,
#                   subject,
#                   body,
#                   group_id=groupId
#                 )
#                 if status == 200:
#                     # Write email address to file
#                     logfile.write(recipient + '\n')

    print nRecruit
    logfile.close()





