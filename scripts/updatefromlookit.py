import os
from experimenter import ExperimenterClient
from utils import indent, printer
import subprocess as sp
import lookitpaths as paths
from utils import backup_and_save
import conf

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

