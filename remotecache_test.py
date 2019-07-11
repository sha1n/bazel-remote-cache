import os
import tempfile
import unittest
from unittest import mock
from uuid import uuid4

# noinspection PyProtectedMember
from remotecache import RemoteCacheFlagsResolver, remote_cache_flags_for, remote_cache_bucket_name, _macos_fingerprint

_RANDOM_BUCKET_NAME = str(uuid4())


def fixed_env_fingerprint():
    return "fingerprint"


def random_mac_ver():
    return str(uuid4()), None, None


def fixed_mac_ver():
    return "1.1.1", None, None


# noinspection PyUnusedLocal
def fixed_clang_fingerprint(cmd, stdout, stderr, encoding):
    assert cmd == ["clang", "--version"]

    d = Dummy()
    d.stdout = "clang_is_clang_is_clang"

    return d


# noinspection PyUnusedLocal
def random_clang_fingerprint(cmd, stdout, stderr, encoding):
    assert cmd == ["clang", "--version"]

    d = Dummy()
    d.stdout = str(uuid4())

    return d


class RemoteCacheTest(unittest.TestCase):

    # noinspection PyUnusedLocal
    @mock.patch("platform.mac_ver", side_effect=fixed_mac_ver)
    @mock.patch("subprocess.run", side_effect=fixed_clang_fingerprint)
    def test_macos_fingerprint_reproducibility(self, m1, m2):
        self.assertEqual(_macos_fingerprint(), _macos_fingerprint())

    # noinspection PyUnusedLocal
    @mock.patch("platform.mac_ver", side_effect=random_mac_ver)
    @mock.patch("subprocess.run", side_effect=fixed_clang_fingerprint)
    def test_macos_version_fingerprint(self, m1, m2):
        os1_fingerprint = _macos_fingerprint()
        os2_fingerprint = _macos_fingerprint()

        self.assertNotEqual(os1_fingerprint, os2_fingerprint)

    # noinspection PyUnusedLocal
    @mock.patch("platform.mac_ver", side_effect=fixed_mac_ver)
    @mock.patch("subprocess.run", side_effect=random_clang_fingerprint)
    def test_macos_version_fingerprint(self, m1, m2):
        clang1_fingerprint = _macos_fingerprint()
        clang2_fingerprint = _macos_fingerprint()

        self.assertNotEqual(clang1_fingerprint, clang2_fingerprint)

    @mock.patch.dict(os.environ, {'BAZEL_DISABLE_REMOTE_CACHE': '1'})
    def test_enable_remote_cache_env_var_disable(self):
        self.assertEqual([], remote_cache_flags_for("Darwin"))

    @mock.patch.dict(os.environ, {'BAZEL_DISABLE_REMOTE_CACHE': '0'})
    def test_enable_remote_cache_os_disable(self):
        self.assertFalse([], remote_cache_flags_for(str(uuid4())))

    @mock.patch.dict(os.environ, {'BAZEL_REMOTE_CACHE_BUCKET_NAME': _RANDOM_BUCKET_NAME})
    def test_remote_cache_bucket_name_env_var(self):
        self.assertEqual(_RANDOM_BUCKET_NAME, remote_cache_bucket_name())

    def test_remote_cache_bucket_name_default(self):
        self.assertEqual("bazel-dev-remote-cache", remote_cache_bucket_name())


class RemoteCacheFlagsResolverTest(unittest.TestCase):

    @staticmethod
    def new_remote_cache_flags_resolver(os_name="tests", env_fingerprint=fixed_env_fingerprint):
        temp_config_dir = tempfile.mkdtemp(prefix="RemoteCacheFlagsResolverTest")
        create_dummy_config_files(temp_config_dir)

        return RemoteCacheFlagsResolver(
            config_dir=temp_config_dir,
            os_name=os_name,
            env_fingerprint=env_fingerprint
        )

    def test_equal_envs_write_to_the_same_location(self):
        argmap1 = resolved_args_map_for(
            self.new_remote_cache_flags_resolver(os_name="MyOS", env_fingerprint=fixed_env_fingerprint)
        )
        argmap2 = resolved_args_map_for(
            self.new_remote_cache_flags_resolver(os_name="MyOS", env_fingerprint=fixed_env_fingerprint)
        )

        self.assertEqual(remote_cache_url_for(argmap1), remote_cache_url_for(argmap2))

    def test_os_name_variant(self):
        argmap1 = resolved_args_map_for(
            self.new_remote_cache_flags_resolver(os_name="OS1", env_fingerprint=fixed_env_fingerprint)
        )
        argmap2 = resolved_args_map_for(
            self.new_remote_cache_flags_resolver(os_name="OS2", env_fingerprint=fixed_env_fingerprint)
        )

        self.assertNotEqual(remote_cache_url_for(argmap1), remote_cache_url_for(argmap2))

    def test_env_fingerprint_variant(self):
        argmap1 = resolved_args_map_for(
            self.new_remote_cache_flags_resolver(os_name="MyOS", env_fingerprint=fixed_env_fingerprint)
        )
        argmap2 = resolved_args_map_for(
            self.new_remote_cache_flags_resolver(os_name="MyOS", env_fingerprint=random_env_fingerprint)
        )

        self.assertNotEqual(remote_cache_url_for(argmap1), remote_cache_url_for(argmap2))


def parse_bazel_args(args):
    argmap = {}
    for arg in args:
        segments = arg.split("=")
        if len(segments) == 1:
            argmap[segments[0]] = True
        else:
            assert len(segments) == 2
            argmap[segments[0]] = segments[1]

    return argmap


def remote_cache_url_for(argmap):
    return argmap["--remote_http_cache"]


def resolved_args_map_for(resolver):
    return parse_bazel_args(resolver.resolve_remote_cache_flags())


def create_dummy_config_files(path):
    gcloud_config_dir = os.path.join(path, ".config", "gcloud")
    os.makedirs(gcloud_config_dir)
    open(os.path.join(gcloud_config_dir, "application_default_credentials.json"), 'a').close()


def random_env_fingerprint():
    return str(uuid4())


class Dummy:
    pass


if __name__ == '__main__':
    unittest.main()
