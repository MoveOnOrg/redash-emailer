# Redash Emailer

This Python 3.6 script fetches Redash query results and sends them via email as CSV attachment.

## Setting up your pyenv virtual environment for local development on MacOS

- You only need to run this one time:
  - Make sure you have followed the instructions on setting up your pyenv env vars:
    - <https://github.com/pyenv/pyenv?tab=readme-ov-file#b-set-up-your-shell-environment-for-pyenv>
  - Set the local python version, `pyenv local 3.12`
  - Initialize the pyenv virtualenv, `pyenv virtualenv 3.12 redash-emailer-venv`
  - Get the pyenv path: `pyenv virtualenvs`, copy the part that has the path, e.g. `3.12.11/envs/redash-emailer-venv`
  - Open the `.python-version` file and replace everything with the path copied above as stated in <https://github.com/pyenv/pyenv-virtualenv?tab=readme-ov-file#activate-virtualenv>.
  - Confirm that this worked by navigating to this project directory in your MacOS terminal.
  The virtualenv should auto-activate.
  - Run `pip install -r requirements.txt`

> [!WARNING]
> To-do: We should move secrets to AWS secrets manager instead.

- Copy `settings.py.example` to `settings.py`, fill in values with the ones stored in 1password as `redash-emailer settings.py`.
- Run `python redash_emailer.py -h` to get input options.

## Recipient

You can set the recipient with either `--to` on the command line, or `TO_ADDRESS` in `settings.py`. In either case, if the recipient value is not an email address (containing `@`), it will be assumed to be the name of a column in the Redash query results, and that column must contain email addresses. This allows more complex workflows in which the query itself determines who receives which records.

## Amazon Lambda

Copy `zappa_settings.json` from 1Password into main directory. Run `zappa update` to update code on Amazon Lambda.
