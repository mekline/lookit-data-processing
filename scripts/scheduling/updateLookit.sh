source venv/bin/activate
say "Updating Lookit version 2 studies and sending reminder emails"

now=$(date +"%m_%d_%Y")
timestamp=$(date +"%Y_%m_%d_%H_%M_%S")
mv /Users/kms/lookit-v2/scripts/logs/autoSync.out /Users/kms/lookit-v2/scripts/logs/autoSync_$timestamp.out
mv /Users/kms/lookit-v2/scripts/logs/autoSync.err /Users/kms/lookit-v2/scripts/logs/autoSync_$timestamp.err

python coding.py updateaccounts
python coding.py update --study physics
python reminder_emails.py --study physics --emails all
python coding.py fetchconsentsheet --coder Kim --study physics
python coding.py exportaccounts --study physics

python coding.py update --study politeness
python announce_politeness.py --emails all
python coding.py update --study flurps
python announce_flurps.py --emails all
python coding.py exportaccounts --study flurps
python coding.py exportaccounts --study politeness

python coding.py update --study geometry
python coding.py fetchconsentsheet --coder Kim --study geometry
python coding.py exportaccounts --study geometry

aws s3 cp /Users/kms/lookitcodingv2/coding/c7001e3a-cfc5-4054-a8e0-0f5e520950ab_Kim.csv s3://lookitgeometry/v2/csv/$now/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

aws s3 cp /Users/kms/lookitcodingv2/coding/accountsprod_c7001e3a-cfc5-4054-a8e0-0f5e520950ab.csv s3://lookitgeometry/v2/csv/$now/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

aws s3 cp /Users/kms/lookitcodingv2/coding/c7001e3a-cfc5-4054-a8e0-0f5e520950ab_Kim.csv s3://lookitgeometry/v2/csv/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

aws s3 cp /Users/kms/lookitcodingv2/coding/accountsprod_c7001e3a-cfc5-4054-a8e0-0f5e520950ab.csv s3://lookitgeometry/v2/csv/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

aws s3 sync /Users/kms/lookitcodingv2/sessions/c7001e3a-cfc5-4054-a8e0-0f5e520950ab/ s3://lookitgeometry/v2/processed/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

aws s3 cp /Users/kms/lookitcodingv2/coding/accountsprod_1e9157cd-b898-4098-9429-a599720d0c0a.csv s3://lookit-data/ --grants read=emailaddress=lisa.chalik@gmail.com full=emailaddress=lookit@mit.edu

aws s3 cp /Users/kms/lookitcodingv2/coding/accountsprod_b40b6731-2fec-4df4-a12f-d38c7be3015e.csv s3://lookit-data/ --grants read=emailaddress=ejyoon@stanford.edu full=emailaddress=lookit@mit.edu
