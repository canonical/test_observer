"""Initial families and stages

Revision ID: 12383cab7248
Revises: 7a9069d2ab59
Create Date: 2023-05-26 11:52:18.703471+00:00

"""
from alembic import op
from sqlalchemy.orm import Session

from test_observer.data_access.models import Family, Stage
from test_observer.data_access.models_enums import FamilyName

initial_families_and_stages = {
    FamilyName.SNAP: ["edge", "beta", "candidate", "stable"],
    FamilyName.DEB: ["proposed", "updates"],
}

# revision identifiers, used by Alembic.
revision = "12383cab7248"
down_revision = "7a9069d2ab59"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)

    for family_name, stage_names in initial_families_and_stages.items():
        family = Family(name=family_name)
        session.add(family)
        session.commit()

        stage_position = 10
        for stage_name in stage_names:
            stage = Stage(name=stage_name, family=family, position=stage_position)
            session.add(stage)
            # Increment by 10 to make it easier to rearrange stages in future
            stage_position += 10

    session.commit()


def downgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)

    families = (
        session.query(Family)
        .filter(Family.name in initial_families_and_stages.keys())
        .all()
    )

    for family in families:
        session.delete(family)

    session.commit()
