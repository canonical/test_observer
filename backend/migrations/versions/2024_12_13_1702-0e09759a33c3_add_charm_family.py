"""Add charm family

Revision ID: 0e09759a33c3
Revises: 4c2e5946358c
Create Date: 2024-12-13 17:02:14.136283+00:00

"""
from alembic import op
import sqlalchemy as sa

from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.models import Family, Stage

new_families = {
    FamilyName.CHARM: ["edge", "beta", "candidate", "stable"],
}


# revision identifiers, used by Alembic.
revision = "0e09759a33c3"
down_revision = "4c2e5946358c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    session = sa.orm.Session(bind=conn)

    for family, stages in new_families.items():
        # Create family
        new_family = Family(name=family)

        # Add stages
        stage_position = 10
        new_family.stages = []
        for stage in stages:
            new_family.stages.append(Stage(name=stage, position=stage_position))
            stage_position += 10

        # Add family
        session.add(new_family)

    session.commit()


def downgrade() -> None:
    conn = op.get_bind()
    session = sa.orm.Session(bind=conn)

    # Delete each family, stage deletes on cascade
    for family in new_families:
        family = session.query(Family).filter_by(name=family).first()
        session.delete(family)

    session.commit()
