Glossary
========

Here is a list of terms used by Test Observer (TO) and what they mean.

Artefact
--------

An artefact is the thing under test, for instance a particular snap or image. An artefact has a name, a version, a family and a stage. Artefacts also have other attributes that are specific to their families (e.g. track is specific to snaps and charms).

Family
------

The type of an artefact. TO currently supports snaps, debs, charms and images.

Stage
-----

The level of risk of this artefact. This property is dependant on the family. Specifically:

* snaps and charms can be one of edge, beta, candidate and stable
* debs can be proposed or updates
* images can be pending or current

Environment
-----------

The architecture and name of what the artefact was tested on. In most cases this is some physical machine. But can be more complicated.

Test Plan
---------

The name of a particular grouping of tests. This is useful if you want to logically partition the tests you have, or if multiple teams are running tests on the same artefact and environment. 

Test Execution
--------------

An execution of a test plan on an artefact under a particular environment. It can contain many test results.

Test Result
-----------

Includes the name and status (PASSED, FAILED, or SKIPPED) of a test. Additionally, it optionally can have logs and other useful bits of information.

Rerun request
-------------

A request to run a test plan on an artefact build under a particular environment again. Test Observer does not run reruns itself; it stores the request in a queue that an external test scheduler polls to run the tests and submit new results. See :doc:`test-execution-lifecycle`.

Priority
--------

An attribute of a rerun request. An integer between -1000000 and 1000000 (default 0) that orders the rerun queue returned by Test Observer (higher first, then oldest first). Priority is advisory: it only affects the order in which pending reruns are returned. Whether it influences when a rerun actually runs is up to the external test scheduler, which may or may not honour it.
