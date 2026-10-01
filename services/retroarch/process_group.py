"""Bounded termination of a process group created with start_new_session=True."""
import os
import signal
import subprocess


def group_exists(group):
    if type(group) is not int or group <= 1:
        return False
    try:
        os.killpg(group, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def terminate_group(process, group, wait_for_exit):
    if type(group) is not int or group <= 1 or group == os.getpgrp():
        raise RuntimeError("Refusing to signal an unowned process group.")
    def send(sig):
        try:
            os.killpg(group, sig)
        except ProcessLookupError:
            pass
    send(signal.SIGTERM)
    try:
        process.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        send(signal.SIGKILL)
        try:
            process.wait(timeout=5.0)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("RetroArch root process did not terminate.") from exc
    if not wait_for_exit(group, timeout=2.0):
        send(signal.SIGKILL)
        if not wait_for_exit(group, timeout=5.0):
            raise RuntimeError("RetroArch process group did not terminate completely.")
