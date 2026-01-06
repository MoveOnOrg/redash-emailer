# Redash Emailer

This script fetches Redash query results and sends them via email as CSV attachment.

## Setting up your pyenv virtual environment for local development on MacOS

- You only need to run this once for this repository on your machine:
  - Follow the steps described in our [Notion docs for setting up `pyenv` on MacOS for development here](https://www.notion.so/moveonorg/Python-Tools-d30deef8d15d47d58f66b4dc7e0e9943?source=copy_link#2cc12fe515bb8017b148d47f5b400e4b), make sure you follow step 3 (Setting up repositories with pyenv) with Python 3.12.
  - Confirm that this worked by checking that this command outputs a correct venv path `echo $VIRTUAL_ENV`
  - If the command above doesn't yield any output, then something is not configured correctly, so you will need to get help from another tech team member.
- Run `pip install -r requirements.txt`

- Additional setup required for new triggers:
  - Each query id needs a corresponding secrets manager entry is needed for the `redash-emailer` secret:
  - key: `{query number}_REDASH_QUERY_KEY`
  - value: {Redash query API key}
- See the test event in the AWS [console](https://us-west-1.console.aws.amazon.com/lambda/home?region=us-west-1#/functions/redash-emailer-prod?tab=testing).

- Run `python redash_emailer.py -h` to get input options.

## Recipient

You can set the recipient with either `--to` on the command line, or `TO_ADDRESS` in `settings.py`. In either case, if the recipient value is not an email address (containing `@`), it will be assumed to be the name of a column in the Redash query results, and that column must contain email addresses. This allows more complex workflows in which the query itself determines who receives which records.
