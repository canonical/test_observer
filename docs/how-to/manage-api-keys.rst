========================================
How to Manage Applications and API Keys
========================================

Test Observer API keys belong to applications. An application's permissions
determine what requests its key can make. There is no separate API-key
management UI, so use the REST API to review applications, create keys, change
permissions, rotate keys, or revoke them by deleting their application.

Before you begin
================

Sign in as a Test Observer administrator, or use an account with the required
application-management permissions. Administrators can perform these
operations; otherwise, the endpoint-specific permissions are:

* ``view_application`` to list or view applications and their keys.
* ``add_application`` to create an application and key.
* ``change_application`` to change permissions, rotate a key, or delete an
  application.

For instructions on using the Swagger UI or making requests with ``curl``, see
:doc:`Access the Test Observer API <access-rest-api>`. The examples below use
the production API paths; use the corresponding API URL for your instance.

Review applications and keys
=============================

Use ``GET /v1/applications`` to list all applications. Each result includes
the application's ``id``, ``name``, ``permissions``, and ``api_key``. Use
``GET /v1/applications/{application_id}`` to retrieve one application by ID.
Both endpoints require ``view_application``.

These responses include usable API keys, not just metadata. Treat them as
secrets and limit ``view_application`` to people who are trusted to access
those credentials. To look up valid permission identifiers, use
``GET /v1/permissions`` (requires ``view_permission``).

Create an application and API key
=================================

Send ``POST /v1/applications`` with a unique application name and the exact
permissions the integration needs. This requires ``add_application``. For
example, a client that only needs to read artefacts and test results could be
created with:

.. code-block:: json

   {
     "name": "example-reporting-integration",
     "permissions": ["view_artefact", "view_test"]
   }

Choose permissions based on the endpoints the integration will call. You can
use an empty list to create an application with no assigned permissions, then
grant permissions later. The response includes the new application's ID and
API key. Store the key in an approved secrets store and send it to the API as
an ``Authorization: Bearer`` token; see :doc:`Access the Test Observer API
<access-rest-api>` for request details.

Change an application's permissions
====================================

Send ``PATCH /v1/applications/{application_id}`` with the complete permissions
list you want that application to have. This requires ``change_application``.
For example, to replace its current permissions with read access to artefacts
only, send:

.. code-block:: json

   {
     "permissions": ["view_artefact"]
   }

An empty list removes all assigned permissions. This changes what the key can
do, but does not rotate or revoke the key itself. The response includes the
application details and key.

Rotate a key after a leak
=========================

If an application's key may have been exposed, send
``POST /v1/applications/{application_id}/rotate``. This requires
``change_application``. The response contains the replacement key, and the
previous key stops working immediately. Update the integration's secret with
the new key; requests using the old key will fail.

After rotating, promptly notify the team responsible for the integration and
any teams that depend on it. Identify the affected credential by the
application's name and ID, and explain that the previous key has been
invalidated so consumers can update their secret. Do not send the old or new
key in the notification; share the replacement through your approved secrets
store. Test Observer does not record who created or owns an application. Use
its name and any available context to make a best-effort attempt to identify
and contact the likely owner; a name may mention a team, project, or engineer,
but it does not guarantee who owns the application.

Test Observer does not provide a separate key-expiration setting or endpoint.
To invalidate a key while keeping the application, rotate it. An application
can also rotate its own key with ``POST /v1/applications/me/rotate`` when
authenticated with that key.

Revoke a key and remove an application
======================================

To revoke a key permanently and remove its application, send
``DELETE /v1/applications/{application_id}``. This requires
``change_application`` and returns ``204 No Content`` when complete. The
application and its key are removed; create a new application if the
integration is needed again.

Endpoint summary
================

.. list-table:: Application-management endpoints
   :header-rows: 1

   * - Goal
     - Request
     - Required permission
   * - List applications and keys
     - ``GET /v1/applications``
     - ``view_application``
   * - Get one application and key
     - ``GET /v1/applications/{application_id}``
     - ``view_application``
   * - Create an application and key
     - ``POST /v1/applications``
     - ``add_application``
   * - Change an application's permissions
     - ``PATCH /v1/applications/{application_id}``
     - ``change_application``
   * - Rotate an application's key
     - ``POST /v1/applications/{application_id}/rotate``
     - ``change_application``
   * - Delete an application and revoke its key
     - ``DELETE /v1/applications/{application_id}``
     - ``change_application``
