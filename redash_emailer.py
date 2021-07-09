import csv
import io
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import os
import smtplib
import sys


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(BASE_DIR, 'settings.py')):
    import settings
else:
    settings = {}

class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

def get_redash_results_for_query(domain, query_id, query_key):
    query_url = '%s/api/queries/%s' % (domain, query_id)
    return requests.get(query_url + '/results.json',
                           params={'api_key': query_key}).json()

def split_rows_by_column(rows, column):
    split_rows = {}
    for record in rows:
        key = record.get(column, '')
        if not split_rows.get(key, False):
            split_rows[key] = []
        split_rows[key].append(record)
    return split_rows

def main(args):
    results = get_redash_results_for_query(args.domain,
                                           args.query_id,
                                           args.query_key)
    data = results.get('query_result', {}).get('data', {})
    rows = data.get('rows', [])

    # Order columns same way as it's returned in the Redash query
    cols = [col['friendly_name'] for col in data.get('columns', [])]
    ordered_rows = []
    for row in rows:
        new_row = {}
        for col in cols:
            new_row[col] = row[col]
        ordered_rows.append(new_row)
    rows = ordered_rows

    if '@' in args.to_address:
        rows_by_recipient = {args.to_address: rows}
    else:
        rows_by_recipient = split_rows_by_column(rows, args.to_address)

    server = smtplib.SMTP(args.smtp_host, args.smtp_port)
    server.ehlo()
    server.starttls()
    server.login(args.smtp_login, args.smtp_password)

    filename = 'query_%s_results.csv' % args.query_id

    for recipient, rows in rows_by_recipient.items():
        msg = MIMEMultipart()
        msg['Subject'] = args.subject
        msg['From'] = args.from_address
        msg['To'] = recipient
        msg.attach(MIMEText(args.body, 'plain'))
        csv_file = io.StringIO()
        csv_writer = csv.writer(csv_file, quoting=csv.QUOTE_NONNUMERIC)
        keys = list(rows[0].keys())
        csv_writer.writerow(keys)
        for row in rows:
            csv_writer.writerow([row[key] for key in keys])
        csv_attachment = MIMEBase('application', 'octet-stream')
        csv_attachment.set_payload(csv_file.getvalue())
        encoders.encode_base64(csv_attachment)
        csv_attachment.add_header('Content-Disposition', 'attachment',
                                  filename=filename)
        msg.attach(csv_attachment)
        server.sendmail(args.from_address, [x.strip() for x in msg['To'].split(',')], msg.as_string())

    server.quit()

    return True

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Send Redash results via Email')
    parser.add_argument('--domain', dest='domain', help='Redash instance domain name', default=getattr(settings, 'REDASH_DOMAIN', False))
    parser.add_argument('--query_id', dest='query_id', help='Redash query ID', default=getattr(settings, 'REDASH_QUERY_ID', False))
    parser.add_argument('--query_key', dest='query_key', help='Redash query key', default=getattr(settings, 'REDASH_QUERY_KEY', False))
    parser.add_argument('--to', dest='to_address', help='Recipeint email addresses (comma separated) or column name containing email addresses', default=getattr(settings, 'TO_ADDRESS', False))
    parser.add_argument('--from', dest='from_address', help='Sender email addresses', default=getattr(settings, 'FROM_ADDRESS', False))
    parser.add_argument('--subject', dest='subject', help='Email subject', default=getattr(settings, 'EMAIL_SUBJECT', 'Query results CSV'))
    parser.add_argument('--body', dest='body', help='Email body', default=getattr(settings, 'EMAIL_BODY', 'See attached CSV.'))
    parser.add_argument('--smtp_host', dest='smtp_host', help='SMTP host', default=getattr(settings, 'SMTP_HOST', 'localhost'))
    parser.add_argument('--smtp_login', dest='smtp_login', help='SMTP login', default=getattr(settings, 'SMTP_LOGIN', ''))
    parser.add_argument('--smtp_password', dest='smtp_password', help='SMTP login', default=getattr(settings, 'SMTP_PASSWORD', ''))
    parser.add_argument('--smtp_port', dest='smtp_port', help='SMTP login', default=getattr(settings, 'SMTP_PORT', 587))

    args = parser.parse_args()
    args.smtp_port = int(args.smtp_port)

    required_text = 'required as either arguments or settings.py.'

    required_inputs = True

    if not args.domain:
        print('Redash domain %s' % required_text)
        required_inputs = False
    if not args.query_id:
        print('Redash query ID %s' % required_text)
        required_inputs = False
    if not args.query_key:
        print('Redash query key %s' % required_text)
        required_inputs = False
    if not args.to_address:
        print('Recipeint email addresses %s' % required_text)
        required_inputs = False
    if not args.from_address:
        print('Sender email address %s' % required_text)
        required_inputs = False

    if required_inputs:
        main(args)

def aws_lambda(event, context):

    if not event.get('domain', False):
        event['domain'] = getattr(settings, 'REDASH_DOMAIN', False)
    if not event.get('query_id', False):
        event['query_id'] = getattr(settings, 'REDASH_QUERY_ID', False)
    if not event.get('query_key', False):
        event['query_key'] = getattr(settings, 'REDASH_QUERY_KEY', False)
    if not event.get('to_address', False):
        event['to_address'] = getattr(settings, 'TO_ADDRESS', False)
    if not event.get('from_address', False):
        event['from_address'] = getattr(settings, 'FROM_ADDRESS', False)
    if not event.get('subject', False):
        event['subject'] = getattr(settings, 'EMAIL_SUBJECT', False)
    if not event.get('body', False):
        event['body'] = getattr(settings, 'EMAIL_BODY', False)
    if not event.get('smtp_host', False):
        event['smtp_host'] = getattr(settings, 'SMTP_HOST', False)
    if not event.get('smtp_login', False):
        event['smtp_login'] = getattr(settings, 'SMTP_LOGIN', False)
    if not event.get('smtp_password', False):
        event['smtp_password'] = getattr(settings, 'SMTP_PASSWORD', False)
    if not event.get('smtp_port', False):
        event['smtp_port'] = getattr(settings, 'SMTP_PORT', False)

    args = Struct(**event)
    return main(args)
