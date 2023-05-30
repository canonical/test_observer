"""populate initial data

Revision ID: 572a80b4473c
Revises: 1dc24581b4f4
Create Date: 2023-05-19 08:32:55.157515+00:00

"""
from alembic import op
from sqlalchemy.orm import Session

from test_observer.data_access.models import Family, Stage
from test_observer.data_access.models_enums import FamilyName


# revision identifiers, used by Alembic.
revision = "572a80b4473c"
down_revision = "1dc24581b4f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)

    # initial families and stages
    families_and_stages = {
        FamilyName.SNAP: ["edge", "beta", "candidate", "stable"],
        FamilyName.DEB: ["proposed", "updates"],
        FamilyName.IMAGE: [
            "lunar",
            "kinetic",
            "jammy",
            "edge",
            "beta",
            "candidate",
            "stable",
            "bionic",
            "focal",
            "released",
            "appliances",
        ],
    }

    for family_name, stage_names in families_and_stages.items():
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
    pass
