import hashlib
import os
import os.path as path
import platform
import subprocess
from typing import List

_BAZEL_REMOTE_CACHE_FLAG_ENV_VAR_NAME = "BAZEL_DISABLE_REMOTE_CACHE"
_BAZEL_REMOTE_CACHE_BUCKET_NAME_ENV_VAR_NAME = "BAZEL_REMOTE_CACHE_BUCKET_NAME"
_REMOTE_CACHE_BASE_URL = "https://storage.googleapis.com"
_DEFAULT_REMOTE_CACHE_BUCKET_NAME = "bazel-dev-remote-cache"


def remote_cache_flags_for(os_name, config_dir=os.path.expanduser("~")):
    os_name_lower = os_name.lower()
    if os_name_lower == "darwin" and os.environ.get(_BAZEL_REMOTE_CACHE_FLAG_ENV_VAR_NAME, "0") != "1":
        return RemoteCacheFlagsResolver(
            config_dir=config_dir,
            os_name=os_name_lower,
            env_fingerprint=_macos_fingerprint
        ).resolve_remote_cache_flags()
    else:
        return []


class RemoteCacheFlagsResolver:
    def __init__(self, config_dir, os_name, env_fingerprint):
        self.config_dir = config_dir
        self.os_name = os_name
        self.env_fingerprint = env_fingerprint

    def resolve_remote_cache_flags(self) -> List[str]:
        remote_cache_args = []

        def gcloud_credentials_path_or_none():
            gcloud_cred_path = path.join(self.config_dir, ".config", "gcloud", "application_default_credentials.json")
            if path.exists(gcloud_cred_path):
                return gcloud_cred_path

            return None

        gcloud_credentials_path = gcloud_credentials_path_or_none()
        if gcloud_credentials_path is None:
            return remote_cache_args

        remote_cache_args.append(
            "--remote_http_cache={base_url}/{bucket_name}/{path}/{macos_env_fingerprint}".format(
                base_url=_REMOTE_CACHE_BASE_URL,
                bucket_name=remote_cache_bucket_name(),
                path=self.os_name,
                macos_env_fingerprint=self.env_fingerprint(),
            )
        )
        remote_cache_args.append("--experimental_guard_against_concurrent_changes")
        remote_cache_args.append("--google_credentials={}".format(gcloud_credentials_path))

        return remote_cache_args


def remote_cache_bucket_name():
    return os.environ.get(_BAZEL_REMOTE_CACHE_BUCKET_NAME_ENV_VAR_NAME, _DEFAULT_REMOTE_CACHE_BUCKET_NAME)


def _macos_fingerprint():
    def clang_version():
        return subprocess.run(["clang", "--version"],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              encoding='utf-8').stdout

    os_version = platform.mac_ver()[0]
    clang_version_info = clang_version()
    return "{os_version}/{clang_fingerprint}".format(
        os_version=os_version,
        clang_fingerprint=hashlib.sha256(clang_version_info.encode('utf-8')).hexdigest()
    )
