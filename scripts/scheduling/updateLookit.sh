source fwenv/bin/activate
say "Updating Lookit studies and sending reminder emails"

frameworkpython coding.py update --study physics
frameworkpython reminder_emails.py --study physics --emails all
frameworkpython coding.py fetchconsentsheet --coder Kim --study physics

frameworkpython coding.py update --study geometry
frameworkpython coding.py fetchconsentsheet --coder Kim --study geometry
frameworkpython announce_geometry.py --emails all

now=$(date +"%m_%d_%Y")

aws s3 cp /Users/kms/lookitcoding/coding/58cc039ec0d9d70097f26220_Kim.csv s3://lookitgeometry/csv/$now/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

aws s3 cp /Users/kms/lookitcoding/coding/accountsprod.csv s3://lookitgeometry/csv/$now/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

aws s3 cp /Users/kms/lookitcoding/coding/58cc039ec0d9d70097f26220_Kim.csv s3://lookitgeometry/csv/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

aws s3 cp /Users/kms/lookitcoding/coding/accountsprod.csv s3://lookitgeometry/csv/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

aws s3 sync /Users/kms/lookitcoding/sessions/58cc039ec0d9d70097f26220/ s3://lookitgeometry/processed/ --grants read=emailaddress=babylab2@g.harvard.edu full=emailaddress=lookit@mit.edu

