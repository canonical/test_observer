from sqlalchemy import Select, select

from test_observer.data_access.models import ArtefactBuild

latest_artefact_builds = (
    select(ArtefactBuild)
    .distinct(ArtefactBuild.artefact_id, ArtefactBuild.architecture)
    .order_by(ArtefactBuild.artefact_id, ArtefactBuild.architecture)
)


def artefact_architectures(artefact_id: int) -> Select[tuple[str]]:
    return (
        select(ArtefactBuild.architecture)
        .distinct()
        .where(ArtefactBuild.id == artefact_id)
    )
