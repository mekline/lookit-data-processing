import os
import errno
from datetime import datetime
import pprint
import pickle
from warnings import warn
import csv

printer = pprint.PrettyPrinter(indent=4)

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


def backup_and_save(filepath, object):
    '''Pickle object and save it to filepath, backup any existing file first.

    Note that this will overwrite any other backup files that share a timestamp.'''

    # move existing file to backup/timestamp/filepath
    backup(filepath)

    # then save in intended location
    with open(filepath,'wb') as f:
        pickle.dump(object, f, protocol=2)

def backup(filepath):
    '''Back up a file if it exists.

    Note that this will overwrite any other backup files that share a timestamp.'''

    # move existing file to backup/timestamp/filepath
    if os.path.exists(filepath):
        (fileDir, fileName) = os.path.split(filepath)
        newDir = os.path.join(fileDir, 'backup', timestamp())
        make_sure_path_exists(newDir)
        os.rename(filepath, os.path.join(newDir, fileName))
        print "Backing up {} to {}".format(fileName, newDir)

def backup_and_save_dict(filepath, dictList, headerList):
    '''Save a list of dicts to a csv file, backing up existing file first.

    Note that this will overwrite any other backup files that share a timestamp.'''

    # Back up any existing coding file by the same name
    backup(filepath)

    # Finally, write the coding csv
    ofile = open(filepath, "wb")
    writer = csv.DictWriter(ofile, fieldnames=headerList, restval='', extrasaction='ignore')
    writer.writeheader()
    writer.writerows(dictList)

    ofile.close()

def flatten_dict(d):
    '''Flatten a dictionary where values may be other dictionaries

    The dictionary returned will have keys created by joining higher- to lower-level keys with dots. e.g. if the original dict d is
    {'a': {'x':3, 'y':4}, 'b':{'z':5}, 'c':{} }
    then the dict returned will be
    {'a.x':3, 'a.y': 4, 'b.z':5}

    Note that if a key is mapped to an empty dict, NO key in the returned dict is created for this key.

    Also note that values may be overwritten if there is conflicting dot notation in the input dictionary, e.g. {'a': {'x': 3}, 'a.x': 4}.
    '''
    # http://codereview.stackexchange.com/a/21035

    for k in d.keys():
        if '.' in k:
            warn('Dangerous key value included in dictionary to flatten')

    def expand(key, value):

        if isinstance(value, dict):
            return [ (key + '.' + k, v) for k, v in flatten_dict(value).items() ]
        else:
            return [ (key, value) ]

    items = [ item for k, v in d.items() for item in expand(k, v) ]

    return dict(items)

def display_unique_counts(vals):
    '''Given a list, display one line per unique value with the count'''
    uniqueVals = list(set(vals))

    for v in uniqueVals:
        print '\t{}\t{}'.format(vals.count(v), v)


