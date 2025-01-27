Submit a test to Test Observer
==============================

Below are the main steps involved in submitting a test to Test Observer (TO):

#. Inform TO that testing has started
#. Submit the results of the testing
#. Inform TO that testing has ended

Note that if you want to execute multiple test plans on the same environment, or test on multiple environments then you will need to repeat the steps for each test execution.

Inform TO that testing has started
----------------------------------

Send a ``PUT`` request to the `start_test endpoint <https://test-observer-api.canonical.com/docs#/test-executions/start_test_execution_v1_test_executions_start_test_put>`_ with a body following the schema appropriate to the type of artefact you are testing (the aforementioned link includes the different schemas). The body of this request includes information about the artefact, the environment and the test plan. TO will store this information and return a test execution id that you will need to submit the results to. It is worth noting that a test execution is not a single test. It is a collection of tests grouped together under a single test plan to be executed on a single environment.

Submit the results of the testing
---------------------------------

When you have the results of your testing, you can submit them to TO using a ``POST`` to the `test-results <https://test-observer-api.canonical.com/docs#/test-executions/post_results_v1_test_executions__id__test_results_post>`_ endpoint. This endpoint may be called multiple times in case you wanted to submit the results in batches.

Inform TO that testing has ended
--------------------------------

Once testing has been completed and you have submitted the results to TO, you should inform TO that the test execution has ended. You can do so by sending a ``PATCH`` request to the `test-executions <https://test-observer-api.canonical.com/docs#/test-executions/patch_test_execution_v1_test_executions__id__patch>`_ endpoint with a body containing::

    {
        "status": "COMPLETED"
    }

TO will then parse the submitted results and set the status of the test execution to either ``PASSED`` (if all tests passed), ``FAILED`` (if some tests failed), or ``ENDED_PREMATURELY`` (if no tests were submitted).
