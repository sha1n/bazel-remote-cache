import os
import platform
import subprocess
import sys

import remotecache

custom_bazel_env = {
    # here we can take control over the PATH or set env variables for other tools and bazel rules.
    # these are currently laid over the global shell env.

    # NOTE! bazelisk 'USE_BAZEL_VERSION' cannot be used in a wrapper script, because when that script executes, bazelisk
    # has already determined the version and we do not want to make recursive calls, or implement bazelisk logic
    # ourselves.
}


def extract_user_args():
    args = []
    sys.argv.pop(0)  # remove the wrapper script argument
    for arg in sys.argv:
        args.append(arg)

    return args


def bazel_env():
    return {**os.environ, **custom_bazel_env}


def _resolve_workspace_dir():
    current_dir = os.getcwd()
    ws_dir = current_dir
    while ws_dir != "/":
        if os.path.exists(os.path.join(ws_dir, "WORKSPACE")):
            return ws_dir
        else:
            ws_dir = os.path.abspath(os.path.join(ws_dir, os.pardir))

    return ws_dir


def build_bazel_command():
    user_args = extract_user_args()
    bazel_command = [
        os.environ["BAZEL_REAL"]  # this is set by the calling bazel command
    ]

    if "info" not in user_args and "version" not in user_args:
        target_list_found = False
        for user_arg in user_args:
            if user_arg == "--":  # target list must come last
                target_list_found = True
                bazel_command = bazel_command + remotecache.remote_cache_flags_for(platform.system())

            bazel_command.append(user_arg)

        if not target_list_found:
            bazel_command = bazel_command + remotecache.remote_cache_flags_for(platform.system())
    else:
        bazel_command = bazel_command + user_args

    return bazel_command


def main():
    subprocess.call(args=build_bazel_command(), env=bazel_env())
