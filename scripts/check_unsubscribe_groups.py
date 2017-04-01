from sendgrid_client import EmailPreferences, SendGrid
import argparse

if __name__ == '__main__':

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='List SendGrid unsubscribe groups for an email address')
    parser.add_argument('--email', help='email address to look up', required=True)

    args = parser.parse_args()

    # Get SendGrid object & unsubscribe group for notifications
    sg = SendGrid()

    print 'Email: {}'.format(args.email)

    for (groupName, group) in sg.groups().items():
        print 'Recipient is unsubscribed from {} list: {}'.format(
            groupName, args.email in sg.unsubscribes_for(group))
