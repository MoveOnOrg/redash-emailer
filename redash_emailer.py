import csv
import io
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import requests
from pywell.secrets_manager import get_secret
import os
import smtplib

logger = logging.getLogger()
logger.setLevel("INFO")


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
    body_text = args.body
    if len(rows) == 0:
        body_text = body_text + '\n No data was returned; skipping attachment.'

    for recipient, rows in rows_by_recipient.items():
        msg = MIMEMultipart()
        msg['Subject'] = args.subject
        msg['From'] = args.from_address
        msg['To'] = recipient
        msg.attach(MIMEText(body_text, 'plain'))
        if len(rows) > 0:
            csv_file = io.StringIO()
            csv_writer = csv.DictWriter(csv_file, rows[0].keys(), quoting=csv.QUOTE_NONNUMERIC)
            csv_writer.writeheader()
            csv_writer.writerows(rows)
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

    parser = argparse.ArgumentParser(description="Send Redash results via Email")
    parser.add_argument(
        "--event_name",
        dest="event_name",
        help="Unique name triggering this run, useful for logging",
        default="CLI event",
    )
    parser.add_argument(
        "--query_id",
        dest="query_id",
        help="Redash query ID",
        default=getattr(settings, "REDASH_QUERY_ID", False),
    )
    parser.add_argument(
        "--to",
        dest="to_address",
        help="Recipeint email addresses (comma separated) or column name containing email addresses",
        default=getattr(settings, "TO_ADDRESS", False),
    )
    parser.add_argument(
        "--from",
        dest="from_address",
        help="Sender email addresses",
        default=getattr(settings, "FROM_ADDRESS", False),
    )
    parser.add_argument(
        "--subject",
        dest="subject",
        help="Email subject",
        default=getattr(settings, "EMAIL_SUBJECT", "Query results CSV"),
    )
    parser.add_argument(
        "--body",
        dest="body",
        help="Email body",
        default=getattr(settings, "EMAIL_BODY", "See attached CSV."),
    )

    args = parser.parse_args()

    # secrets
    secrets = get_secret("redash-emailer")
    secrets["domain"] = secrets.get("REDASH_DOMAIN", False)
    secrets["smtp_host"] = secrets.get("SMTP_HOST", False)
    secrets["smtp_login"] = secrets.get("SMTP_LOGIN", False)
    secrets["smtp_password"] = secrets.get("SMTP_PASSWORD", False)
    secrets["smtp_port"] = secrets.get("SMTP_PORT", False)
    secrets["query_key"] = secrets.get(
        f"{args.get('query_id')}_REDASH_QUERY_KEY", False
    )

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
    args = event.get("kwargs")

    # non-secrets
    if not args.get("event_name", False):
        args["event_name"] = getattr(settings, "EVENT_NAME", False)
    if not args.get("query_id", False):
        args["query_id"] = getattr(settings, "REDASH_QUERY_ID", False)
    if not args.get("to_address", False):
        args["to_address"] = getattr(settings, "TO_ADDRESS", False)
    if not args.get("from_address", False):
        args["from_address"] = getattr(settings, "FROM_ADDRESS", False)
    if not args.get("subject", False):
        args["subject"] = getattr(settings, "EMAIL_SUBJECT", False)
    if not args.get("body", False):
        args["body"] = getattr(settings, "EMAIL_BODY", False)

    secrets = get_secret("redash-emailer")

    # secrets
    args["domain"] = secrets.get("REDASH_DOMAIN", False)
    args["smtp_host"] = secrets.get("SMTP_HOST", False)
    args["smtp_login"] = secrets.get("SMTP_LOGIN", False)
    args["smtp_password"] = secrets.get("SMTP_PASSWORD", False)
    args["smtp_port"] = secrets.get("SMTP_PORT", False)
    args["query_key"] = secrets.get(f"{args.get('query_id')}_REDASH_QUERY_KEY", False)

    app_struct = Struct(**args)

    logger.info(
        "Started with query_id: %s, event_name: %s ",
        args["query_id"],
        args["event_name"],
    )
    return main(app_struct)
