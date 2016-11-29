source venv/bin/activate
say "Updating Lookit physics study and sending reminder emails"
python coding.py update --study physics
python reminder_emails.py --study physics --emails all
