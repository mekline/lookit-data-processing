import sys
import os
import json

from mappings import MAPPINGS

import pymongo

def convert_childs(account_id, records):
    if not records or not records.count():
        return []

    ret = []

    for childs in records:
        child_ids = childs.get('child', [])
        child_names = childs.get('child_name', [])
        child_genders = childs.get('gender', [])
        child_g_ages = childs.get('weeks', [])

        if isinstance(child_ids, list):
            for i in range(len(child_ids)):
                child = {
                    'profileId': "{}.{}".format(account_id, child_ids[i]),
                    'firstName': child_names[i],
                    'birthday': None,  # TODO
                    'gestationalAgeAtBirth': child_g_ages[i],
                    'gender': child_genders[i],
                    'deleted': False,
                }
                dupes = [item for item in ret if item['profileId'] == child['profileId']]
                if dupes:
                    print "Duplicate child records found under account: {}".format(account_id)
                    print "Record:"
                    print json.dumps(child, sort_keys=True, indent=4, separators=(',', ': '))
                    print "is not being written because:"
                    print json.dumps(dupes[0], sort_keys=True, indent=4, separators=(',', ': '))
                    print "already exists"
                    continue
                ret.append(child)
        else:
            child = {
                'profileId': "{}.{}".format(account_id, child_ids),
                'firstName': child_names,
                'birthday': None,  # TODO
                'gestationalAgeAtBirth': child_g_ages,
                'gender': child_genders,
                'deleted': False,
            }
            dupes = [item for item in ret if item['profileId'] == child['profileId']]
            if dupes:
                print "Duplicate child records found under account: {}".format(account_id)
                print "Record:"
                print json.dumps(child, sort_keys=True, indent=4, separators=(',', ': '))
                print "is not being written because:"
                print json.dumps(dupes[0], sort_keys=True, indent=4, separators=(',', ': '))
                print "already exists"
                continue
            ret.append(child)

    return ret

def convert_demographic(demo):
    ret = {}
    for key, mapping in MAPPINGS.items():
        value = demo.get(key)
        if value is None:
            continue
        if isinstance(mapping, list):
            for item in mapping:
                if 'ref' in item:
                    ret[item['to']] = item['ref'][value.strip()]
                else:
                    ret[item['to']] = value
        else:
            if 'ref' in mapping:
                try:
                    ret[mapping['to']] = mapping['ref'][value.strip()]
                except Exception as e:
                    print e
                    import ipdb; ipdb.set_trace()
            else:
                ret[mapping['to']] = value
    return ret

def convert_users(db):
    ret = []
    for record in db.details.find():
        email = record.get('email_label')
        demographic = db.demographic.find_one({
            'email_label': email
        }) or {}

        childs = db.childs.find({
            'parent_id': email
        })

        demographic = convert_demographic(demographic)
        demographic['demographicsNumberOfBooks'] = None

        id = email.split('@')[0]
        attrs = dict(
            id=id,
            name=record.get('name'),
            email=email,
            emailPreferenceNextSession=True,
            emailPreferenceNewStudies=('updates' in record.get('preference', [])),
            emailPreferenceResultsPublished=('results' in record.get('preference', [])),
            profiles=convert_childs(str(id), childs)
        )
        attrs.update(demographic)
        ret.append(attrs)
    return ret

def migrate(db, outputdir):
    accounts = convert_users(db)
    profileIds = {}
    for account in accounts:
        aid = account['id']
        if aid not in profileIds:
            profileIds[aid] = 1
        else:
            count = profileIds[aid]
            account['id'] = aid + '_' + str(count)
            profileIds[aid] = profileIds[aid] + 1    
    with open(os.path.join(outputdir, 'accounts.json'), 'w') as fp:
        json.dump(accounts, fp, sort_keys=True, indent=4, separators=(',', ': '))

def main():
    try:
        inputdir = sys.argv[1]
    except IndexError:
        print "Please supply a path to the mongo backup to be restored and migrated, e.g.:"
        print "./migrate.py --in=<PATH> --out=<PATH> --dbname=<DBNAME>"
        sys.exit(1)
    try:
        outputdir = sys.argv[2]
    except IndexError:
        print "Please supply a path to the desired output directory (of the migrated JSON), e.g.:"
        print "./migrate.py --in=<PATH> --out=<PATH> --dbname=<DBNAME>"
        sys.exit(1)
    try:
        dbname = sys.argv[3]
    except IndexError:
        print "Please supply the database name of the dumped db, e.g.:"
        print "./migrate.py --in=<PATH> --out=<PATH> --dbname=<DBNAME>"
        sys.exit(1)


    client = pymongo.MongoClient('localhost', 27017)
    try:
        db = client[dbname]
    except KeyError:
        print "No database named {} found.".format(dbname)
    else:
        migrate(db, outputdir)

if __name__ == "__main__":
    main()
