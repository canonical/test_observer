from argparse import ArgumentParser

from test_observer.users.change_assignee import change_assignee

if __name__ == "__main__":
    parser = ArgumentParser(
        prog="change_assignee",
        description="Changes the user assigned to review a particular artefact",
    )

    parser.add_argument("artefact_id", type=int)
    parser.add_argument("user_id", type=int)

    args = parser.parse_args()

    change_assignee(args.artefact_id, args.user_id)
