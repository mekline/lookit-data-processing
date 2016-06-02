import os
import errno
from datetime import datetime

def make_sure_path_exists(path):
	'''Make this directory if it doesn't already exist.'''
	try:
		os.makedirs(path)
		return 1
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise
		return 0

def indent(lines, amount, ch=' '):
	'''http://stackoverflow.com/a/8348914'''
	padding = amount * ch
	return padding + ('\n'+padding).join(lines.split('\n'))


def timestamp(micro=False):
    today = datetime.today()
    if micro:
    	return today.strftime("%y%m%d%H%M%S%f")
    else:
		return today.strftime("%y%m%d%H%M%S")
