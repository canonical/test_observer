Release management
==================

For managing releases in Test Observer, two permanent branches exist: ``stable`` and ``main``. Another branch that will be part of this explanation is ``stable-hotfix``.

``stable`` is where the latest stable release code is. ``main`` is where the edge code is.

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

Hotfixes
--------

Hotfixes can be implemented to quickly solve and deploy an issue in ``stable``. They skip the candidate process and are created from the ``stable`` branch to a ``stable-hotfix`` branch. They are directly tagged to a ``stable-hotfix`` release.

The hotfix should also be implemented for ``main`` so that it is included in future candidates.

The release for a hotfix should be tagged with ``stable-hotfix/a.b.c-d`` with release notes explaining the issue and how it was fixed. The version follows ``stable``.
