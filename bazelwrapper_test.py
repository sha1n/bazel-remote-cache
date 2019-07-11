import os
import sys
import unittest
from unittest import mock

# noinspection PyProtectedMember
from bazelwrapper import build_bazel_command

_FAKE_WS_DIR = "/"
_EXPECTED_2ND_PARTY_SCRIPT_PATH = _FAKE_WS_DIR + "tools/resolve_2nd_party_repositories.py"


def resolve_fake_workspace_dir():
    return _FAKE_WS_DIR


# noinspection PyUnusedLocal
def remote_cache_flags_call(os_name):
    return ["--dummy_cache_flag"]


class BuildBazelCommandTest(unittest.TestCase):

    @mock.patch("remotecache.remote_cache_flags_for", side_effect=remote_cache_flags_call)
    def test_bazel_version_command_no_cache(self, remote_cache_flags_call_evidence):
        sys.argv = ["bazel", "version"]
        os.environ["BAZEL_REAL"] = "barzel"

        bazel_command = build_bazel_command()

        self.assertEqual(0, remote_cache_flags_call_evidence.call_count)

        self.assertEqual([os.environ["BAZEL_REAL"], "version"], bazel_command)

    @mock.patch("remotecache.remote_cache_flags_for", side_effect=remote_cache_flags_call)
    def test_bazel_info_command_no_cache(self, remote_cache_flags_call_evidence):
        sys.argv = ["bazel", "info"]
        os.environ["BAZEL_REAL"] = "barzel"

        bazel_command = build_bazel_command()

        self.assertEqual(0, remote_cache_flags_call_evidence.call_count)
        self.assertEqual([os.environ["BAZEL_REAL"], "info"], bazel_command)

    @mock.patch("remotecache.remote_cache_flags_for", side_effect=remote_cache_flags_call)
    def test_bazel_cacheable_command(self, remote_cache_flags_call_evidence):
        sys.argv = ["bazel", "tests", "//..."]
        os.environ["BAZEL_REAL"] = "barzel"

        bazel_command = build_bazel_command()

        self.assertEqual(1, remote_cache_flags_call_evidence.call_count)
        self.assertEqual([os.environ["BAZEL_REAL"], "tests", "//...", "--dummy_cache_flag"], bazel_command)

    @mock.patch("remotecache.remote_cache_flags_for", side_effect=remote_cache_flags_call)
    def test_bazel_cacheable_command_with_target_list(self, remote_cache_flags_call_evidence):
        sys.argv = ["bazel", "build", "--", "//target1:a", "//target2:a"]
        os.environ["BAZEL_REAL"] = "barzel"

        bazel_command = build_bazel_command()

        self.assertEqual(1, remote_cache_flags_call_evidence.call_count)
        self.assertEqual(
            [os.environ["BAZEL_REAL"], "build", "--dummy_cache_flag", "--", "//target1:a", "//target2:a"],
            bazel_command
        )


if __name__ == '__main__':
    unittest.main()
