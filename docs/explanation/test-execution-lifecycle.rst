Test execution lifecycle
=========================

Test Observer is a system that receives and stores test results from external test runners. Tests are executed by the CI/CD pipeline, pytest, Jenkins, or other automation integrated into Test Observer. This page explains how tests and artefacts flow through the system.


Test execution states
----------------------

A **test execution** represents a single run of a test plan against an artefact build in a specific environment. It has a lifecycle that starts when results are first submitted and ends when the execution is marked as complete.

.. mermaid::
   :config: {"state": {"curve": "linear"}}

   stateDiagram-v2
      [*] --> NOT_STARTED: Created
      NOT_STARTED --> IN_PROGRESS: Results submitted
      IN_PROGRESS --> PASSED: All tests pass
      IN_PROGRESS --> FAILED: Any test fails
      IN_PROGRESS --> ENDED_PREMATURELY: Stopped early

      PASSED --> [*]
      FAILED --> [*]
      ENDED_PREMATURELY --> [*]

- `NOT_STARTED`: Execution created, no results yet
- `IN_PROGRESS`: Receiving test results
- `PASSED`: All tests passed
- `FAILED`: At least one test failed
- `ENDED_PREMATURELY`: Execution stopped before completion

Artefact states
------------------

An **artefact** is a specific version of a software package that goes through testing and review before approval.

.. mermaid::
   :config: {"state": {"curve": "linear"}}

   stateDiagram-v2
      [*] --> UNDECIDED: Artefact created
      UNDECIDED --> APPROVED: All reviews approved
      UNDECIDED --> MARKED_AS_FAILED: Any review rejected

      APPROVED --> [*]
      MARKED_AS_FAILED --> [*]

- `UNDECIDED`: Default state, awaiting review decisions
- `APPROVED`: Ready for release to next stage
- `MARKED_AS_FAILED`: Rejected, cannot proceed


Test result triaging
--------------------

Failed or skipped tests must be linked to issues (Jira, GitHub, Launchpad) before an artefact can be approved.

.. mermaid::

   flowchart TD
      Failed[Test Result: FAILED/SKIPPED]

      Failed --> Attached{Issue<br/>attached?}
      Attached -->|Yes| Triaged[Triaged ✓]
      Attached -->|No| Queue[Appears in triage queue]

      Queue --> Link[Reviewer links to<br/>Jira/GitHub/Launchpad]
      Link --> Triaged

      Triaged --> Auto{Auto-rerun<br/>enabled?}
      Auto -->|Yes| Rerun[Create rerun request]
      Auto -->|No| Done[Done]

A ``TestExecution`` has an ``is_triaged`` property that checks if all failed/skipped tests have attached issues.

