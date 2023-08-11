"""Initial data models

Revision ID: 7a9069d2ab59
Revises:
Create Date: 2023-05-26 11:51:06.722382+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "7a9069d2ab59"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "environment",
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_environment_name"), "environment", ["name"], unique=True)
    op.create_table(
        "family",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_family_name"), "family", ["name"], unique=True)
    op.create_table(
        "stage",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["family_id"],
            ["family.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_stage_name"), "stage", ["name"], unique=False)
    op.create_table(
        "artefact",
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("source", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("stage_id", sa.Integer(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("Approved", "Marked as Failed", name="artefact_status_enum"),
            nullable=True,
        ),
        sa.Column("is_archived", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["stage_id"],
            ["stage.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "version", "source", name="unique_artefact"),
    )
    op.create_index(op.f("ix_artefact_name"), "artefact", ["name"], unique=False)
    op.create_table(
        "artefact_build",
        sa.Column("architecture", sa.String(length=100), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=True),
        sa.Column("artefact_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["artefact_id"],
            ["artefact.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("artefact_id", "architecture", "revision"),
    )
    op.create_index(
        op.f("ix_artefact_build_architecture"),
        "artefact_build",
        ["architecture"],
        unique=False,
    )
    op.create_table(
        "test_execution",
        sa.Column("jenkins_link", sa.String(length=200), nullable=True),
        sa.Column("c3_link", sa.String(length=200), nullable=True),
        sa.Column("artefact_build_id", sa.Integer(), nullable=False),
        sa.Column("environment_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "Not Started",
                "In Progress",
                "Passed",
                "Failed",
                "Not Tested",
                name="test_status_enum",
            ),
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["artefact_build_id"],
            ["artefact_build.id"],
        ),
        sa.ForeignKeyConstraint(
            ["environment_id"],
            ["environment.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("artefact_build_id", "environment_id"),
    )


def downgrade() -> None:
    op.drop_table("test_execution")
    op.drop_index(op.f("ix_artefact_build_architecture"), table_name="artefact_build")
    op.drop_table("artefact_build")
    op.drop_index(op.f("ix_artefact_name"), table_name="artefact")
    op.drop_table("artefact")
    op.drop_index(op.f("ix_stage_name"), table_name="stage")
    op.drop_table("stage")
    op.drop_index(op.f("ix_family_name"), table_name="family")
    op.drop_table("family")
    op.drop_index(op.f("ix_environment_name"), table_name="environment")
    op.drop_table("environment")
    op.execute("DROP TYPE IF EXISTS artefact_status_enum")
    op.execute("DROP TYPE IF EXISTS test_status_enum")
