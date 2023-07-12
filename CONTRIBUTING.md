Installation
============

```shell
$ git clone https://github.com/SUSE-Enceladus/csp-billing-adapter.git
$ cd csp-billing-adapter

# Create a Python Virtual Environment (venv) using:
# $ python3 -m venv <path_to_venv>
# Activate the Virtual Environment using:
# $ . <path_to_venv>/bin/activate
# And then install csp-billing-adapter in editable mode, along with it's
# dependencies and the recommended dev support tools.
$ pip install -e .[dev]
```

`csp-billing-adapter` is now installed in the active virtual environment in development
mode.

*NOTE*: You will need to create a `~/.config/csp-billing-adapter.yaml` with
appropriate configuration settings to be able to run the `csp-billing-adapter`
command directly.

Dev Requirements
================

- bumpversion

Testing Requirements
====================

- coverage
- flake8
- pytest-cov

Contribution Checklist
======================

- All patches must be signed. [Signing Commits](#signing-commits)
- All contributed code must conform to flake8. [Code Style](#code-style)
- All new code contributions must be accompanied by a test.
    - Tests must pass and coverage remain above 90%. [Unit & Integration Tests](#unit-&-integration-tests)
- Follow Semantic Versioning. [Versions & Releases](#versions-&-releases)

Versions & Releases
===================

**csp-billing-adapter** adheres to Semantic versioning; see <http://semver.org/> for
details.

[bumpversion](https://pypi.python.org/pypi/bumpversion/) is used for
release version management, and is configured in `setup.cfg`:

```shell
$ bumpversion major|minor|patch
$ git push
```

Bumpversion will create a commit with version updated in all locations.
The annotated tag is created separately.

```shell
$ git tag -a v{version}
# git tag -a v0.0.1

# Create a message with the changes since last release and push tags.
$ git push --tags
```

Testing with tox
================
The `tox` tool automatically creates appropriately configured Python
virtual environments that can be used to run the code quality and
verification tests, avoiding the need for the user to create an
appropriate Python virtual environment.

The `tox.ini` settings should work with versions of tox >= 2.9.1; the
latest tox version available for your system's Python version should
be available in your virtualenv if you installed the developer tools
using `pip install -e .[dev]`.

If you want to run the recommended code quality and verification tests
you can use the `tox` command with no arguments:

```shell
$ tox
```

*NOTE1*: By default tox is configured to run the pytest coverage tests for
all supported Python versions, skipping any versions that aren't available.
See [pyenv](https://github.com/pyenv/pyenv) for a solution that allows
multiple versions of Python to be installed and available to support local
testing.

*NOTE2*: On openSUSE Leap systems with a distro packages tox (version 2.9.1)
if you have additional systemn Python versions installed, e.g. python3.10,
you may see errors from tox related to trying to setup virtial environments
for Python 3.10. If so it is recommened to create a virtialenv and install
the latest version of tox available for your Python version, and use that
tox command.

If you want to run just the recommended code quality and verification tests
using your system's default `python3` version, you can explicity select the
`dev` testing environment when running tox:

```shell
$ tox -e dev
```

Unit & Integration Tests
========================

All tests should pass and test coverage should remain above 90%.

The tests and coverage can be run directly via pytest.

```shell
$ pytest --cov=csp_billing_adapter
```

Alternatively you can explicitly run just the pytest coverage tests using
`tox`:

```shell
$ tox -e pytest
```

Code Style
==========

Source should pass flake8 and pep8 standards.

```shell
$ flake8 csp_billing_adapter
```

Alternatively you can explicitly run just the code quality checks using
`tox`:

```shell
$ tox -e check
```

Signing Commits
===============

The repository and the code base patches sent for inclusion must be GPG
signed. See the GitHub article, [Signing commits using
GPG](https://help.github.com/articles/signing-commits-using-gpg/), for
more information.
