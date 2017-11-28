source fwenv/bin/activate
say "Updating Lookit studies and sending reminder emails"

now=$(date +"%m_%d_%Y")
timestamp=$(date +"%Y_%m_%d_%H_%M_%S")
mv /Users/kms/lookit/scripts/logs/autoSync.out /Users/kms/lookit/scripts/logs/autoSync_$timestamp.out

frameworkpython coding.py update --study physics
frameworkpython reminder_emails.py --study physics --emails all
frameworkpython coding.py fetchconsentsheet --coder Kim --study physics
frameworkpython coding.py updateaccounts --study physics


