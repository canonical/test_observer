# Copyright 2023 Canonical Ltd.
# All rights reserved.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Written by:
#        Nadzeya Hutsko <nadzeya.hutsko@canonical.com>
#        Omar Abou Selo <omar.selo@canonical.com>


from itertools import groupby


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from test_observer.data_access.models import Family
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.setup import get_db
from test_observer.data_access.repository import get_artefacts_by_family_name

from .models import FamilyDTO

router = APIRouter()


@router.get("/{family_name}", response_model=FamilyDTO)
def read_family(family_name: str, db: Session = Depends(get_db)):
    """Retrieve all the stages and artefacts from the family"""
    family = db.query(Family).filter(Family.name == family_name).first()
    if family is None:
        raise HTTPException(status_code=404, detail="Family not found")

    family_name_enum_value = FamilyName(family_name)
    latest_artefacts = get_artefacts_by_family_name(db, family_name_enum_value)

    stage_artefact_dict = groupby(latest_artefacts, lambda art: art.stage)

    for stage, artefacts in stage_artefact_dict:
        stage.artefacts = list(artefacts)

    family.stages = sorted(family.stages, key=lambda x: x.position)
    return family
