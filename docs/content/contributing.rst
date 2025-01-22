:orphan:


How to contribute
=================

We believe that everyone has something valuable to contribute,
whether you're a coder, a writer or a tester.
Here's how and why you can get involved:

- **Why join us?** Work with like-minded people, develop your skills,
  connect with diverse professionals, and make a difference.

- **What do you get?** Personal growth, recognition for your contributions,
  early access to new features and the joy of seeing your work appreciated.

- **Start early, start easy**: Dive into code contributions,
  improve documentation, or be among the first testers.
  Your presence matters,
  regardless of experience or the size of your contribution.


The guidelines below will help keep your contributions effective and meaningful.


Code of conduct
---------------

When contributing, you must abide by the
`Ubuntu Code of Conduct <https://ubuntu.com/community/ethos/code-of-conduct>`_.


Licence and copyright
---------------------

By default, all contributions to Test Observer Backend are made under the AGPLv3 licence. See the [licence](https://github.com/canonical/test_observer/blob/main/backend/LICENSE) in the Test Observer GitHub repository for details. All contributions to Test Observer Frontend are made under the GPLv3 license. See the [licence](https://github.com/canonical/test_observer/blob/main/frontend/LICENSE) in the Test Observer GitHub repository for details.

All contributors must sign the `Canonical contributor licence agreement
<https://ubuntu.com/legal/contributors>`_,
which grants Canonical permission to use the contributions.
The author of a change remains the copyright owner of their code
(no copyright assignment occurs).


Environment setup
-----------------

To work on the backend, see the backend's [README](https://github.com/canonical/test_observer/blob/main/backend/README.md).
To work on the frontend, see the frontend's [README](https://github.com/canonical/test_observer/blob/main/frontend/README.md)


Submissions
-----------

If you want to address an issue or a bug in Test Observer,
notify in advance the people involved to avoid confusion;
also, reference the issue or bug number when you submit the changes.

- `Fork
  <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/about-forks>`_
  our `GitHub repository <https://github.com/canonical/test_observer>`_
  and add the changes to your fork,
  properly structuring your commits,
  providing detailed commit messages
  and signing your commits.

- Make sure the updated project builds and runs without warnings or errors;
  this includes linting, documentation, code and tests.

- Submit the changes as a `pull request (PR)
  <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork>`_.


Your changes will be reviewed in due time;
if approved, they will be eventually merged.


Describing pull requests
~~~~~~~~~~~~~~~~~~~~~~~~

To be properly considered, reviewed and merged,
your pull request must provide the following details:

- **Title**: Summarise the change in a short, descriptive title.

- **Description**: Explain the problem that your pull request solves.
  Mention any new features, bug fixes or refactoring.

- **Relevant issues**: Reference any
  `related issues, pull requests and repositories <https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/autolinked-references-and-urls>`_.

- **Testing**: Explain whether new or updated tests are included.

- **Reversibility**: If you propose decisions that may be costly to reverse,
  list the reasons and suggest steps to reverse the changes if necessary.


Signing commits
~~~~~~~~~~~~~~~

To improve contribution tracking, we use the developer certificate of origin
(`DCO 1.1 <https://developercertificate.org/>`_) and require signed commits
(using the ``-S`` or ``--gpg-sign`` option) for all changes that go into the
Test Observer project.

Signed commits will have a GPG, SSH, or S/MIME signature that is
cryptographically verifiable, and will be marked with a "Verified" or
"Partially verified" badge in GitHub. This verifies that you made the changes or
have the right to commit it as an open-source contribution.

To set up locally signed commits and tags, see `GitHub Docs - About commit
signature verification <https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification>`_.

.. tip::

   You can configure your Git client to sign commits by default for any local
   repository by running ``git config --global commit.gpgsign true``.
   Once you have configured this, you no longer need to add ``-S`` to your
   commits explicitly.

   See `GitHub Docs - Signing commits <https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits>`_ for more information.

If you've made an unsigned commit and encounter the "Commits must have verified
signatures" error when pushing your changes to the remote:

1. Amend the most recent commit by signing it without changing the commit
   message, and push again:

   .. code-block:: none

      git commit --amend --no-edit -n -S
      git push
#. If you still encounter the same error, confirm that your GitHub account has
   been set up properly to sign commits as described in the `GitHub Docs - About
   commit signature verification <https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification>`_.

   .. tip::

      If you use SSH keys to sign your commits, make sure to add a "Signing Key"
      type in your GitHub account. See
      [GitHub Docs - Adding a new SSH key to your account](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)
      for more information.


Structure
~~~~~~~~~

- **Check linked code elements**:
  Check that coupled code elements, files and directories are adjacent.
  For instance, store test data close to the corresponding test code.

- **Group variable declaration and initialisation**:
  Declare and initialise variables together
  to improve code organisation and readability.

- **Split large expressions**:
  Break down large expressions
  into smaller self-explanatory parts.
  Use multiple variables where appropriate
  to make the code more understandable
  and choose names that reflect their purpose.

- **Use blank lines for logical separation**:
  Insert a blank line between two logically separate sections of code.
  This improves its structure and makes it easier to understand.

- **Avoid nested conditions**:
  Avoid nesting conditions to improve readability and maintainability.

- **Remove dead code and redundant comments**:
  Drop unused or obsolete code and comments.
  This promotes a cleaner code base and reduces confusion.

- **Normalise symmetries**:
  Treat identical operations consistently, using a uniform approach.
  This also improves consistency and readability.


Tests
-----

All code contributions must include tests.

To run tests locally, frontend and backend directories.


Documentation
-------------

Test Observer's documentation is stored in the ``DOCDIR`` directory of the repository.
It is based on the `Canonical starter pack
<https://canonical-starter-pack.readthedocs-hosted.com/latest/>`_
and hosted on `Read the Docs <https://about.readthedocs.com/>`_.

For syntax help and guidelines,
refer to the `Canonical style guides
<https://canonical-documentation-with-sphinx-and-readthedocscom.readthedocs-hosted.com/#style-guides>`_.

In structuring,
the documentation employs the `Diátaxis <https://diataxis.fr/>`_ approach.

To run the documentation locally before submitting your changes:

.. code-block:: console

   make run


Automatic checks
~~~~~~~~~~~~~~~~

GitHub runs automatic checks on the documentation
to verify spelling, validate links and suggest inclusive language.

You can (and should) run the same checks locally:

.. code-block:: console

   make spelling
   make linkcheck
   make woke
