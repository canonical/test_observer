Reviewer assignment
===================

Test Observer automatically assigns reviewers to artefacts and environments based on configurable rules. This document explains how the assignment process works for both artefacts and individual environments.

Overview
--------

Reviewer assignment happens in two stages:

1. **Artefact-level assignment**: When a test execution starts, reviewers are assigned to the overall artefact based on matching rules
2. **Environment-level assignment**: Once artefact reviewers are assigned, they are distributed across the artefact's environments for granular review

The assignment process is triggered when a test execution is started with the ``needs_assignment`` flag set to ``true``.

Artefact matching rules
-----------------------

Teams can be configured with **artefact matching rules** that define which artefacts they are responsible for reviewing. These rules specify criteria based on the artefact's characteristics.

Rule structure
~~~~~~~~~~~~~~

Each matching rule consists of:

* **family** (required): The artefact family (snap, deb, charm, or image)
* **stage** (optional): The release stage (e.g., beta, edge, proposed)
* **track** (optional): The artefact track (e.g., "22" for core22 snap)
* **branch** (optional): The git branch or PPA name

Rule matching specificity
~~~~~~~~~~~~~~~~~~~~~~~~~

When multiple rules match an artefact, Test Observer selects the **most specific** rule:

1. Rules are scored based on the number of non-empty optional fields (stage, track, branch)
2. Only rules with the highest score are considered
3. If multiple rules have the same specificity, all matching rules are used

**Example**: For a snap artefact with ``family=snap, stage=beta, track=22``:

* Rule A: ``family=snap`` (score: 0)
* Rule B: ``family=snap, stage=beta`` (score: 1)
* Rule C: ``family=snap, stage=beta, track=22`` (score: 2)

Rule C would be selected as it's the most specific.

Artefact reviewer assignment
-----------------------------

When a test execution starts with ``needs_assignment=true``, the following process occurs:

Step 1: Find matching rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The system queries for all rules matching the artefact's characteristics.

Step 2: Select most specific rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Rules are sorted by specificity (number of non-empty criteria), and only the most specific rules are retained.

Step 3: Get candidate reviewers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All users who are members of teams associated with the selected rules become candidate reviewers.

Step 4: Calculate reviewer count
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The number of reviewers needed is based on the number of environments (test executions) for the artefact. The constant ``ENVIRONMENTS_PER_REVIEWER`` determines how many environments each reviewer should handle on average.

Step 5: Randomly select reviewers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Reviewers are randomly selected from the candidate pool, up to a limit of :math:`\min(\lceil \frac{\text{total\_environments}}{\text{ENVIRONMENTS\_PER\_REVIEWER}} \rceil, \text{available\_users})`. Existing reviewers are not removed, and no more reviewers are added than available candidates.

This ensures:

* At least 1 reviewer is assigned if candidates exist
* No more reviewers are assigned than available candidates
* Existing reviewers are not removed

Environment reviewer assignment
-------------------------------

Once artefact-level reviewers are assigned, they are distributed across the artefact's environments for per-environment review.

Distribution algorithm
~~~~~~~~~~~~~~~~~~~~~~

The goal is to distribute environments evenly across all artefact reviewers:

1. **Count existing assignments**: Tally how many environments each reviewer is already assigned to
2. **Sort reviewers**: Order reviewers by their current assignment count (ascending)
3. **Calculate target**: Determine how many environments each reviewer should review: :math:`\lceil \frac{\text{total\_environments}}{\text{total\_reviewers}} \rceil`
4. **Round-robin assignment**: Iterate through environments and assign the reviewer with the fewest current assignments

Special case: Single reviewer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When there's only one reviewer assigned to the artefact, all environment-level assignments are cleared. This allows for less visual pollution in the UI and notifications.

Manual reviewer management
--------------------------

Reviewers can also be manually assigned or changed through a PATCH endpoint. Refer to the API documentation for details.

When reviewers are manually updated:

* The artefact's reviewer list is replaced with the specified users
* Environment assignments are recalculated using the same distribution algorithm
