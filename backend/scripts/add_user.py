#!/usr/bin/env python

from argparse import ArgumentParser

from test_observer.users.add_user import add_user

if __name__ == "__main__":
    parser = ArgumentParser(
        prog="add_user",
        description="Adds a user via their launchpad email"
        " to the list of users that can review artefacts",
    )

    parser.add_argument("launchpad_email", type=str)

    args = parser.parse_args()

    add_user(args.launchpad_email)
