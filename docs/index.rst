Test Observer
=============

Test Observer (TO) is a dashboard for viewing the results of tests run on different environments for a particular artefact. It provides APIs for storing test results, a web dashboard for viewing and comparing results, and a review workflow for gating releases.

A user interested in testing an artefact (a deb, snap, charm or image) under different environments (particular machines or cloud setups) can use TO as means for storing, viewing and comparing results with previous runs or versions of an artefact. The last use case is particularly useful for catching regressions.

Additionally, TO provides a mechanism to assign reviewers that can look at results and mark artefacts as approved or failed to gate updates. It is important to note that TO does not run the tests itself, but provides an API with which users can report the results to.


.. toctree::
   :hidden:
   :maxdepth: 2

   how-to/index
   explanation/index


---------

In this documentation
---------------------

* **Submitting tests**: :doc:`Authenticate <how-to/authenticate>` • :doc:`Submit a test <how-to/submit-a-test>`
* **Reviewing tests**: :doc:`Triage test results <how-to/triage-test-results>`
* **Key concepts**: :doc:`explanation/glossary`

---------

How this documentation is organised
------------------------------------

This documentation follows the `Diátaxis documentation framework <https://diataxis.fr/>`_, which organizes content into four distinct types:

* **Tutorials** take you step-by-step through submitting your first test results and using the review workflow. 
* **How-to guides** provide practical instructions for specific tasks. They assume basic familiarity with Test Observer and get straight to solving your problem.
* **Reference** provides technical descriptions of APIs, data models, configuration options, and permissions. Use this when you need to look up exact specifications.
* **Explanation** discusses concepts, architecture, and design decisions. Read this to understand how Test Observer works and why it works that way.

---------

Project and community
---------------------

Test Observer is developed by Canonical and used across multiple teams for test result tracking and release gating. It's an open source project that warmly welcomes community contributions, suggestions, fixes and constructive feedback.

Deployments
~~~~~~~~~~~

Ubuntu's public Test Observer instance is available at:

* https://tests.ubuntu.com/


The following instances are deployed for Canonical to review Stable Release Updates (SRUs), Charm testing, and other internal testing purposes. These instances require Canonical VPN access:

* `Production instance <https://test-observer.canonical.com/>`_ • `Production API <https://test-observer-api.canonical.com/docs>`_
* `Staging instance <https://test-observer-staging.canonical.com/>`_ • `Staging API <https://test-observer-api-staging.canonical.com/docs>`_

Get involved
~~~~~~~~~~~~

* `Contribute <https://github.com/canonical/test_observer>`_
* `Report issues <https://github.com/canonical/test_observer/issues>`_


Governance and policies
~~~~~~~~~~~~~~~~~~~~~~~~

* `Ubuntu Code of conduct`_
