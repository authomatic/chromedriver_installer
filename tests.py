import itertools
import os
import re
import shlex
import subprocess
import tempfile
try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

import pytest


PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
VIRTUALENV_DIR = os.environ['VIRTUAL_ENV']
INSTALL_COMMAND_BASE = 'pip install {0} '.format(PROJECT_DIR)


def generate_version_fixture_params():
    """
    Loads all known versions of chromedriver from
    `https://chromedriver.storage.googleapis.com`__
    and returns a dictionary with keys ``params`` and ``ids`` which should be
    unpacked as arguments to :func:`pytest.fixture` decorator.

    This way we can generate and ``params`` and ``ids`` arguments with a single
    function call. We need the ``ids`` parameter for nice display of tested
    versions in the verbose ``pytest`` output.

    :returns:
        A dictionary with keys ``params`` and ``ids``.
    """
    body = urlopen('https://chromedriver.storage.googleapis.com').read()
    versions = re.findall(
        r'<Key>(\d+\.\d{2}).*?<ETag>"(.*?)"</ETag>',
        body.decode('utf-8'),
    )

    params = [
        (version, [checksum for _, checksum in checksums])
        for version, checksums in itertools.groupby(versions, lambda x: x[0])
    ]

    return dict(
        params=params,
        ids=[version for version, _ in params]
    )


@pytest.fixture(**generate_version_fixture_params())
def version(request):
    request.param_index = request.param[0]
    return request.param


class Base(object):
    def _uninstall(self):
        try:
            subprocess.check_call(
                shlex.split('pip uninstall chromedriver_installer -y')
            )
        except subprocess.CalledProcessError:
            pass

        chromedriver_executable = os.path.join(VIRTUALENV_DIR,
                                               'bin', 'chromedriver')

        if os.path.exists(chromedriver_executable):
            print('REMOVING chromedriver executable: ' +
                  chromedriver_executable)
            os.remove(chromedriver_executable)

    def teardown(self):
        self._uninstall()

    def _not_available(self):
        with pytest.raises(OSError):
            subprocess.check_call(shlex.split('chromedriver --version'))


class TestFailure(Base):
    def test_bad_checksum(self):
        self._not_available()

        command = INSTALL_COMMAND_BASE + (
            '--install-option="--chromedriver-version=2.10" '
            '--install-option="--chromedriver-checksums=foo,bar,baz"'
        )

        error_message = subprocess.Popen(
            shlex.split(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).communicate()[0]

        assert ('matches none of the checksums '
                'foo, bar, baz!') in str(error_message)


class VersionBase(Base):
    def _assert_cached_files_exist(self, exists, remove=False):
        path = os.path.join(tempfile.gettempdir(),
                            'chromedriver_{0}.zip'.format(self.version))

        if remove and os.path.exists(path):
            os.remove(path)

        assert os.path.exists(path) is exists

    def _test_version(self, version, cached):
        self.version, self.checksums = version

        # Chromedriver executable should not be available.
        self._not_available()

        # Assert that zip archives are cached or not, depending on test type.
        self._assert_cached_files_exist(cached, remove=not cached)

        # After installation...
        subprocess.check_call(shlex.split(self._get_install_command()))

        # ...the chromedriver executable should be available...
        expected_version, error = subprocess.Popen(
            shlex.split('chromedriver -v'),
            stdout=subprocess.PIPE
        ).communicate()

        # ...and should be of the right version.
        assert self.version in str(expected_version)

    def test_version_uncached(self, version):
        self._test_version(version, cached=False)


class TestVersionOnly(VersionBase):
    def _get_install_command(self):
        return (
            INSTALL_COMMAND_BASE +
            '--install-option="--chromedriver-version={0}"'.format(self.version)
        )


class TestVersionAndChecksums(VersionBase):
    def _get_install_command(self):
        return INSTALL_COMMAND_BASE + (
            '--install-option="--chromedriver-version={0}" '
            '--install-option="--chromedriver-checksums={1}"'
        ).format(self.version, ','.join(self.checksums))

    def test_version_cached(self, version):
        self._test_version(version, cached=True)
