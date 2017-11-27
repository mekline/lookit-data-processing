source fwenv/bin/activate
say "Updating Lookit version 2 studies and sending reminder emails"

now=$(date +"%m_%d_%Y")
timestamp=$(date +"%Y_%m_%d_%H_%M_%S")
mv /Users/kms/lookit/scripts/logs/autoSync.out /Users/kms/lookit/scripts/logs/autoSync_$timestamp.out

frameworkpython coding.py updateaccounts
frameworkpython coding.py update --study physics
frameworkpython reminder_emails.py --study physics --emails all
frameworkpython coding.py fetchconsentsheet --coder Kim --study physics
frameworkpython coding.py exportaccounts --study physics

frameworkpython coding.py update --study geometry
frameworkpython coding.py fetchconsentsheet --coder Kim --study geometry
frameworkpython coding.py exportaccounts --study geometry
frameworkpython announce_geometry.py --emails all

aws s3 cp /Users/kms/lookitcodingmultilab/coding/c7001e3a-cfc5-4054-a8e0-0f5e520950ab_Kim.csv s3://lookitgeometry/v2/csv/$now/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

aws s3 cp /Users/kms/lookitcodingmultilab/coding/accountsprod_c7001e3a-cfc5-4054-a8e0-0f5e520950ab.csv s3://lookitgeometry/v2/csv/$now/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

aws s3 cp /Users/kms/lookitcodingmultilab/coding/c7001e3a-cfc5-4054-a8e0-0f5e520950ab_Kim.csv s3://lookitgeometry/v2/csv/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

aws s3 cp /Users/kms/lookitcodingmultilab/coding/accountsprod_c7001e3a-cfc5-4054-a8e0-0f5e520950ab.csv s3://lookitgeometry/v2/csv/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

aws s3 sync /Users/kms/lookitcodingmultilab/sessions/c7001e3a-cfc5-4054-a8e0-0f5e520950ab/ s3://lookitgeometry/v2/processed/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu
