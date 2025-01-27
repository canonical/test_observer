Introduction
==========================

Test Observer (TO) is a dashboard for viewing the results of tests run on different environments for a particular artefact. A user interested in testing an artefact (a deb, snap, charm or image) under different environments (particular machines or cloud setups) can use TO as means for storing, viewing and comparing results with previous runs or versions of an artefact. The last usecase is particularly useful for catching regressions. Additionally, TO provides a mechanism to assign reviewers that can look at results and mark artefacts as approved or failed to gate updates. It is important to note that TO does not run the tests itself, but provides an API with which users can report the results to.

Certification currently deploys an instance of TO that they used for reviewing Stable Release Updates (SRUs). Other teams also use this instance for their tests. You can visit the `frontend <https://test-observer.canonical.com/>`_ and view the `API docs <https://test-observer-api.canonical.com/docs>`_, although this currently requires Canonical VPN access. There's also a staging deployment of `frontend <https://test-observer-staging.canonical.com/>`_ and `API <https://test-observer-api-staging.canonical.com/docs>`_ that teams can use to test their integration.

Note that these docs may reference the online API docs which currently require Canonical's VPN to access.

.. toctree::
   :hidden:
   :maxdepth: 2

   content/how-to/index
