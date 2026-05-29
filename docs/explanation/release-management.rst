Release management
==================

For managing releases in Test Observer, the goal is to have a simple approach that can adapt to the volatile needs of the platform. We have two branches that never go away: ``stable`` and ``main``. Another branch that will be part of this explanation is ``stable-hotfix``.

``stable`` is where the latest stable release code is. ``main`` is where the edge code is.

Anyone with control over the ``test_observer`` repository has the authority to create and promote stable, candidates or hotfix releases.

.. mermaid::

  flowchart TD
       previous_commit("a commit") --> candidate_commit
       candidate_commit("candidate") --> another_commit
       candidate_commit --> stable
       stable("stable") --> stable_hotfix
       another_commit("another commit") --> edge
       edge("edge")
       stable_hotfix(stable-hotfix)

Versioning
----------

Versions consist of three values (major, minor, patch) and are created based on the following rules:

- Major (A.b.c): updated when there are breaking changes
- Minor (a.B.c): updated when there is new functionality in a backward-compatible manner
- Patch (a.b.C): updated when there are backward-compatible bug fixes

``stable`` has a version in the format ``stable/a.b.c``. Candidates have the format ``candidate/A.B.C-rcD``, following the stable reference's version. Hotfixes are versioned in the format ``stable-hotfix/a.b.c-d``, following the stable reference's version. The ``-rcD`` and ``-d`` suffixes are used to differentiate candidates and hotfixes from stable releases while still versioning them (e.g., applying two hotfixes to the same stable release).

Candidates
----------

Candidate tags are created from ``main`` and deployed to staging. We only ever have one candidate at a time, i.e., there are no parallel candidates.

Furthermore, ``stable`` is only ever updated from a candidate, and if there are issues with a candidate it is rejected.

To create a candidate:

- Create a tag from ``main`` with the format ``candidate/A.B.C-rcD`` and add a release note to that tag with the changes included in that candidate
- Trigger deployment to staging
- Update Charmhub with the new candidate version and link to release notes

To promote a candidate to stable:

- Update ``stable`` from a candidate tag
- Trigger deployment to production
- Update Charmhub with the new stable version and link to release notes

Hotfixes
--------

Hotfixes can be implemented to quickly solve and deploy an issue in ``stable``. They skip the candidate process and are created from the ``stable`` branch to a ``stable-hotfix`` branch. They are directly tagged to a ``stable-hotfix`` release.

The hotfix should also be implemented for ``main`` so that it is included in future candidates.

The release for a hotfix should be tagged with ``stable-hotfix/a.b.c-d`` with release notes explaining the issue and how it was fixed. The version follows ``stable``.

To create a hotfix release:

- Create a tag from the ``stable-hotfix`` branch
- Trigger deployment to production
- Update Charmhub with the new hotfix version and link to release notes
