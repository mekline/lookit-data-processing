import argparse
import sendgrid
import json
import pprint

import conf


class EmailPreferences(object):

    ASM_MAPPING = {
        'Next Session': 'nextSession',
        'New Studies': 'newStudies',
        'Results Published': 'resultsPublished',
        'Opt Out': 'optOut'
    }

    def __init__(self, nextSession, newStudies, resultsPublished):
        self.nextSession = nextSession
        self.newStudies = newStudies
        self.resultsPublished = resultsPublished


class SendGrid(object):

    def __init__(self, apikey=None, from_addr=None):
        self.sg = sendgrid.SendGridAPIClient(
            apikey=apikey or conf.SENDGRID_KEY
        )
        self.smtp = sendgrid.SendGridClient(
            apikey or conf.SENDGRID_KEY
        )
        self.from_addr = from_addr or 'Test client <test-client@foo.com>'

    def groups(self):
        res = self.sg.client.asm.groups.get()
        return {
            EmailPreferences.ASM_MAPPING[group['name']]: group
            for group in json.loads(res.response_body)
        }

    def unsubscribes_for(self, group):
        return json.loads(
            self.sg.client.asm.groups._(
                group['id']
            ).suppressions.get().response_body
        ) or []

    def unsubscribe_from(self, group, email):
        return self.batch_unsubscribe_from(group, [email])

    def batch_unsubscribe_from(self, group, emails):
        return json.loads(
            self.sg.client.asm.groups._(group['id']).suppressions.post(
                request_body={"recipient_emails": emails}
            ).response_body
        )

    def subscribe_to(self, group, email):
        self.sg.client.asm.groups._(group['id']).suppressions._(
            email
        ).delete()
        return None

    def send_email_to(self, email, subject, body, group_id=None):
        message = sendgrid.Mail()
        message.add_to(email)
        message.set_subject(subject)
        message.set_html(body)
        message.set_text(body)
        message.set_from(self.from_addr)
        if group_id:
            message.set_asm_group_id(group_id)
        status, msg = self.smtp.send(message)
        print(status, msg)


def test(recipient_email, subscribe=True, unsubscribe=False):
    sg = SendGrid()
    groups = sg.groups()
    for _, group in groups.items():
        print "Emails currently in the unsubscribe group '{}':".format(group['name'])  # noqa
        print "{}".format(', '.join(sg.unsubscribes_for(group)))
        print "-------------------"
        print "{}ubscribing {}".format('S' if not unsubscribe else 'Uns', recipient_email)  # noqa
        if not unsubscribe:
            sg.subscribe_to(group, recipient_email)
        else:
            sg.unsubscribe_from(group, recipient_email)
        print "-------------------"
        print "Emails now in the unsubscribe group:"
        print "{}".format(', '.join(sg.unsubscribes_for(group)))
        print "-------------------"
        print "Sending a test email to {} with group_id {}".format(
            recipient_email,
            group['id']
        )
        sg.send_email_to(
            recipient_email,
            'A test',
            'This is a test',
            group_id=group['id']
        )
        print "*******************"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--recipient', type=str, required=True,
                        help='A recipient email')
    parser.add_argument('-s', '--subscribe', type=bool, default=True,
                        help='Subscribe to ASM groups?')
    parser.add_argument('-u', '--unsubscribe', type=bool, default=False,
                        help='Unsubscribe from ASM groups?')
    args = parser.parse_args()
    test(args.recipient,
         subscribe=args.subscribe,
         unsubscribe=args.unsubscribe)
