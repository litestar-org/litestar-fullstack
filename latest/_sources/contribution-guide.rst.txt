:orphan:

.. include:: ../CONTRIBUTING.rst

Setting up the environment
--------------------------

1. If you do not have already have Astral's UV installed, run `make install-uv`
2. Run ``uv sync --all-groups`` to create a `virtual environment <https://docs.python.org/3/tutorial/venv.html>`_ and install
   the dependencies
3. If you're working on the documentation and need to build it locally, install the extra dependencies with ``uv sync --group docs``
4. Install `pre-commit <https://pre-commit.com/>`_
5. Run ``pre-commit install`` to install pre-commit hooks

**Note** There is a short-cut for running the installation process.  You can run ``make install`` to install the dependencies and pre-commit hooks.

Code contributions
------------------

Workflow
++++++++

1. `Fork <https://github.com/litestar-org/litestar-fullstack/fork>`_ the `fullstack repository <https://github.com/litestar-org/litestar-fullstack>`_
2. Clone your fork locally with git
3. `Set up the environment <#setting-up-the-environment>`_
4. Make your changes
5. (Optional) Run ``make lint`` to run linters and formatters. This step is optional and will be executed
   automatically by git before you make a commit, but you may want to run it manually in order to apply fixes
6. Commit your changes to git
7. Push the changes to your fork
8. Open a `pull request <https://docs.github.com/en/pull-requests>`_. Give the pull request a descriptive title
   indicating what it changes. If it has a corresponding open issue.
   For example a pull request that fixes issue ``bug: Increased stack size making it impossible to find needle``
   could be titled ``fix: Make needles easier to find by applying fire to haystack``

.. tip:: Pull requests and commits all need to follow the
    `Conventional Commit format <https://www.conventionalcommits.org>`_

Project documentation
---------------------

The documentation is located in the ``/docs`` directory and is built with `ReST <https://docutils.sourceforge.io/rst.html>`_
