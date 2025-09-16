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

Why You Can't Use cURL with Your Browser Session
=================================================

When logged in through the web, you can't copy your session cookie to cURL due to CSRF protection. Test Observer requires special tokens that prove requests come from its own pages.

**Solution**: Either use the web API interface at ``/docs`` or get an API key.
