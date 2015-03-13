import os
import shlex
import subprocess
import tempfile

import pytest


PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
VIRTUALENV_DIR = os.environ['VIRTUAL_ENV']
INSTALL_COMMAND_BASE = 'pip install {0} '.format(PROJECT_DIR)


# The --version option is available since version 2.10
VERSIONS = {
    '2.10': (
        '4fecc99b066cb1a346035bf022607104',
        '058cd8b7b4b9688507701b5e648fd821',
        'fd0dafc3ada3619edda2961f2beadc5c',
        '082e91e5c8994a7879710caeed62e334'
    ),
    '2.11': (
        'bf0d731cd34fd07e22f4641c9aec8483',
        '7a7336caea140f6ac1cb8fae8df50d36',
        '447ebc91ac355fc11e960c95f2c15622',
        '44443738344b887ff1fe94710a8d45dc'
    ),
    '2.12': (
        '6f4041e7f8300380cc2a13babbac354e',
        'f306b93ff1b34af74371cee87d6560e4',
        '259bb87f4ebf3b0bc4792ed203bd69f5',
        '51eb47ad5ea91422aa1aaa400a724e7b'
    ),
    '2.13': (
        '187dbe7973c82e59446d5bca7ed40acd',
        'fcfd993330704f8cfb307a2fca5a9687',
        'e37a65a1be68523385761d29decf15d4',
        'ae85407694d3849450a25431f9669a81'
    ),
    '2.14': (
        'f130cb3b94a8fbd28212f18c929f79ee',
        '8368d266bd832ff2ea292baedbc770be',
        '2b8a3e7249c80dec95264cbb55c897ed',
        '00c70587c3e215f030307d546b315323'
    )
}


@pytest.fixture(params=VERSIONS)
def version_info(request):
    return request.param


class Base(object):
    def _uninstall(self):
        try:
            subprocess.check_call(shlex.split('pip uninstall chromedriver_installer -y'))
        except subprocess.CalledProcessError:
            pass

        chromedriver_executable = os.path.join(VIRTUALENV_DIR,
                                               'bin', 'chromedriver')

        if os.path.exists(chromedriver_executable):
            print('REMOVING chromedriver executable: ' + chromedriver_executable)
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

        assert 'failed with error code 1' in str(error_message)


class VersionBase(Base):

    def _assert_cached_files_exist(self, exists, remove=False):
        path = os.path.join(tempfile.gettempdir(),
                            'chromedriver_{0}.zip'.format(self.version))

        if remove and os.path.exists(path):
            os.remove(path)

        assert os.path.exists(path) is exists

    def _test_version(self, version_info, cached):
        self.version = version_info
        self.checksums = VERSIONS[version_info]

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
