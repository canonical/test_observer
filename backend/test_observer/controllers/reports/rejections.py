# Copyright (C) 2025 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    ArtefactBuildEnvironmentReview,
    Environment,
)
from test_observer.data_access.models_enums import ArtefactBuildEnvironmentReviewDecision, FamilyName
from test_observer.data_access.setup import get_db

router = APIRouter()


@router.get("/rejections")
def get_rejections_report(
    start_date: datetime = Query(default=datetime.min),
    end_date: datetime = Query(default_factory=datetime.now),
    families: list[str] = Query(default=['snap', 'deb', 'charm', 'image']),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Returns a report of rejections over time, aggregated by day.
    
    Shows the count of environment review rejections for artefacts
    over the specified time period, broken down by family type.
    """
    
    # Validate families
    valid_families = [f.value for f in FamilyName if f.value in families]
    if not valid_families:
        valid_families = ['snap', 'deb', 'charm', 'image']
    
    # Query for individual rejections (not aggregated)
    # Get all rejection records with their details
    query = (
        select(
            func.date(ArtefactBuildEnvironmentReview.created_at).label('rejection_date'),
            Artefact.family.label('family'),
            Artefact.name.label('artefact_name'),
            Artefact.version.label('artefact_version'),
            Environment.name.label('environment_name'),
            ArtefactBuildEnvironmentReview.review_comment.label('review_comment'),
            ArtefactBuildEnvironmentReview.created_at.label('review_timestamp')
        )
        .select_from(ArtefactBuildEnvironmentReview)
        .join(ArtefactBuild, ArtefactBuildEnvironmentReview.artefact_build_id == ArtefactBuild.id)
        .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
        .join(Environment, ArtefactBuildEnvironmentReview.environment_id == Environment.id)
        .where(
            and_(
                ArtefactBuildEnvironmentReview.created_at >= start_date,
                ArtefactBuildEnvironmentReview.created_at <= end_date,
                Artefact.family.in_(valid_families),
                # Check if REJECTED is in the review_decision array
                ArtefactBuildEnvironmentReview.review_decision.contains([ArtefactBuildEnvironmentReviewDecision.REJECTED])
            )
        )
        .order_by(ArtefactBuildEnvironmentReview.created_at.desc())
    )
    
    results = db.execute(query).fetchall()
    
    # Aggregate data by date and family
    daily_aggregates = {}
    rejection_details = []
    
    for row in results:
        date_str = row.rejection_date.isoformat()
        family = row.family
        
        # Track individual rejection details
        rejection_details.append({
            'date': date_str,
            'timestamp': row.review_timestamp.isoformat(),
            'family': family,
            'artefact_name': row.artefact_name,
            'artefact_version': row.artefact_version,
            'environment_name': row.environment_name,
            'review_comment': row.review_comment or '',  # Handle None values
        })
        
        # Aggregate counts by date and family
        if date_str not in daily_aggregates:
            daily_aggregates[date_str] = {
                'date': date_str,
                'total_rejections': 0,
                'by_family': {}
            }
        
        if family not in daily_aggregates[date_str]['by_family']:
            daily_aggregates[date_str]['by_family'][family] = 0
            
        daily_aggregates[date_str]['by_family'][family] += 1
        daily_aggregates[date_str]['total_rejections'] += 1
    
    # Convert to list and sort by date
    time_series = sorted(daily_aggregates.values(), key=lambda x: x['date'])
    
    # Calculate summary statistics
    total_rejections = len(rejection_details)
    family_totals = {}
    for detail in rejection_details:
        family = detail['family']
        if family not in family_totals:
            family_totals[family] = 0
        family_totals[family] += 1
    
    # Fill in missing dates with zero counts for continuity
    if time_series:
        start_date_obj = datetime.fromisoformat(start_date.isoformat().split('T')[0])
        end_date_obj = datetime.fromisoformat(end_date.isoformat().split('T')[0])
        
        # Create a complete date range
        complete_series = []
        current_date = start_date_obj
        existing_dates = {item['date']: item for item in time_series}
        
        while current_date <= end_date_obj:
            date_str = current_date.isoformat().split('T')[0]
            if date_str in existing_dates:
                complete_series.append(existing_dates[date_str])
            else:
                complete_series.append({
                    'date': date_str,
                    'total_rejections': 0,
                    'by_family': {}
                })
            current_date += timedelta(days=1)
        
        time_series = complete_series
    
    return {
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'total_rejections': total_rejections,
        'family_totals': family_totals,
        'time_series': time_series,
        'rejection_details': rejection_details,
        'families_included': valid_families,
    }


@router.get("/rejections/summary")
def get_rejections_summary(
    start_date: datetime = Query(default=datetime.min),
    end_date: datetime = Query(default_factory=datetime.now),
    families: list[str] = Query(default=['snap', 'deb', 'charm', 'image']),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Returns a summary of rejections with top rejected artefacts and environments.
    """
    
    # Validate families
    valid_families = [f.value for f in FamilyName if f.value in families]
    if not valid_families:
        valid_families = ['snap', 'deb', 'charm', 'image']
    
    # Query for top rejected artefacts
    artefacts_query = (
        select(
            Artefact.name.label('artefact_name'),
            Artefact.family.label('family'),
            func.count(ArtefactBuildEnvironmentReview.id).label('rejection_count')
        )
        .select_from(ArtefactBuildEnvironmentReview)
        .join(ArtefactBuild, ArtefactBuildEnvironmentReview.artefact_build_id == ArtefactBuild.id)
        .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
        .where(
            and_(
                ArtefactBuildEnvironmentReview.created_at >= start_date,
                ArtefactBuildEnvironmentReview.created_at <= end_date,
                Artefact.family.in_(valid_families),
                ArtefactBuildEnvironmentReview.review_decision.contains([ArtefactBuildEnvironmentReviewDecision.REJECTED])
            )
        )
        .group_by(Artefact.name, Artefact.family)
        .order_by(func.count(ArtefactBuildEnvironmentReview.id).desc())
        .limit(10)
    )
    
    # Query for top rejecting environments
    environments_query = (
        select(
            Environment.name.label('environment_name'),
            func.count(ArtefactBuildEnvironmentReview.id).label('rejection_count')
        )
        .select_from(ArtefactBuildEnvironmentReview)
        .join(ArtefactBuild, ArtefactBuildEnvironmentReview.artefact_build_id == ArtefactBuild.id)
        .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
        .join(Environment, ArtefactBuildEnvironmentReview.environment_id == Environment.id)
        .where(
            and_(
                ArtefactBuildEnvironmentReview.created_at >= start_date,
                ArtefactBuildEnvironmentReview.created_at <= end_date,
                Artefact.family.in_(valid_families),
                ArtefactBuildEnvironmentReview.review_decision.contains([ArtefactBuildEnvironmentReviewDecision.REJECTED])
            )
        )
        .group_by(Environment.name)
        .order_by(func.count(ArtefactBuildEnvironmentReview.id).desc())
        .limit(10)
    )
    
    artefacts_result = db.execute(artefacts_query).fetchall()
    environments_result = db.execute(environments_query).fetchall()
    
    top_rejected_artefacts = [
        {
            'artefact_name': row.artefact_name,
            'family': row.family,
            'rejection_count': row.rejection_count
        }
        for row in artefacts_result
    ]
    
    top_rejecting_environments = [
        {
            'environment_name': row.environment_name,
            'rejection_count': row.rejection_count
        }
        for row in environments_result
    ]
    
    return {
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'top_rejected_artefacts': top_rejected_artefacts,
        'top_rejecting_environments': top_rejecting_environments,
        'families_included': valid_families,
    }