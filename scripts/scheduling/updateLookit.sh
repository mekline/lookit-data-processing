source fwenv/bin/activate
say "Updating Lookit studies and sending reminder emails"
frameworkpython coding.py update --study physics
frameworkpython reminder_emails.py --study physics --emails all
frameworkpython coding.py fetchconsentsheet --coder Kim --study physics
frameworkpython coding.py update --study geometry
frameworkpython coding.py fetchconsentsheet --coder Kim --study geometry
