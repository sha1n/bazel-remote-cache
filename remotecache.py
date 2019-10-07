import hashlib
import os
import platform
import subprocess
from typing import List

_BAZEL_REMOTE_CACHE_FLAG_ENV_VAR_NAME = "BAZEL_DISABLE_REMOTE_CACHE"
_BAZEL_REMOTE_CACHE_BUCKET_NAME_ENV_VAR_NAME = "BAZEL_REMOTE_CACHE_BUCKET_NAME"
_REMOTE_CACHE_BASE_URL = "https://storage.googleapis.com"
_DEFAULT_REMOTE_CACHE_BUCKET_NAME = "bazel-dev-remote-cache"


def remote_cache_flags_for(os_name):
    os_name_lower = os_name.lower()
    if os_name_lower == "darwin" and os.environ.get(_BAZEL_REMOTE_CACHE_FLAG_ENV_VAR_NAME, "0") != "1":
        return RemoteCacheFlagsResolver(
            os_name=os_name_lower,
            env_fingerprint=_macos_fingerprint
        ).resolve_remote_cache_flags()
    else:
        return []


class RemoteCacheFlagsResolver:
    def __init__(self, os_name, env_fingerprint):
        self.os_name = os_name
        self.env_fingerprint = env_fingerprint

    def resolve_remote_cache_flags(self) -> List[str]:
        return [
            "--remote_http_cache={base_url}/{bucket_name}/{path}/{macos_env_fingerprint}".format(
                base_url=_REMOTE_CACHE_BASE_URL,
                bucket_name=remote_cache_bucket_name(),
                path=self.os_name,
                macos_env_fingerprint=self.env_fingerprint(),
            ),
            "--experimental_guard_against_concurrent_changes",
            # This requires GCloud 'application-default' authentication to be set with a valid google account.
            # On MacOS and Linux systems the credentials file should normally be located here:
            #   ~/.config/gcloud/application_default_credentials.json
            "--google_default_credentials=true"
        ]


def remote_cache_bucket_name():
    return os.environ.get(_BAZEL_REMOTE_CACHE_BUCKET_NAME_ENV_VAR_NAME, _DEFAULT_REMOTE_CACHE_BUCKET_NAME)


def _macos_fingerprint():
    def clang_version():
        return subprocess.run(["clang", "--version"],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              encoding='utf-8').stdout

    # OS version is added to the path for convenience only. OS version is already included in clang_fingerprint
    os_version = platform.mac_ver()[0]
    clang_version_info = clang_version()
    return "{os_version}/{clang_fingerprint}".format(
        os_version=os_version,
        clang_fingerprint=hashlib.sha256(clang_version_info.encode('utf-8')).hexdigest()
    )
