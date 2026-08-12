Test execution lifecycle
=========================

Test Observer is a system that receives and stores test results from external test runners. Tests are executed by the CI/CD pipeline, pytest, Jenkins, or other automation integrated into Test Observer. This page explains how tests and artefacts flow through the system.

Test execution states
----------------------

A **test execution** represents a single run of a test plan against an artefact build in a specific environment. It has a lifecycle that starts when results are first submitted and ends when the execution is marked as complete.

.. mermaid::
  :config: {"state": {"curve": "linear"}}

  stateDiagram-v2
      direction LR

      [*] --> NOT_STARTED: Created
      NOT_STARTED --> IN_PROGRESS: First result submitted
      NOT_STARTED --> ENDED_PREMATURELY: Completed without results
      IN_PROGRESS --> PASSED: All tests pass
      IN_PROGRESS --> FAILED: Any test fails
      IN_PROGRESS --> ENDED_PREMATURELY: Completion signal without pass/fail

      PASSED --> [*]
      FAILED --> [*]
      ENDED_PREMATURELY --> [*]


``NOT_STARTED``
    Initial state when an execution is created. The execution record exists but no test results have been submitted yet.

``IN_PROGRESS``
    Test results are being actively submitted. Transitions from ``NOT_STARTED`` when the first result arrives.

``PASSED``
    All submitted test results have status ``PASSED`` or ``SKIPPED``, with no ``FAILED`` results. Indicates successful test execution with no failures.

``FAILED``
    At least one test result has status ``FAILED``. The execution produced test evidence but found problems.

``ENDED_PREMATURELY``
    The execution completed without producing a clear pass/fail outcome. This occurs when:

    - Completion signals (status updates, events) indicate the job finished
    - The execution is neither ``PASSED`` nor ``FAILED`` because no results were submitted or all results were skipped.

    This state captures cases where testing was attempted but did not produce definitive outcomes, such as infrastructure failures, timeouts, or intentional skips.

``NOT_TESTED``
    The execution was intentionally skipped or not performed. Used when testing is not applicable for a particular environment or configuration. This status can be manually set outside the automated execution lifecycle shown in the state diagram above.

Artefact states
------------------

An **artefact** represents a specific version of a software package undergoing testing and review. While test executions reflect test outcomes, artefact status reflects **review decisions** about whether the package is suitable for release. 

The artefact status is determined by the combination of test execution outcomes and reviewer decisions:

- A ``FAILED`` test execution may still lead to ``APPROVED`` if failures are triaged and deemed acceptable. For example: known infrastructure issues, customer-specific prerequisites, or non-critical test failures that do not block release.
- A ``PASSED`` test execution does not guarantee ``APPROVED``. For example, reviewers may reject for non-test reasons such as security concerns, policy violations.

.. mermaid::
   :config: {"state": {"curve": "linear"}}

   stateDiagram-v2
      direction LR
      
      [*] --> UNDECIDED: Artefact created
      UNDECIDED --> APPROVED: Final environment approved (all approved)
      UNDECIDED --> MARKED_AS_FAILED: Any environment rejected

      APPROVED --> [*]
      MARKED_AS_FAILED --> [*]

Artefact status changes when reviewers submit environment-level review decisions:

``UNDECIDED``
    Default state when an artefact is created. Testing and review are in progress. The artefact awaits reviewer decisions on all required environments.

``APPROVED``
    All environment-level reviews have approved decisions. The artefact is considered suitable for release to the next stage. Approval can occur even with failed tests if issues are triaged and acceptable.

``MARKED_AS_FAILED``
    At least one environment review was explicitly rejected (``REJECTED`` decision). The artefact cannot proceed and should not be released.


Test result triaging
--------------------

**Triaging** is the process of documenting why tests failed or were skipped by linking them to tracked issues. This provides accountability and justification for approving artefacts despite test failures.

A test execution is triaged when ``FAILED`` or ``SKIPPED`` results have been investigated and have issues attached. Failed or skipped tests should be linked to issues (Jira, GitHub, Launchpad, etc.) to document known problems before artefact approval, indicating failures have been reviewed.

.. mermaid::

   flowchart TD
      Execution[Test Execution with<br/>FAILED/SKIPPED results]
      
      Execution --> Queue[Appears in triage queue]
      Queue --> Review[Reviewer investigates failures]
      Review --> Link[Reviewer links to<br/>Jira/GitHub/Launchpad]
      Link --> Triaged

      Triaged --> Auto{Auto-rerun<br/>enabled?}
      Auto -->|Yes| Rerun[Create rerun request]
      Auto -->|No| Done[Done]



Rerun requests
--------------

A **rerun request** asks for a test group — the combination of a test plan, an artefact build and an environment — to be run again. Rerun requests are created manually from the dashboard or automatically as part of triaging (see the flowchart above).

Test Observer **does not run tests**, and it does not run reruns either. Creating a rerun request only records that a rerun is wanted; it adds the request to a queue that Test Observer exposes via ``GET /v1/test-executions/reruns``. An **external test scheduler** (the same CI/CD pipeline, Jenkins, or other automation that submits results) is expected to poll this queue, run the requested test groups, and submit fresh results.

Priority
~~~~~~~~

**Priority is an attribute of a rerun request.** It is an integer between ``-1000000`` and ``1000000`` (default ``0``). The rerun queue returned by ``GET /v1/test-executions/reruns`` is ordered by priority descending, then by creation time ascending — so higher-priority requests appear first, and among equal priorities the oldest requests appear first.

Priority is **advisory metadata**. Its only guaranteed effect is the order in which Test Observer returns pending reruns. Whether a rerun with a higher priority is actually run sooner depends entirely on the external test scheduler consuming the queue: a scheduler may respect the ordering, apply its own scheduling policy, or ignore priority altogether. Set a priority to express relative urgency to your scheduler, but do not rely on Test Observer to enforce it.
