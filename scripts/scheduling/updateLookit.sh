source fwenv/bin/activate
say "Updating Lookit studies and sending reminder emails"

now=$(date +"%m_%d_%Y")
timestamp=$(date +"%Y_%m_%d_%H_%M_%S")
mv /Users/kms/lookit/scripts/logs/autoSync.out /Users/kms/lookit/scripts/logs/autoSync_$timestamp.out

frameworkpython coding.py update --study physics
frameworkpython reminder_emails.py --study physics --emails all
frameworkpython coding.py fetchconsentsheet --coder Kim --study physics
frameworkpython coding.py updateaccounts --study physics

frameworkpython coding.py update --study geometry
frameworkpython coding.py fetchconsentsheet --coder Kim --study geometry
frameworkpython coding.py updateaccounts --study geometry
frameworkpython announce_geometry.py --emails all

frameworkpython experimenter.py download session58cc039ec0d9d70097f26220s --out ~/lookitcoding/coding/geometry.json

aws s3 cp /Users/kms/lookitcoding/coding/58cc039ec0d9d70097f26220_Kim.csv s3://lookitgeometry/csv/$now/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

aws s3 cp /Users/kms/lookitcoding/coding/accountsprod_58cc039ec0d9d70097f26220.csv s3://lookitgeometry/csv/$now/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

aws s3 cp /Users/kms/lookitcoding/coding/58cc039ec0d9d70097f26220_Kim.csv s3://lookitgeometry/csv/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

aws s3 cp /Users/kms/lookitcoding/coding/geometry.json s3://lookitgeometry/csv/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

aws s3 cp /Users/kms/lookitcoding/coding/accountsprod_58cc039ec0d9d70097f26220.csv s3://lookitgeometry/csv/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

aws s3 sync /Users/kms/lookitcoding/sessions/58cc039ec0d9d70097f26220/ s3://lookitgeometry/processed/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu


