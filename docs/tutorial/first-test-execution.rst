Start your first test execution
===============================

Test Observer is a dashboard for viewing and managing test results on software artefacts across different environments. You can integrate Test Observer with your testing pipelines to monitor test results over time.

In this tutorial, you will learn how to report test results to Test Observer using its REST API. You will create a Python script that starts a test execution, submits test results, and marks the execution as complete.

Understand the workflow
-----------------------

Test Observer does not run tests itself, instead, it is a tracking and reporting system that stores test results from external test runners.

The integrated workflow consists of three main steps:

.. mermaid::

    sequenceDiagram
       participant Runner as Your test runner
       participant TO as Test Observer
    
       Runner->>TO: Start a test execution
       TO-->>Runner: Return <test_execution_id>
       Runner-->>Runner: Execute tests and collect results
       Runner->>TO: Submit test results
       Runner->>TO: Complete the test execution
       TO-->>TO: Calculate overall status

1. **Start a test execution**: your test runner calls Test Observer API to specify what artefact or software package is being tested.

   An **artefact** is a Debian package, snap, charm, or system image with a specific name and version. A **test execution** groups all test results from one test session together for a specific artefact version in a particular environment.

2. **Submit test results**: the test runner submits individual test results to the registered test execution ID.

3. **Complete the test execution**: the test runner signals that testing is finished so Test Observer can calculate the overall execution status based on all submitted test results.


Set up your workspace
----------------------

Before starting, ensure you have the following prerequisites: 

- Access to Test Observer instance (the Canonical production and staging instances require VPN access)
- An API key with ``change_test`` permission to the instance (contact Test Observer administrators)

.. note::

    We will use the Canonical staging instance in this tutorial as an example. The staging API server is available at: `https://test-observer-api-staging.canonical.com/`. If you need to use other instances, replace the base URL accordingly.


Create a project directory and install the ``requests`` library to communicate with the Test Observer API:

.. code-block:: shell

   python3 -m venv venv
   source venv/bin/activate
   pip install requests


Configure authentication
-------------------------

Test Observer requires an API key to accept test results from automation tools. 
In this tutorial, we will create Python script that uses an environment variable to securely store the API key.

For example, store your API key in an environment variable as follows:

.. code-block:: shell

   $ export TO_API_KEY="your-api-key"

Create a file named ``submit_test.py`` and add the following code to set up authentication:

.. code-block:: python

    #!/usr/bin/env python3
    import os
    import requests
    import sys

    # Basic configuration
    BASE_URL = "https://test-observer-api-staging.canonical.com"
    API_KEY = os.getenv("TO_API_KEY")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }


The headers dictionary will be used in all subsequent API requests to authenticate with Test Observer.


Start a test execution
-----------------------

Before submitting test results from the runners, you must start a test execution to tell Test Observer what you are testing and where the tests are running.

The test execution is defined by the artefact details and environment. The following example simulates the workflow by creating fake test results for a Debian package named ``hello-world-app`` in a test environment called ``tutorial-laptop``:

.. code-block:: python

   # Define what we are testing
   payload = {
       "family": "deb",
       "name": "hello-world-app",
       "version": "1.0.0-ubuntu1",
       "arch": "amd64",
       "environment": "tutorial-laptop",
       "test_plan": "smoke-tests",
       "series": "noble",
       "repo": "main",
       "execution_stage": "proposed",
   }

.. note::

    You can find the required fields for different artefact families in the `Staging API <https://test-observer-api-staging.canonical.com/docs>`_ or  `Production API <https://test-observer-api.canonical.com/docs>`_ specification.


Send a PUT request to the ``/v1/test-executions/start-test`` endpoint with this payload to register the test execution. Add the following code to your ``submit_test.py`` file:

.. code-block:: python

    print(f"Base URL: {BASE_URL}")
    print(f"Starting test execution for {payload['name']} {payload['version']}...")

    # Send PUT request to start the execution
    try:
        response = requests.put(
            f"{BASE_URL}/v1/test-executions/start-test",
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to start execution: {e}")
        sys.exit(1)

    execution_id = response.json()['id']
    print(f"Execution ID: {execution_id}")


Run the updated script:

.. code-block:: shell

    $ python3 submit_test.py

    Base URL: https://test-observer-api-staging.canonical.com
    Starting test execution for hello-world-app 1.0.0-ubuntu1...
    Execution ID: 42

The returned ``execution_id`` is a unique identifier for this test run. You will use this ID to submit results and complete the execution.

Submit test results
-------------------

Now that the execution is registered, you can submit test results as a grouped record. Each individual test result includes the test name, status, comments, and optional logs.

The following code example simulates submitting four test results: two passes, one failure, and one skipped test. Note that the test names should be unique within your test framework.

.. code-block:: python

    # Define test results
    test_results = [
        {
            "name": "test_boot",
            "status": "PASSED",
            "comment": "System booted in 15 seconds",
            "category": "boot",
        },
        {
            "name": "test_audio",
            "status": "PASSED",
            "comment": "Audio playback working correctly",
            "category": "audio",
        },
        {
            "name": "test_wifi",
            "status": "FAILED",
            "comment": "Could not connect to network",
            "category": "wifi",
            "io_log": "Error: Unable to connect to network ...",
        },
        {
            "name": "test_performance_benchmark",
            "status": "SKIPPED",
            "comment": "Requires GPU, not available in this environment",
            "category": "performance",
        },
    ]

    print(f"Submitting {len(test_results)} test results...")

To submit the list of test results, send a POST request to the ``/v1/test-executions/`` endpoint. Add the following code to your ``submit_test.py`` file:

.. code-block:: python

    try:
        response = requests.post(
            f"{BASE_URL}/v1/test-executions/{execution_id}/test-results",
            json=test_results,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to submit results: {e}")
        sys.exit(1)

    print("Results submitted")

Run the updated script again:

.. code-block:: shell

    $ python3 submit_test.py
    ...
    Submitting 4 test results...
    Results submitted

.. note::

   You can call the ``test-results`` endpoint multiple times to submit results in batches. Test Observer appends each batch to the execution.


Complete the execution
----------------------

After all test results are submitted, you must mark the execution as complete. This triggers Test Observer to parse the submitted results and calculate the overall execution status:

- **PASSED** (if all tests passed)
- **FAILED** (if any required tests failed)
- **ENDED_PREMATURELY** (if no tests were submitted)


Call the PATCH endpoint to mark the execution as complete:

.. code-block:: python

   print("Marking execution as complete...")

   try:
       response = requests.patch(
           f"{BASE_URL}/v1/test-executions/{execution_id}",
           json={"status": "COMPLETED"},
           headers=headers,
           timeout=30
       )
       response.raise_for_status()
   except requests.exceptions.RequestException as e:
       print(f"Failed to complete execution: {e}")
       sys.exit(1)

   print(f"Success! Your test execution is complete (ID: {execution_id})")

Run the complete script:

.. code-block:: shell

   $ python3 submit_test.py
   ...
   Marking execution as complete...
   Success! Your test execution is complete (ID: 42)


Verify in the dashboard
-----------------------

You can view your test execution results through the web interface. To find your execution, navigate to https://test-observer-staging.canonical.com/artefacts?family=deb and use the search box and filters to find the artefact name: ``hello-world-app`` and version ``1.0.0-ubuntu1``

The execution status should show ``FAILED`` because one test failed in our submitted results. Expand and check the individual test results and their logs.

Congratulations! You have successfully submitted your first test results to Test Observer using the REST API. You can now integrate Test Observer into your CI/CD pipelines to track test results across your projects.

Next steps
----------

To further explore Test Observer, consider the following resources:

- `Staging API`_ or `Production API`_ documentation for detailed API specifications
- :doc:`../explanation/glossary` for key terminology
- :doc:`../explanation/authentication-and-authorization` for managing API keys and permissions
- :doc:`../how-to/triage-test-results` to learn how to triage and approve artefacts

