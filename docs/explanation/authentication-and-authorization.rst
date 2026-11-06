============================================
Understanding Test Observer Authentication
============================================

Two Types of Authentication
============================

Test Observer separates human users from automated systems:

- **Users** authenticate via Ubuntu One SSO
- **Applications** authenticate via API keys

This separation allows interactive web access for humans while providing simple tokens for scripts and automation.

How Permissions Work
====================

Users Get Permissions from Teams
---------------------------------

When you log in through Ubuntu One SSO, Test Observer receives your Launchpad team memberships. Your permissions come from these teams.

**Example**: If you're in the "canonical-hw-cert" Launchpad team, and that team has "create_artefact" permission, you can create artefacts.

Applications Get Direct Permissions
------------------------------------

Applications don't belong to teams. They receive specific permissions directly when created.

**Example**: A CI/CD pipeline might have only "create_artefact" permissions.

Using a Browser Session with cURL
=================================

You can make a manual API request with your browser session cookie, but the
cookie alone is not sufficient. Every request authenticated with a session
cookie must also include the ``X-CSRF-Token`` header. The browser-based Swagger
UI handles the cookie and header automatically. For a ``curl`` example and
guidance on handling the session cookie safely, see
:doc:`Access the Test Observer API <../how-to/access-rest-api>`.

For scripts and automation, use an application API key instead of a personal
browser session; see :doc:`How to Authenticate with Test Observer
<../how-to/authenticate>`.
