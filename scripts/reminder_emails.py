from sendgrid_client import EmailPreferences, SendGrid
from coding import *
from utils import printer
from updatefromlookit import update_account_data
import datetime
import numpy as np

def get_username(profileId):
	return profileId.split('.')[0]

def get_email(username):
	return exp.accounts[username]['attributes']['email']


def getFeedbackToSend(allSessions, child):

	# Get list of feedback that's been given on any sessions
	allFeedback = [ {'sessionId': sess['id'],
				   'feedback': sess['attributes']['feedback'],
				   'sessDate': datetime.datetime.strftime(datetime.datetime.strptime(sess['meta']['created-on'], '%Y-%m-%dT%H:%M:%S.%f'), '%B %d'),
				   'progress': len([segment for segment in sess['attributes']['expData'].keys() if 'pref-phys-videos' in segment])} \
				  for sess in allSessions if len(sess['attributes']['feedback'])]

	# But only send feedback that hasn't been sent in previous emails
	feedbackToSend = [f for f in allFeedback if not any([f['sessionId'] in e['feedbackKeys'] for e in exp.email.get(child, [])])]

	return feedbackToSend

def generate_email(allSessions, child, message, nCompleted, justFeedback=False):
	feedbackToSend = getFeedbackToSend(allSessions, child)

	# Get username, email address, & names to use in email generation
	participant = get_username(child)
	acc =  exp.accounts[participant]
	name = acc['attributes']['name']
	childProfiles = acc['attributes']['profiles']
	childName = [prof['firstName'] for prof in childProfiles if prof['profileId'] == child][0]

	# Generate email text to send
	body = 'Hi ' + (name if name else participant) + ',<br><br>'
	if justFeedback:
		body += message + "<br> "
	else:
		body += message + "This study will be one of the first to look in detail not just at infants' abilities collectively, but at individual differences in their expectations and styles of responding. But to do that, we need families to keep coming back so we can gather enough data from each child.<br><br>Our goal--unprecedented in cognitive development research--is to observe as many participants as possible over at least " + str(idealSessions) + " sessions each. Will you and " + childName + " <a href='https://lookit.mit.edu' target=_blank>come back to Lookit</a> to help out? We're ready if you are, and you can participate any time that's convenient for you!<br><br> "

	if len(feedbackToSend):
		body += "Here's some new feedback from the research team on your recent sessions: "
	for feedback in feedbackToSend:
		body += '	 ' + feedback['sessDate'] + ' ('
		if feedback['progress'] >= 24:
			body += 'complete): '
		else:
			body += str(feedback['progress']) + ' of 24 videos): '
		body += '"' + feedback['feedback'] + '"<br><br>'

	body += 'Our records indicate that you have already completed ' + str(nCompleted) + ' of the 15 sessions'
	if (idealSessions+1)/2 < nCompleted < (idealSessions - 4):
		body += ' (more than halfway done)!'
	elif (idealSessions - 4) <= nCompleted < idealSessions:
		body += ' (so close)!'
	elif nCompleted >= idealSessions:
	    body += ' (all done)!'
	else:
		body += '!'

	if nCompleted >= idealSessions:
		body += ' Thank you so much for all the time you have put in. We will send a personalized report about ' + childName + "'s looking patterns once video coding is ready!<br><br>--The Lookit team<br><br><hr>"
	else:
	    body += ' Thank you for all the time you have already put in. If you complete all ' + str(idealSessions) + ' sessions, we will be able to send a personalized report about ' + childName + "'s looking patterns once video coding is ready.<br><br>--The Lookit team<br><br><hr>"
	return (body, feedbackToSend)

# Email timing
emailsScheduled = {
#	  'tried2': {
#		  'success': False,
#		  'days': 2,
#		  'subject': '',
#		  'message': "It's been a few days since you tried to participate!"},
#	  'tried7': {
#		  'success': False,
#		  'days': 7,
#		  'subject': '',
#		  'message': "Last week you tried to participate!"},
	'started2': {
		'success': True,
		'days': 2,
		'subject': 'Ready for another "Your baby the physicist" session?',
		'message': "Thank you so much for participating in the study 'Your baby the physicist' on Lookit a few days ago with your child! "},
	'started4': {
		'success': True,
		'days': 4,
		'subject': "Ready for another 'Your baby the physicist' session?",
		'message': "Thank you so much for participating in the study 'Your baby the physicist' on Lookit this week with your child! "},
	'started7': {
		'success': True,
		'days': 7,
		'subject': "It's been a week since your last 'Your baby the physicist' session - ready to come back?",
		'message': "Thank you so much for participating in the study 'Your baby the physicist' on Lookit last week with your child! "},
	'started14': {
		'success': True,
		'days': 14,
		'subject': "It's been a few weeks since your last 'Your baby the physicist' session - ready to come back?",
		'message': "Thank you so much for participating in the study 'Your baby the physicist' on Lookit with your child! "}}

idealSessions = 15

if __name__ == '__main__':

	# Parse command-line arguments
	parser = argparse.ArgumentParser(description='Send reminder emails for a Lookit study')
	parser.add_argument('--study', help='Study ID')
	parser.add_argument('--feedback', action='store_true')
	parser.add_argument('--emails', help='Only send emails to these addresses (enter "all" to send to all eligible)',	 action='append', default=['kimber.m.scott@gmail.com'])

	args = parser.parse_args()
	study = paths.studyNicknames.get(args.study, args.study)


	update_account_data()
	exp = Experiment(study)
	exp.update_session_data()

	# Get list of all participants
	children = list(set([sess['attributes']['profileId'] for sess in exp.sessions['sessions']])) # full profile ID, e.g. kim2.zwmst

	print("Sending reminder emails. All accounts participating in this study:")
	print(", ".join(list(set([get_username(child) for child in children]))))

	# Get SendGrid object & unsubscribe group for notifications
	sg = SendGrid()
	groups = sg.groups()
	group = groups['nextSession']
	groupId = group['id']

	# Date/time to use for determining whether to send email yet
	td = datetime.datetime.today()

	for child in children:

		print "***********	" + child

		# Get list of all sessions completed by this child
		allSessions = [sess for sess in exp.sessions['sessions'] if sess['attributes']['profileId'] == child]

		# Sort by time completed
		allSessions = sorted(allSessions, key=lambda sess:datetime.datetime.strptime(sess['meta']['created-on'], '%Y-%m-%dT%H:%M:%S.%f'))

		# Figure out how many "real" sessions to count & when last was.

		# 1. Require at least one pref-phys-videos segment
		theseSessions = [sess for sess in allSessions if any(['pref-phys-videos' in segment for segment in sess['attributes']['expData'].keys()])]

		# 2. Don't include sessions within 8 hrs of a previous session
		anyTooClose = True
		while anyTooClose:
			sessDatetimes = [datetime.datetime.strptime(sess['meta']['created-on'], '%Y-%m-%dT%H:%M:%S.%f') for sess in theseSessions]
			daysSinceSession = [ float((td - sd).total_seconds())/86400 for sd in sessDatetimes]

			dayDiffs = np.subtract(daysSinceSession[:-1], daysSinceSession[1:])
			tooClose = [i for i, diff in enumerate(dayDiffs) if diff < 1./3]
			anyTooClose = len(tooClose) > 0

			if anyTooClose:
				del theseSessions[tooClose[0] + 1]

		# A. Has only unsuccessfully tried to participate, FIRST trial was N days ago...
		anySuccess = len(theseSessions) > 0
		if not anySuccess:
			firstSessionDate = datetime.datetime.strptime(allSessions[0]['meta']['created-on'], '%Y-%m-%dT%H:%M:%S.%f')
			sincePrev = float((td - firstSessionDate).total_seconds())/86400

		# B. Has successfully participated at least once; LAST successful trial was N days ago...
		else:
			sincePrev = daysSinceSession[-1]

		# Has it been long enough to send each scheduled email?
		eligible = sorted([(emailName, emailDesc) for (emailName, emailDesc) in emailsScheduled.items() if sincePrev > emailDesc['days'] and anySuccess == emailDesc['success']], key=lambda e:e[1]['days'])
		# Make sure subject has participated and NOT completed the study!
		sendEmail = len(eligible) > 0 and len(theseSessions) < idealSessions

		# Also send an email if we	have feedback to send, even if it hasn't been long enough to trigger a reminder
		feedbackToSend = getFeedbackToSend(allSessions, child)
		justFeedback = not sendEmail and len(feedbackToSend)
		if justFeedback and args.feedback:
			eligible = [('thanks', {
				'success': True,
				'days': 0,
				'subject': "Thanks for participating in the 'Your baby the physicist' study on Lookit!",
				'message': "Thank you so much for participating in the study 'Your baby the physicist' on Lookit with your child! "})]
			sendEmail = True

		# Go ahead and send the email!
		if sendEmail:
			(emailName, emailDesc) = eligible[-1] # send most-recently triggered
			message = emailDesc['message']

			# Have we already sent this reminder to this child?
			alreadySent = emailName in [e['emailName'] for e in exp.email.get(child, [])]
			recipient = get_email(get_username(child))

			if (not alreadySent) or emailName == 'thanks':

				(body, feedbackToSend) = generate_email(allSessions, child, message, len(theseSessions), justFeedback=justFeedback)

				if recipient in args.emails or 'all' in args.emails:
					print "Actually sending email:"
					print (recipient, body)
					status = sg.send_email_to(
					recipient,
					emailDesc['subject'],
					body,
					group_id=groupId
				)
				if status == 200:
					# Record in list of emails sent to this child
					emailRecord = {'emailName': emailName,
								   'message': emailDesc['message'],
								   'dateSent': td,
								   'daysPastToSend': emailDesc['days'],
								   'actualDaysPast': sincePrev,
								   'success': emailDesc['success'],
								   'feedbackKeys': [f['sessionId'] for f in feedbackToSend]}
					if child in exp.email.keys():
						exp.email[child].append(emailRecord)
					else:
						exp.email[child] = [emailRecord]
					backup_and_save(paths.email_filename(study), exp.email)

			if not anySuccess:
				print "Has never successfully participated; first session was {} days ago.".format(sincePrev)
			else:
				print "Has successfully participated {} times; last session was {} days ago.".format(len(theseSessions), sincePrev)

			print 'Recipient is unsubscribed from this list: {}'.format(
				recipient in sg.unsubscribes_for(group))

			if sendEmail:
				print 'Time to send email ({})'.format(emailName)
				print "Already sent: {}".format(alreadySent)
			else:
				print 'No email to send at this time'
