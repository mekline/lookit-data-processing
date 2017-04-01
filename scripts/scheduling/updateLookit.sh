source fwenv/bin/activate
say "Updating Lookit physics study and sending reminder emails"
frameworkpython coding.py update --study physics
frameworkpython reminder_emails.py --study physics --emails all
frameworkpython coding.py fetchconsentsheet --coder Kim --study physics
frameworkpython experimenter.py download session58cc039ec0d9d70097f26220s --out geometry.json
