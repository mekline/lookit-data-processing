from sendgrid_client import EmailPreferences, SendGrid
from coding import *
from utils import printer
from experimenter import update_account_data
import datetime
import numpy as np
import donotsend

if __name__ == '__main__':

	# Parse command-line arguments
	parser = argparse.ArgumentParser(description='Send one-time announcement email for Lookit study')
	parser.add_argument('--emails', help='Only send emails to these addresses (enter "all" to send to all eligible)',	 action='append', default=['kimber.m.scott@gmail.com'])

	args = parser.parse_args()

	accounts = Experiment.load_account_data()

	# Date/time to use for determining ages
	td = datetime.datetime.today()
	ageRangeDays = (730, 1461)

	# Get SendGrid object & unsubscribe group for notifications
	sg = SendGrid()

	logfilename = '/Users/kms/lookit-v2/scripts/logs/sentpolitenessannouncement.txt'

	with open(logfilename) as f:
		alreadySent = f.readlines()
	alreadySent = [x.strip().encode('utf-8') for x in alreadySent]
	print "Already sent announcement to: {}".format(", ".join(alreadySent))

	logfile = open(logfilename, 'a+')

	nRecruit = 0
	nSent = 0

	politeness = Experiment('b40b6731-2fec-4df4-a12f-d38c7be3015e')
	politenessSubjects = list(set([paths.get_context_from_session(sess)['child'] for sess in politeness.sessions]))

	print "Existing subjects: {}".format(", ".join(politenessSubjects))

	# Go through accounts looking for people with birthdays in age range
	for (uname, acc) in accounts.items():

		name = acc['attributes']['nickname']
		recipient = acc['attributes']['username'].strip().encode('utf-8')

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
		recruitChildren = [child for child in recruitChildren if child['id'] not in politenessSubjects]

		# Make sure child profile not deleted
		recruitChildren = [child for child in recruitChildren if not child['deleted']]

		nRecruit += len(recruitChildren)

		if len(recruitChildren):

			if uname in donotsend.users:
				print("Skipping email for user on donotsend list: {}".format(user))
				continue

			# Generate the email message to send

			childNames = [child['given_name'].title() for child in recruitChildren]
			subject = 'New study for ' + ' and '.join(childNames) + ' on Lookit!'

			body = 'Hi ' + (name if name else uname) + ',<br><br>'
			body += "We're writing to invite " + ' and '.join(childNames) + " to participate in the new study 'Mind and Manners' on Lookit! This study for 2- through 4-year-olds looks at how kids learn what it means to be polite. <br><br> In this 15-minute study, your child will listen to short stories where people make requests, and answer questions about the characters by pointing. <br><br> To learn more or get started, visit <a href='https://lookit.mit.edu/studies/b40b6731-2fec-4df4-a12f-d38c7be3015e/' target=_blank>the study</a> on Lookit!<br><br> You'll earn a $4 Amazon gift card for participating (one gift card per child)! <br><br>Happy experimenting! <br><br>The Lookit team<br><br> P.S. Do you have any friends with kids around the same age? We'd be grateful for any help spreading the word about this study!<br><br><hr>"

			if recipient in args.emails or 'all' in args.emails:
				#print recipient

				print 'Already sent to recipient: {}'.format(
		recipient in alreadySent)

				if recipient not in alreadySent and acc['attributes']['email_new_studies']:
					print recipient
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

					if nSent > 50:
						break

	print "n in age range, not yet participated: ", nRecruit
	print "n emails actually sent (not already sent, not unsubscribed):", nSent
	logfile.close()
