"""Add permissions

Revision ID: 6a8187602dcc
Revises: f0847700d32e
Create Date: 2026-04-09 13:49:52.784772+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6a8187602dcc"
down_revision = "f0847700d32e"
branch_labels = None
depends_on = None


PERMISSION_ENUM_NAME = "permission"

# Manually copied from 2026_03_23_1733-c29b4f545a9b_add_permissions_to_amrs.py
OLD_PERMISSIONS = {
    "view_user",
    "change_user",
    "view_team",
    "change_team",
    "add_application",
    "change_application",
    "view_application",
    "view_permission",
    "view_issue",
    "change_issue",
    "change_issue_attachment",
    "change_issue_attachment_bulk",
    "change_attachment_rule",
    "change_auto_rerun",
    "view_test",
    "change_test",
    "view_rerun",
    "change_rerun",
    "change_rerun_bulk",
    "view_artefact",
    "change_artefact",
    "view_environment_review",
    "change_environment_review",
    "view_report",
    "view_test_case_reported_issue",
    "change_test_case_reported_issue",
    "view_environment_reported_issue",
    "change_environment_reported_issue",
    "view_notification",
    "change_notification",
}

# Removing explicit notification permissions
# if a user/app is authenticated, it can view and clear (change) notifications
NEW_PERMISSIONS = OLD_PERMISSIONS.union({"view_sentry_debug"}).difference({"view_notification", "change_notification"})


def upgrade() -> None:
    """
    Although PostgreSQL does support adding new values to an enum type,
    it does not support removing values from an enum type,
    which is what we would need to do in the downgrade.
    As a result, we take a more symmetric approach to upgrading and downgrading,
    where we create new enum types in both cases.
    """
    # Rename the old enum to a new temporary name, so that we can create the new enum with the same name.
    op.execute(f"ALTER TYPE {PERMISSION_ENUM_NAME} RENAME TO {PERMISSION_ENUM_NAME}_old")

    # Create the new enum with the same name as the old enum.
    formatted_options = ", ".join(f"'{p}'" for p in sorted(NEW_PERMISSIONS))
    op.execute(f"CREATE TYPE {PERMISSION_ENUM_NAME} AS ENUM ({formatted_options})")

    # artefact_matching_rule comes from this migration:
    # 2026_03_23_1733-c29b4f545a9b_add_permissions_to_amrs.py
    # application and team come from this migration:
    # 2026_03_31_1410-f0847700d32e_convert_permission_to_enum.py
    columns_to_update = [
        ("application", "permissions"),
        ("artefact_matching_rule", "grant_permissions"),
        ("team", "permissions"),
    ]
    # Update existing table columns to use the new enum type
    for table_name, column_name in columns_to_update:
        # Check if a default currently exists
        # This query returns the default expression string if it exists, or None
        has_default = (
            op.get_bind()
            .execute(
                sa.text(
                    f"""
                    SELECT column_default 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    AND column_name = '{column_name}'
                    """
                )
            )
            .scalar()
        )

        if has_default:
            # We have to drop the default before altering the column type,
            # otherwise PostgreSQL will complain about being unable to cast the default value to the new enum type.
            op.execute(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} DROP DEFAULT")

        op.execute(
            f"""
            ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE {PERMISSION_ENUM_NAME}[]
            USING {column_name}::text[]::{PERMISSION_ENUM_NAME}[]
            """
        )

        if has_default:
            # Reapply the default, which is an empty array of the new enum type.
            op.execute(
                f"ALTER TABLE {table_name} ALTER COLUMN {column_name} SET DEFAULT '{{}}'::{PERMISSION_ENUM_NAME}[]"
            )

    # Drop the old enum type
    # We need to use SQL here, because otherwise the SQLAlchemy Enum object will attempt to drop the new enum,
    # since it has the same name as the old enum.
    # This will fail, since values were updated to point to the new enum.
    op.execute(f"DROP TYPE {PERMISSION_ENUM_NAME}_old")


def downgrade() -> None:
    """
    PostgreSQL does not support removing enum values,
    so one option is to just do nothing in the downgrade.
    However, for the sake of attempting to create a somewhat reversible process,
    we will rename the current enum, create the old enum, and convert the columns back to the old enum.
    """

    # Rename the current enum to a new temporary name, so that we can create the old enum with the same name.
    op.execute(f"ALTER TYPE {PERMISSION_ENUM_NAME} RENAME TO {PERMISSION_ENUM_NAME}_new")

    # Create the old enum with the same name as the current enum.
    formatted_options = ", ".join(f"'{p}'" for p in sorted(OLD_PERMISSIONS))
    op.execute(f"CREATE TYPE {PERMISSION_ENUM_NAME} AS ENUM ({formatted_options})")

    columns_to_update = [
        ("application", "permissions"),
        ("artefact_matching_rule", "grant_permissions"),
        ("team", "permissions"),
    ]

    # Update existing table columns to use the new enum type
    # However, on downgrading, we have to remove any values that are not in the old enum
    to_remove = ", ".join(f"'{p}'" for p in sorted(NEW_PERMISSIONS - OLD_PERMISSIONS))
    for table_name, column_name in columns_to_update:
        has_default = (
            op.get_bind()
            .execute(
                sa.text(
                    f"""
                    SELECT column_default 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    AND column_name = '{column_name}'
                    """
                )
            )
            .scalar()
        )

        if has_default:
            op.execute(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} DROP DEFAULT")

        # We want to remove any values that are not in the old enum
        # That is, if a row has permissions = ["view_user", "change_user", "view_basic", "view_docs"],
        # we want that row to have its permissions set to ["view_user", "change_user"]
        op.execute(
            f"""
            UPDATE {table_name} SET {column_name} = COALESCE(
                ARRAY(
                    SELECT val
                    FROM unnest({column_name}) AS val
                    WHERE val::text NOT IN ({to_remove})
                ),
                '{{}}'
            )
            WHERE {column_name}::text[] && ARRAY[{to_remove}]::text[]
            """
        )
        op.execute(
            f"""
            ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE {PERMISSION_ENUM_NAME}[]
            USING {column_name}::text[]::{PERMISSION_ENUM_NAME}[]
            """
        )

        if has_default:
            op.execute(
                f"ALTER TABLE {table_name} ALTER COLUMN {column_name} SET DEFAULT '{{}}'::{PERMISSION_ENUM_NAME}[]"
            )

    op.execute(f"DROP TYPE {PERMISSION_ENUM_NAME}_new")
