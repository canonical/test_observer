=======================================
How to Authenticate with Test Observer
=======================================

Log in as a User
================

1. Navigate to Test Observer
2. Click "Log in" 
3. Sign in with your Ubuntu One SSO credentials

You'll have permissions based on your Launchpad team memberships.

Access the REST API
===================

For general guidance on using the REST API through the Swagger UI or with
``curl``, see :doc:`Access the Test Observer API <access-rest-api>`.

Get an API Key
==============

1. Ask your Test Observer administrator for an application
2. Provide:
   
   - Application name
   - Required permissions

3. Receive your API key

Test Observer administrators can follow :doc:`How to Manage Applications and
API Keys <manage-api-keys>` to manage applications and their keys through the
REST API.

Use an API Key
==============

Add the key to your requests::

    Authorization: Bearer <your-api-key>

**Python**::

    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)

**cURL**::

    curl -H "Authorization: Bearer ${API_KEY}" <url>

Request More Permissions
========================

**For users**: Ask your admin to grant permissions to your Launchpad team

**For applications**: Ask your admin to update your application's permissions

Troubleshooting
===============

**Can't log in?**
  - Clear browser cookies
  - Try incognito mode
