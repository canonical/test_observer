# Copyright 2025 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
from sqlalchemy.orm import Session

from test_observer.controllers.issues.attachment_rules_logic import (
    apply_test_result_attachment_rules,
    query_matching_test_result_attachment_rules,
)
from test_observer.data_access.models import (
    IssueTestResultAttachmentRule,
    IssueTestResultAttachmentRuleExecutionMetadata,
)
from test_observer.data_access.models_enums import FamilyName
from tests.data_generator import DataGenerator

params_query_matching_test_result_attachment_rules: list[dict] = [
    {
        "label": "no_rules",
        "attachment_rules": [],
    },
    {
        "label": "no_criteria",
        "attachment_rules": [
            (True, {}),
        ],
    },
    {
        "label": "disabled",
        "attachment_rules": [
            (False, {"enabled": False}),
        ],
    },
    {
        "label": "match_family",
        "attachment_rules": [
            (True, {"families": [FamilyName.snap]}),
            (True, {"families": [FamilyName.snap, FamilyName.charm]}),
            (False, {"families": [FamilyName.charm]}),
        ],
    },
    {
        "label": "match_environment_name",
        "attachment_rules": [
            (True, {"environment_names": ["laptop"]}),
            (True, {"environment_names": ["laptop", "desktop"]}),
            (False, {"environment_names": ["desktop"]}),
        ],
    },
    {
        "label": "match_test_case_name",
        "attachment_rules": [
            (True, {"test_case_names": ["camera/detect"]}),
            (True, {"test_case_names": ["camera/detect", "camera/poweroff"]}),
            (False, {"test_case_names": ["camera/poweroff"]}),
        ],
    },
    {
        "label": "match_template_id",
        "attachment_rules": [
            (True, {"template_ids": ["some-template"]}),
            (True, {"template_ids": ["some-template", "other-template"]}),
            (False, {"template_ids": ["other-template"]}),
        ],
    },
    {
        "label": "match_execution_metadata",
        "attachment_rules": [
            (True, {"execution_metadata": [("category1", "value1")]}),
            (
                True,
                {
                    "execution_metadata": [
                        ("category1", "value1"),
                        ("category2", "value1"),
                    ]
                },
            ),
            (
                True,
                {
                    "execution_metadata": [
                        ("category1", "value1"),
                        ("category1", "value3"),
                    ]
                },
            ),
            (False, {"execution_metadata": [("category1", "value3")]}),
            (
                False,
                {
                    "execution_metadata": [
                        ("category1", "value1"),
                        ("category2", "value3"),
                    ]
                },
            ),
            (False, {"execution_metadata": [("category3", "value1")]}),
        ],
    },
    {
        "label": "match_mixed",
        "attachment_rules": [
            (
                True,
                {
                    "families": [FamilyName.snap],
                    "execution_metadata": [("category1", "value1")],
                },
            ),
            (
                False,
                {
                    "families": [FamilyName.charm],
                    "execution_metadata": [("category3", "value1")],
                },
            ),
            (
                False,
                {
                    "families": [FamilyName.snap],
                    "execution_metadata": [("category3", "value1")],
                },
            ),
            (
                False,
                {
                    "families": [FamilyName.charm],
                    "execution_metadata": [("category1", "value1")],
                },
            ),
        ],
    },
]


@pytest.mark.parametrize(
    "params",
    params_query_matching_test_result_attachment_rules,
    ids=[params["label"] for params in params_query_matching_test_result_attachment_rules],
)
def test_query_matching_test_result_attachment_rules(
    params: dict,
    generator: DataGenerator,
    db_session: Session,
):
    artefact = generator.gen_artefact()
    artefact_build = generator.gen_artefact_build(artefact=artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build=artefact_build,
        environment=environment,
        execution_metadata={
            "category1": [
                "value1",
                "value2",
            ],
            "category2": [
                "value1",
                "value2",
            ],
        },
    )
    test_case = generator.gen_test_case(template_id="some-template")
    test_result = generator.gen_test_result(test_case=test_case, test_execution=test_execution)
    issue = generator.gen_issue()

    expected_matched_rules = set()
    for match_expected, spec in params["attachment_rules"]:
        attachment_rule = IssueTestResultAttachmentRule(
            issue=issue,
            enabled=spec.get("enabled", True),
            test_results=spec.get("test_results", []),
            families=spec.get("families", []),
            environment_names=spec.get("environment_names", []),
            test_case_names=spec.get("test_case_names", []),
            template_ids=spec.get("template_ids", []),
            execution_metadata=[
                IssueTestResultAttachmentRuleExecutionMetadata(category=category, value=value)
                for category, value in spec.get("execution_metadata", [])
            ],
        )
        db_session.add(attachment_rule)
        db_session.commit()
        if match_expected:
            expected_matched_rules.add(attachment_rule.id)

    attachment_rules_stmt = query_matching_test_result_attachment_rules(test_result)
    attachment_rules = db_session.scalars(attachment_rules_stmt).all()

    assert {rule.id for rule in attachment_rules} == expected_matched_rules


def test_apply_test_result_attachment_rules(
    generator: DataGenerator,
    db_session: Session,
):
    artefact = generator.gen_artefact()
    artefact_build = generator.gen_artefact_build(artefact=artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(artefact_build=artefact_build, environment=environment)
    test_case = generator.gen_test_case(template_id="some-template")
    test_result = generator.gen_test_result(test_case=test_case, test_execution=test_execution)
    issue_1 = generator.gen_issue(key="1")
    issue_2 = generator.gen_issue(key="2")
    issue_3 = generator.gen_issue(key="3")

    attachment_rules = [
        IssueTestResultAttachmentRule(issue=issue_1, template_ids=["some-template"]),
        IssueTestResultAttachmentRule(issue=issue_2, families=[FamilyName.charm]),
        IssueTestResultAttachmentRule(issue=issue_3, families=[FamilyName.snap]),
        IssueTestResultAttachmentRule(issue=issue_1, families=[FamilyName.snap]),
    ]
    for attachment_rule in attachment_rules:
        db_session.add(attachment_rule)
    db_session.commit()

    apply_test_result_attachment_rules(db_session, test_result)

    assert {(attachment.issue_id, attachment.attachment_rule_id) for attachment in test_result.issue_attachments} == {
        (issue_1.id, attachment_rules[0].id),
        (issue_3.id, attachment_rules[2].id),
    }
