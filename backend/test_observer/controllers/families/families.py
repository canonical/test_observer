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

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from test_observer.data_access.models import Family
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

    latest_artefacts = get_artefacts_by_family_name(db, family_name, latest_only=True)

    stage_artefact_dict = {stage.id: [] for stage in family.stages}
    for artefact in latest_artefacts:
        stage_artefact_dict[artefact.stage_id].append(artefact)

    for stage in family.stages:
        stage.artefacts = stage_artefact_dict[stage.id]

    family.stages = sorted(family.stages, key=lambda x: x.position)
    return family
