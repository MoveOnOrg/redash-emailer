# Redash Emailer

This Python 3 script fetches Redash query results and sends them via email as CSV attachment.

## Getting started

* Within a Python 3 environment, run `pip install -r requirements`.
* Copy `settings.py.example` to `settings.py`, fill in values.
* Run `python redash_emailer.py -h` to get input options.

## Recipient

You can set the recipient with either `--to` on the command line, or `TO_ADDRESS` in `settings.py`. In either case, if the recipient value is not an email address (containing `@`), it will be assumed to be the name of a column in the Redash query results, and that column must contain email addresses. This allows more complex workflows in which the query itself determines who receives which records.
