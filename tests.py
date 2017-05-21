import itertools
import os
import re
import shlex
import subprocess
import tempfile
import urllib2

import pytest


PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
VIRTUALENV_DIR = os.environ['VIRTUAL_ENV']
INSTALL_COMMAND_BASE = 'pip install {0} '.format(PROJECT_DIR)


def fetch_available_versions():
    body = urllib2.urlopen('https://chromedriver.storage.googleapis.com').read()
    versions = re.findall(r'<Key>(\d+\.\d{2}).*?<ETag>"(.*?)"</ETag>', body)

    return [
        (version, [checksum for _, checksum in checksums])
        for version, checksums in itertools.groupby(versions, lambda x: x[0])
    ]


@pytest.fixture(params=fetch_available_versions())
def version_info(request):
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

    def _test_version(self, version_info, cached):
        self.version, self.checksums = version_info

        # Chromedriver executable should not be available.
        self._not_available()

        # Assert that zip archives are cached or not, depending on test type.
        self._assert_cached_files_exist(cached, remove=not cached)

        # After installation...
        subprocess.check_call(shlex.split(self._get_install_command()))

        # ...the chromedriver executable should be available...
        expected_version = subprocess.Popen(
            shlex.split('chromedriver -v'),
            stdout=subprocess.PIPE
        ).communicate()[0]

        # ...and should be of the right version.
        assert self.version in str(expected_version)

    def test_version_uncached(self, version_info):
        self._test_version(version_info, cached=False)


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

    def test_version_cached(self, version_info):
        self._test_version(version_info, cached=True)
