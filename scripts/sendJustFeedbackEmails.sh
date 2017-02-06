source fwenv/bin/activate
say "Also sending emails with just new feedback"
frameworkpython reminder_emails.py --study physics --emails all --feedback
