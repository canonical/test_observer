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
    exists,
    and_,
    ColumnElement,
    Select,
    literal,
    cast,
)
from sqlalchemy.dialects.postgresql import insert, ENUM

from test_observer.data_access.models import (
    TestResult,
    IssueTestResultAttachmentRule,
    IssueTestResultAttachmentRuleExecutionMetadata,
    TestExecutionMetadata,
    TestExecution,
    IssueTestResultAttachment,
)
from test_observer.data_access.models_enums import TestResultStatus


def _array_empty_or_contains(
    array: InstrumentedAttribute, value: ColumnElement
) -> ColumnElement[bool]:
    return or_(
        func.cardinality(array) == 0,
        array.any(value),
    )


def _filter_by_execution_metadata(
    stmt: Select[tuple[IssueTestResultAttachmentRule]],
    test_result: TestResult,
) -> Select[tuple[IssueTestResultAttachmentRule]]:
    # Step 1: Build join condition for TestExecutionMetadata
    # We want to match each attachment rule's metadata requirements to the actual
    # metadata present in the test execution.
    # This join condition ensures that only metadata for the current test execution,
    # with matching category and value, is considered.
    join_condition = and_(
        TestExecutionMetadata.test_executions.any(
            TestExecution.id == test_result.test_execution_id
        ),
        TestExecutionMetadata.category
        == IssueTestResultAttachmentRuleExecutionMetadata.category,
        TestExecutionMetadata.value
        == IssueTestResultAttachmentRuleExecutionMetadata.value,
    )

    # Step 2: Build the unmatched_categories subquery
    # For each attachment rule, we need to identify categories that are required by
    # the rule but do not exist (or do not have a matching value) in the
    # test execution's metadata.
    # This subquery finds (rule_id, category) pairs for unfulfilled metadata.
    unmatched_categories_query = select(
        IssueTestResultAttachmentRuleExecutionMetadata.attachment_rule_id,
        IssueTestResultAttachmentRuleExecutionMetadata.category,
    )
    unmatched_categories_query = unmatched_categories_query.outerjoin(
        TestExecutionMetadata,
        join_condition,
    )
    unmatched_categories_query = unmatched_categories_query.group_by(
        IssueTestResultAttachmentRuleExecutionMetadata.attachment_rule_id,
        IssueTestResultAttachmentRuleExecutionMetadata.category,
    )
    unmatched_categories_query = unmatched_categories_query.having(
        func.count(TestExecutionMetadata.value) == 0
    )
    unmatched_categories = unmatched_categories_query.subquery()

    # Step 3: Exclude rules with unmatched categories
    # If any required category for a rule is not matched by the test execution's
    # metadata, that rule should not apply.
    # This exclusion ensures that only rules for which all required categories are
    # satisfied are kept.
    exclusion_condition = ~exists(
        select(1)
        .select_from(unmatched_categories)
        .where(
            unmatched_categories.c.attachment_rule_id
            == IssueTestResultAttachmentRule.id
        )
    )
    stmt = stmt.where(exclusion_condition)

    # Step 4: Return the filtered statement
    return stmt


def query_matching_test_result_attachment_rules(
    test_result: TestResult,
) -> Select[tuple[IssueTestResultAttachmentRule]]:
    stmt = select(IssueTestResultAttachmentRule)

    # Only fetch enabled rules
    stmt = stmt.where(IssueTestResultAttachmentRule.enabled)

    # Filter families
    stmt = stmt.where(
        _array_empty_or_contains(
            IssueTestResultAttachmentRule.families,
            literal(test_result.test_execution.artefact_build.artefact.family),
        )
    )

    # Filter environment_names
    stmt = stmt.where(
        _array_empty_or_contains(
            IssueTestResultAttachmentRule.environment_names,
            literal(test_result.test_execution.environment.name),
        )
    )

    # Filter test_case_names
    stmt = stmt.where(
        _array_empty_or_contains(
            IssueTestResultAttachmentRule.test_case_names,
            literal(test_result.test_case.name),
        )
    )

    # Filter template_ids
    stmt = stmt.where(
        _array_empty_or_contains(
            IssueTestResultAttachmentRule.template_ids,
            literal(test_result.test_case.template_id),
        )
    )

    # Filter test result status
    stmt = stmt.where(
        _array_empty_or_contains(
            IssueTestResultAttachmentRule.test_result_statuses,
            cast(literal(test_result.status.value), ENUM(
                TestResultStatus, 
                name="testresultstatus"
            )),
        )
    )

    # Filter execution metadata
    stmt = _filter_by_execution_metadata(stmt, test_result)

    return stmt


def apply_test_result_attachment_rules(db: Session, test_result: TestResult):
    # Fetch matching attachment rule
    attachment_rules_stmt = query_matching_test_result_attachment_rules(test_result)

    # Apply attachment rules based on creation
    attachment_rules_stmt = attachment_rules_stmt.order_by(
        IssueTestResultAttachmentRule.id
    )

    # Create a subquery
    attachment_rules_subquery = attachment_rules_stmt.subquery()

    # Create insertion statement using subquery
    insert_stmt = (
        insert(IssueTestResultAttachment)
        .from_select(
            ["issue_id", "attachment_rule_id", "test_result_id"],
            select(
                attachment_rules_subquery.c.issue_id,
                attachment_rules_subquery.c.id,
                literal(test_result.id),
            ),
        )
        .on_conflict_do_nothing()
    )

    db.execute(insert_stmt)
