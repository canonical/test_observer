===================================
How to Access the Test Observer API
===================================

Test Observer exposes a REST API. You can explore and call it interactively
with the browser-based Swagger UI, or make requests from a command-line tool
such as ``curl``. This guide covers the common access and authentication
patterns; use the :doc:`OpenAPI reference <../reference/openapi>` to look up
available endpoints and their request and response schemas.

The production API base URL is ``https://test-observer-api.canonical.com``.
API paths shown in the documentation (for example, ``/v1/...``) are appended
to that base URL. Use your deployment's API URL when working with another
instance.

Use the Swagger UI in a browser
===============================

The API's ``/docs`` page is a Swagger UI generated from the OpenAPI schema.
For production, open:

``https://test-observer-api.canonical.com/docs``

Sign in to Test Observer in the browser first. In the Swagger UI, expand an
endpoint, select **Try it out**, provide any required parameters or request
body, and select **Execute**. The browser sends your session cookie, and the
Swagger page adds the required CSRF header automatically. Requests are still
subject to your account's permissions.

Call the API with ``curl`` and your browser session
===================================================

For an occasional manual request, you can send the API's session cookie with
``curl``. This uses your logged-in user identity and permissions; it does not
create an API key.

1. Sign in to Test Observer in your browser.
2. In your browser's developer tools, find the ``session`` cookie for the API
   host (``test-observer-api.canonical.com`` in production) and copy its
   value. Treat this value like a password: anyone who has it may be able to
   act as you until the session expires. Do not share it or save it in scripts,
   source control, or shell history.
3. Set the API URL and make a request, supplying both the cookie and the CSRF
   header:

   .. code-block:: bash

      API_URL="https://test-observer-api.canonical.com"
      read -rsp "Session cookie: " SESSION_COOKIE
      echo
      curl --get --cookie "session=${SESSION_COOKIE}" --header "X-CSRF-Token: 1" "${API_URL}/v1/..."
      unset SESSION_COOKIE

Replace ``/v1/...`` with the path of the endpoint you want to call, as shown
in the Swagger UI or OpenAPI reference. Include ``X-CSRF-Token`` on requests
authenticated with a session cookie, including ``GET`` requests. For requests
with a JSON body, add the appropriate method, content type, and body (for
example, ``--request POST``, ``--header 'Content-Type: application/json'``, and
``--data '{...}'``). The endpoint's documentation describes its required
parameters and body.

Use an API key for scripts and automation
=========================================

For repeatable scripts or CI/CD jobs, use an application API key rather than
copying a personal browser session cookie. See :doc:`How to Authenticate with
Test Observer <authenticate>` for how to request an application and use its
key. An API key is sent as an ``Authorization: Bearer`` header; it does not
use the browser session cookie or CSRF header. The application's assigned
permissions determine which operations it can perform.

Troubleshooting
===============

* A ``401 Unauthorized`` response usually means the session cookie is missing,
  invalid, or expired. Confirm that you copied the ``session`` cookie for the
  API host.
* A ``403 Forbidden`` response means the request was recognized but your user
  or application does not have permission for that operation. With a browser
  session, also check that the ``X-CSRF-Token`` header is present. Check the
  endpoint's required permissions in the Swagger UI or ask a Test Observer
  administrator.
