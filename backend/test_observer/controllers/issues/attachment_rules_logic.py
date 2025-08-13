# Copyright (C) 2023 Canonical Ltd.
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


from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy import (
    select,
    or_,
    func,
    any_,
    exists,
    and_,
    type_coerce,
    Enum,
    ColumnElement,
)
from sqlalchemy.dialects.postgresql import insert
from collections.abc import Sequence

from test_observer.data_access.models import (
    TestResult,
    IssueTestResultAttachmentRule,
    IssueTestResultAttachmentRuleExecutionMetadata,
    TestExecutionMetadata,
    TestExecution,
    IssueTestResultAttachment,
)
from test_observer.data_access.models_enums import FamilyName


def _empty_or_contains(
    array: InstrumentedAttribute, value: object
) -> ColumnElement[bool]:
    return or_(
        func.cardinality(array) == 0,
        value == any_(array),
    )


def query_matching_test_result_attachment_rules(
    db: Session, test_result: TestResult
) -> Sequence[IssueTestResultAttachmentRule]:
    stmt = select(IssueTestResultAttachmentRule)

    # Only fetch enabled rules
    stmt = stmt.where(IssueTestResultAttachmentRule.enabled)

    # Filter families
    stmt = stmt.where(
        _empty_or_contains(
            IssueTestResultAttachmentRule.families,
            type_coerce(
                test_result.test_execution.artefact_build.artefact.family,
                Enum(FamilyName),
            ),
        )
    )

    # Filter environment_names
    stmt = stmt.where(
        _empty_or_contains(
            IssueTestResultAttachmentRule.environment_names,
            test_result.test_execution.environment.name,
        )
    )

    # Filter test_case_names
    stmt = stmt.where(
        _empty_or_contains(
            IssueTestResultAttachmentRule.test_case_names, test_result.test_case.name
        )
    )

    # Filter template_ids
    stmt = stmt.where(
        _empty_or_contains(
            IssueTestResultAttachmentRule.template_ids,
            test_result.test_case.template_id,
        )
    )

    # Filter execution metadata
    unmatched_categories = (
        select(IssueTestResultAttachmentRuleExecutionMetadata.category)
        .outerjoin(
            TestExecutionMetadata,
            and_(
                TestExecutionMetadata.test_executions.any(
                    TestExecution.id == test_result.test_execution_id
                ),
                TestExecutionMetadata.category
                == IssueTestResultAttachmentRuleExecutionMetadata.category,
                TestExecutionMetadata.value
                == IssueTestResultAttachmentRuleExecutionMetadata.value,
            ),
        )
        .where(
            IssueTestResultAttachmentRuleExecutionMetadata.attachment_rule_id
            == IssueTestResultAttachmentRule.id
        )
        .group_by(IssueTestResultAttachmentRuleExecutionMetadata.category)
        .having(func.count(TestExecutionMetadata.value) == 0)
    )
    stmt = stmt.where(~exists(unmatched_categories))

    # Sort by first created
    stmt = stmt.order_by(IssueTestResultAttachmentRule.created_at)

    return db.scalars(stmt).all()


def apply_test_result_attachment_rules(db: Session, test_result: TestResult):
    # Fetch matching attachment rule
    attachment_rules = query_matching_test_result_attachment_rules(db, test_result)

    # Attach all issues
    if len(attachment_rules) > 0:
        db.execute(
            insert(IssueTestResultAttachment)
            .values(
                [
                    {
                        "issue_id": attachment_rule.issue_id,
                        "test_result_id": test_result.id,
                        "attachment_rule_id": attachment_rule.id,
                    }
                    for attachment_rule in attachment_rules
                ]
            )
            .on_conflict_do_nothing()
        )
