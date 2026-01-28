Start your first test execution
===============================

Test Observer is a dashboard for viewing and managing test results across different environments and artefact types. You can integrate Test Observer with your testing pipelines to track test executions for software artefacts (debs, snaps, charms, and images), compare results across versions, and gate releases based on test outcomes.

In this tutorial, you will learn how to integrate your test automation with Test Observer. You will create a Python script that simulates CI/CD behaviour to start a test run and report test results to Test Observer using the REST API. 

Understand the workflow
-----------------------

Test Observer does not trigger or run tests itself. It is a tracking and reporting system that stores test results from external test runners. Your test runner (Jenkins, GitHub Actions, pytest, etc.) is responsible for executing tests. Test Observer's role is to receive and store the results after tests complete. 

Test Observer's API workflow consists of three main steps:

1. Start a **test execution**: when your CI/CD pipeline or test runner decides to run tests, it calls Test Observer API to specify what artefact or software package is being tested.

   An **artefact** is a Debian package, snap, charm, or system image with a specific name and version. A test execution groups all test results from one test session together for a specific artefact version in a particular environment.

   In this tutorial, we will not run actual tests. Instead, we will simulate the workflow by creating fake test results. In a real integration, it's the test runners that execute tests and report results.

2. Submit **test results**: after tests complete, the test runner submits individual test results to the Test Observer execution. Each test result represents a single test that passed, failed, or was skipped.

3. Complete the execution: the test runner signals that testing is finished so Test Observer can calculate the overall execution status based on all submitted test results.


Set up your workspace
----------------------

Before starting, ensure you have the following prerequisites: 

- Access to Test Observer instance (the Canonical production and staging instances require VPN access)
- An API key with ``change_test`` permission to the instance (contact Test Observer administrators)

.. note::

    We will use the Canonical staging instance in this tutorial as an example. The staging API server is available at: `https://test-observer-api-staging.canonical.com/`. If you need to use other instances, replace the base URL accordingly.


Create a project directory and install the required Python library:

.. code-block:: shell

   mkdir test-observer-tutorial
   cd test-observer-tutorial
   python3 -m venv venv
   source venv/bin/activate
   pip install requests

The ``requests`` library will be used to communicate with the Test Observer API.


Configure authentication
-------------------------

Test Observer requires an API key to accept test results from automation tools. 
In this tutorial, we will create Python script that uses an environment variable to securely store the API key.
