# Authenticate

from __future__ import print_function

import datetime
from time import time
import argparse

import os.path
import base64  # to decode message body
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.message import EmailMessage

import html2text

from llms import openai_replier

from parameters import LABELS, MAX_EMAILS, NEWER_THAN, MAX_EMAIL_LENGTH, SKIP_SUBJECT, SKIP_FROM

text_maker = html2text.HTML2Text()
text_maker.ignore_images = True
text_maker.ignore_emphasis = True

ap = argparse.ArgumentParser(
    prog='python3 email-replier.py', description='Create draft replies to emails'
)
ap.add_argument('-c', "--check", help="Check emails without replying", action='store_true')


def authenticate():

    print("Authenticating gmail")
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        return service

    except HttpError as error:
        print(f'An error occurred: {error}')


def get_mails(service, max_msgs=10, newer_than='7d', labels_ids=['UNREAD', 'INBOX']):

    max_snippet_length = 180  # snippet is ~200 chars max (not found in gmail api)
    received_emails = []

    try:
        print('Getting unread messages...')

        results = (
            service.users()
            .messages()
            .list(
                userId='me',
                labelIds=labels_ids,
                maxResults=max_msgs,
                q='newer_than:' + newer_than,
            )
            .execute()
        )

        messages_list = results.get('messages', [])

        if not messages_list:
            print('Yo have no new messages.')
            return messages_list

        print('You have', len(messages_list), 'messages')

        # Check messages ids
        # print('Message list:')
        # print(messages_list)

        # Get messages
        for msg_info in messages_list:
            email = {
                'id': None,
                'message_id': None,
                'thread_id': None,
                'mime_type': None,
                'is_text': False,
                'from': '',
                'date': '',
                'subject': '',
                'snippet': '',
                'body': '',
                'body_type': '',
                'reply': '',
            }

            email['id'] = msg_info.get('id')
            email['thread_id'] = msg_info.get('threadId')

            msg = service.users().messages().get(userId='me', id=msg_info.get('id')).execute()
            # format:  full, metadata, minimal, raw

            payload = msg.get('payload')  # dict
            email['mime_type'] = payload.get('mimeType')

            # Headers. Email info. List of dicts of the form {'name':'field', 'value':'valuex'}
            headers = payload.get('headers')

            # Parse headers of message
            for header in headers:
                if header.get('name') == 'From':
                    email['from'] = header.get('value') or None
                if header.get('name') == 'Subject':
                    email['subject'] = header.get('value') or None
                if header.get('name') == 'Date':
                    email['date'] = header.get('value') or None
                if header.get('name') == 'Message-ID':
                    email['message_id'] = header.get('value') or None

            # Content
            email['snippet'] = msg.get('snippet')  # snippet is ~200 chars max

            if len(email['snippet']) > max_snippet_length:
                # Parse for text parts
                parts = payload.get('parts')  # list
                if parts:
                    content = None
                    for p in parts:
                        if p.get('mimeType') in ['text/plain', 'text/html'] and p.get('body').get(
                            'size'
                        ):
                            content = p
                            email['body_type'] = p.get('mimeType')
                            email['is_text'] = True
                            break
                        if p.get('mimeType') in ['multipart/related', 'multipart/alternative']:
                            for sub_p in p.get('parts'):
                                if sub_p.get('mimeType') in ['text/plain', 'text/html']:
                                    content = sub_p
                                    email['body_type'] = sub_p.get('mimeType')
                                    email['is_text'] = True
                                    break

                elif email['mime_type'] in ['text/plain', 'text/html']:
                    content = payload
                    email['body_type'] = email['mime_type']
                    email['is_text'] = True

                if email['is_text']:
                    text = content.get('body').get('data')

                    if text:
                        email['body'] = base64.urlsafe_b64decode(text.encode('ASCII')).decode(
                            'utf-8'
                        )
                        # email['body'] = base64.urlsafe_b64decode(text).decode("utf-8")

                        if email['body_type'] == 'text/html':
                            email['body'] = text_maker.handle(email['body'])

                        # clean:
                        # long url tags, space, remove tail
                        email['body'] = re.sub(r'<.*?>', '', email['body'])
                        # email['body'] = email['body'].replace("&#39;", "'")

                        # email['body'] = email['body'].split('@',1)[0]
                        email['body'] = re.split(
                            'Recruitment Consultant|Candidate Consultant|T:|Tel.|Consultant',
                            email['body'],
                            1,
                        )[0]

            else:
                email['body'] = email['snippet']

            received_emails.append(email)

    except Exception as e:
        print(e)

    return received_emails


def reply_email(email):

    email['reply'] = openai_replier(email['body'])

    return email


def reply_emails(received_emails):

    replied_emails = []

    print("Replying emails...")
    for email in received_emails:
        email = reply_email(email)
        replied_emails.append(email)

    return replied_emails


def create_draft(service, email):

    if email.get('reply'):

        message = EmailMessage()

        message.set_content(email.get('reply'))
        message['To'] = email.get('from')
        message['Subject'] = email.get('subject')
        message['In-Reply-To'] = email.get('message_id')

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'message': {'raw': encoded_message, 'threadId': email.get('thread_id')}}

        try:
            # pylint: disable=E1101
            draft = service.users().drafts().create(userId="me", body=create_message).execute()

            print(f"Draft data: {draft['message']}")

        except HttpError as error:
            print(f"An error occurred: {error}")
            draft = None

        return draft

    print("Reply is empty. Draft was no created")
    return


# Other functions


def get_mailbox_labels(service):

    try:
        # Get Labels
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        if not labels:
            print('No labels found.')
            return

        return [(label['name'], label['id']) for label in labels]

    except HttpError as error:
        print(f'An error occurred: {error}')


def mark_msg_as_read(service, msg_id):
    pass


def emaildata2string(email):

    data_string = ''
    data_string += f"Subject: {email.get('subject')}\n"
    data_string += f"From: {email.get('from')}\n"
    data_string += f"mimeType: {email.get('mime_type')}\n"
    data_string += f"BodyType: {email.get('body_type')}\n"
    data_string += f"Snipppet: {email.get('snippet')}\n"
    data_string += "Body:\n"
    data_string += email.get('body') + "\n"
    data_string += f"Email length (characters): {len(email.get('body'))}\n"
    data_string += "Reply:\n"
    data_string += email.get('reply') + "\n"
    data_string += (80 * "-") + "\n"

    return data_string


def fetch_messages():

    iso_date = datetime.datetime.today().replace(microsecond=0).isoformat().replace(':', '')

    service = authenticate()
    # print(get_mailbox_labels(service))

    print(f"\nGetting emails newer than {NEWER_THAN} with labels {LABELS} ...")
    received_emails = get_mails(
        service, max_msgs=MAX_EMAILS, newer_than=NEWER_THAN, labels_ids=LABELS
    )
    print(80 * '-')

    if received_emails:

        for mail in received_emails:
            print("Subject:", mail.get('subject'))
            print("From:", mail.get('from'))
            print("Snipppet:", mail.get('snippet'))
            print("Email length (characters):", len(mail.get('body')))
            print(80 * '-')

        with open('logs/' + iso_date + '-received-mails.txt', 'w') as f:

            for email in received_emails:
                f.write(emaildata2string(email))


def main():

    iso_date = datetime.datetime.today().replace(microsecond=0).isoformat().replace(':', '')

    service = authenticate()

    print(f"\nGetting emails newer than {NEWER_THAN} with labels {LABELS} ...")
    emails = get_mails(service, max_msgs=MAX_EMAILS, newer_than=NEWER_THAN, labels_ids=LABELS)

    if emails:

        f = open('logs/' + iso_date + '-reply-log.txt', 'w')

        for email in emails:

            start = time()

            print(80 * '-')
            print(f"\nProcessing email: {email['subject']}, from {email['from']} ...")

            if len(email.get('body')) > MAX_EMAIL_LENGTH:
                print(f"Email too long ({len(email.get('body'))} characters), skipping reply...")
                continue

            if set(email.get('subject').split()) & SKIP_SUBJECT:
                print("Skipping email due to subject")
                continue

            if email.get('from') in SKIP_FROM:
                print("Sender in skip list, skipping reply...")
                continue

            reply_email(email)

            print("\nMaking Draft...")
            _ = create_draft(service, email)

            print("\nTime elapsed:", round(time() - start, 1), "seconds")

            f.write(emaildata2string(email))

        f.close()


if __name__ == '__main__':

    args = ap.parse_args()

    if args.check:
        fetch_messages()
    else:
        main()
