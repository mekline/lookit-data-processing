import os
from experimenter import ExperimenterClient
#from sendgrid_client import SendGrid
from utils import indent, printer
import subprocess as sp
from warnings import warn
import lookitpaths as paths
from utils import backup_and_save
import conf
import pickle

def sync_S3(pull=False):
	'''Download any new or modified video files from S3.

	pull: if true, also pull videos from wowza to S3 first.

	This only gets the video files; details are not stored in the video database.'''
	if pull:
		pull_from_wowza()
		print('Pulled videos from Wowza')

	origVideos = paths.get_videolist()
	sp.check_call(['aws', 's3', 'sync', 's3://mitLookit', paths.VIDEO_DIR, '--only-show-errors', '--metadata-directive', 'COPY'])
	allVideos = paths.get_videolist()
	newVideos = list(set(allVideos)-set(origVideos))
	print "Downloaded {} videos:".format(len(newVideos))
	print(indent(printer.pformat(newVideos), 4))
	return newVideos

def pull_from_wowza():
	'''Sync wowza data with S3 so we get up-to-date data from S3'''
	thisDir = os.path.dirname(os.path.realpath(__file__))
	sp.call(['ssh', '-i', os.path.join(thisDir, 'lookit2016.pem'), 'ec2-user@lookit-streaming.mit.edu', 'aws', 's3', 'sync', '/home/ec2-user/content', 's3://mitLookit'])

### TODO: USE JSON
def update_session_data(experimentId, display=False):
	'''Get session data from the server for this experiment ID and save'''
	client = ExperimenterClient.authenticate(conf.OSF_ACCESS_TOKEN, base_url=conf.JAM_HOST, namespace=conf.JAM_NAMESPACE)
	exp = {'sessions': client.fetch_collection_records(paths.make_long_expId(experimentId))}

	backup_and_save(paths.session_filename(experimentId), exp)

	if display:
		printer.pprint(exp['sessions'])

	print "Synced session data for experiment: {}".format(experimentId)


def update_account_data():
	'''Get current account data from the server and save to the account file'''
	client = ExperimenterClient.authenticate(conf.OSF_ACCESS_TOKEN, base_url=conf.JAM_HOST, namespace=conf.JAM_NAMESPACE)
	accountData = client.fetch_collection_records('accounts')
	print('Download complete. Found {} records'.format(len(accountData)))
	allAccounts = {acc[u'id'].split('.')[-1]: acc for acc in accountData}
	backup_and_save(paths.ACCOUNT_FILENAME, allAccounts)
