# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import importlib.util
import os
import re
import subprocess
import time
import zipfile
from collections.abc import Iterator
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts/lxd-dev"
loader = SourceFileLoader("lxd_dev", str(SCRIPT_PATH))
spec = importlib.util.spec_from_loader(loader.name, loader)
assert spec is not None
lxd_dev = importlib.util.module_from_spec(spec)
loader.exec_module(lxd_dev)


def make_archive(path: Path, filename: str = "dump/toc.dat") -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(filename, "directory dump")


def test_extract_snapshot_archive_rejects_non_zip(tmp_path: Path) -> None:
    archive = tmp_path / "not-a-zip.zip"
    archive.write_text("not a zip")

    with pytest.raises(SystemExit):
        lxd_dev.extract_snapshot_archive(str(archive))


@pytest.mark.parametrize("unsafe_path", ["../escape/toc.dat", "/absolute/toc.dat", "dump\\escape"])
def test_extract_snapshot_archive_rejects_unsafe_paths(tmp_path: Path, unsafe_path: str) -> None:
    archive = tmp_path / "unsafe.zip"
    make_archive(archive, unsafe_path)

    with pytest.raises(SystemExit):
        lxd_dev.extract_snapshot_archive(str(archive))


def test_extract_snapshot_archive_accepts_directory_dump(tmp_path: Path) -> None:
    archive = tmp_path / "snapshot.zip"
    make_archive(archive)

    temporary, dump_dir, restore_list = lxd_dev.extract_snapshot_archive(str(archive))
    try:
        assert (dump_dir / "toc.dat").read_text() == "directory dump"
        assert dump_dir.name == "dump"
        assert restore_list.parent == Path(temporary.name) and restore_list.name.startswith(".lxd-dev-restore-")
    finally:
        temporary.cleanup()


def test_should_seed_database_marks_uninitialized_database_pending(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(lxd_dev, "DATABASE_STATE_FILE", tmp_path / "database-state.json")
    monkeypatch.setattr(lxd_dev, "database_is_initialized", lambda: False)

    assert lxd_dev.should_seed_database() is True
    assert lxd_dev.read_database_state() == {"initialized": False, "source": "seeded"}


def test_should_seed_database_preserves_initialized_database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    state_file = tmp_path / "database-state.json"
    monkeypatch.setattr(lxd_dev, "DATABASE_STATE_FILE", state_file)
    monkeypatch.setattr(lxd_dev, "database_is_initialized", lambda: True)
    lxd_dev.write_database_state(initialized=False, source="seeded")

    assert lxd_dev.should_seed_database() is True

    lxd_dev.write_database_state(initialized=True, source="snapshot")
    assert lxd_dev.should_seed_database() is False
    assert lxd_dev.read_database_state() == {"initialized": True, "source": "snapshot"}


def test_should_seed_database_keeps_legacy_initialized_database(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    state_file = tmp_path / "database-state.json"
    monkeypatch.setattr(lxd_dev, "DATABASE_STATE_FILE", state_file)
    monkeypatch.setattr(lxd_dev, "database_is_initialized", lambda: True)

    assert lxd_dev.should_seed_database() is False
    assert lxd_dev.read_database_state() == {"initialized": True, "source": "existing"}


def test_ensure_node_falls_back_when_compatible_node_has_no_npm(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    system_node = tmp_path / "system-node/bin"
    system_node.mkdir(parents=True)
    (system_node / "node").touch()
    pinned_node = tmp_path / ".local/opt" / f"node-v{lxd_dev.NODE_VERSION}"
    pinned_bin = pinned_node / "bin"
    pinned_bin.mkdir(parents=True)
    (pinned_bin / "node").touch()
    (pinned_bin / "npm").touch()
    (pinned_bin / "npm").chmod(0o755)
    monkeypatch.setattr(lxd_dev.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(lxd_dev.shutil, "which", lambda _command: str(system_node / "node"))

    def fake_run(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if args == ["node", "--version"]:
            return subprocess.CompletedProcess(args, 0, stdout="v22.14.0")
        return subprocess.CompletedProcess(args, 0, stdout="10.9.2")

    monkeypatch.setattr(lxd_dev, "run", fake_run)

    assert lxd_dev.ensure_node() == pinned_bin


def test_write_nginx_config_routes_simplesaml_php_through_fpm(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(lxd_dev, "STATE_DIR", tmp_path / "state")
    monkeypatch.setattr(lxd_dev, "SYSTEM_STATE_DIR", tmp_path / "system-state")
    monkeypatch.setattr(lxd_dev, "sudo", lambda *_args, **_kwargs: None)

    config_path, _prefix = lxd_dev.write_nginx_config(tmp_path / "simplesaml")

    config = config_path.read_text()
    php_location = "location ~ ^(?<prefix>/simplesaml)(?<phpfile>.+?\\.php)"
    assert php_location in config
    assert "location ^~ /simplesaml" not in config
    public_dir = tmp_path / "simplesaml" / "public"
    assert f'alias "{public_dir}/";' in config
    assert "fastcgi_pass unix:/run/php/php8.3-fpm.sock;" in config
    assert re.match(
        r"^/simplesaml(?P<phpfile>.+?\.php)(?P<pathinfo>/.*)?$",
        "/simplesaml/saml2/idp/metadata.php",
    )


def test_wait_for_seed_completion_uses_new_seed_log_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log_path = tmp_path / "api.log"
    stale_marker = "Database seeding completed successfully!\n"
    log_path.write_text(stale_marker)
    monkeypatch.setattr(lxd_dev, "is_process_alive", lambda *_args: True)
    monotonic_values = iter([0, 0, 2])
    monkeypatch.setattr(lxd_dev.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(lxd_dev.time, "sleep", lambda _delay: None)

    with pytest.raises(SystemExit):
        lxd_dev.wait_for_seed_completion(42, log_path, len(stale_marker.encode()), timeout=1)
    assert "Timed out waiting for initial database seeding" in capsys.readouterr().err

    with log_path.open("a") as log:
        log.write("Starting database seed...\nDatabase seeding completed successfully!\n")
    monkeypatch.setattr(lxd_dev.time, "monotonic", lambda: 0)
    lxd_dev.wait_for_seed_completion(42, log_path, len(stale_marker.encode()), timeout=1)


def test_stop_api_does_not_signal_reused_pid(monkeypatch: pytest.MonkeyPatch) -> None:
    liveness_checks: list[str | None] = []
    alive_results = iter([True, False, False])
    signals: list[tuple[int, int]] = []

    def fake_is_process_alive(_pid: object, expected: str | None = None) -> bool:
        liveness_checks.append(expected)
        return next(alive_results)

    monkeypatch.setattr(lxd_dev, "is_process_alive", fake_is_process_alive)
    monkeypatch.setattr(lxd_dev.os, "killpg", lambda pid, sig: signals.append((pid, sig)))
    monkeypatch.setattr(lxd_dev.time, "monotonic", lambda: 0)
    monkeypatch.setattr(lxd_dev.time, "sleep", lambda _delay: None)

    lxd_dev.stop_api(123)

    assert signals == [(123, lxd_dev.signal.SIGTERM)]
    assert liveness_checks == [str(lxd_dev.BACKEND / "dev_entrypoint.sh")] * 3


def test_signal_nginx_pid_does_not_signal_reused_pid(monkeypatch: pytest.MonkeyPatch) -> None:
    pidfds_opened: list[int] = []
    pidfds_closed: list[int] = []
    signals: list[tuple[int, int]] = []
    proc_cmdline = Path("/proc/456/cmdline")
    original_read_bytes = Path.read_bytes

    def fake_read_bytes(path: Path) -> bytes:
        if path == proc_cmdline:
            return b"unrelated-service\0--worker\0"
        return original_read_bytes(path)

    monkeypatch.setattr(lxd_dev.os, "pidfd_open", lambda pid: pidfds_opened.append(pid) or 89)
    monkeypatch.setattr(lxd_dev.os, "close", lambda pidfd: pidfds_closed.append(pidfd))
    monkeypatch.setattr(lxd_dev.signal, "pidfd_send_signal", lambda pidfd, sig: signals.append((pidfd, sig)))
    monkeypatch.setattr(Path, "read_bytes", fake_read_bytes)

    assert (
        lxd_dev.signal_nginx_pid(
            456,
            Path("/home/user/.local/state/test-observer/lxd-dev/nginx.conf"),
            Path("/var/lib/test-observer-lxd-dev/nginx"),
            lxd_dev.signal.SIGQUIT,
        )
        is False
    )

    assert pidfds_opened == [456]
    assert pidfds_closed == [89]
    assert signals == []


def test_signal_nginx_pid_signals_matching_private_master(monkeypatch: pytest.MonkeyPatch) -> None:
    pidfd_signals: list[tuple[int, int]] = []
    proc_cmdline = Path("/proc/456/cmdline")
    original_read_bytes = Path.read_bytes

    def fake_read_bytes(path: Path) -> bytes:
        if path == proc_cmdline:
            return (
                b"nginx: master process /usr/sbin/nginx -c /tmp/lxd-dev/nginx.conf "
                b"-p /var/lib/test-observer-lxd-dev/nginx/\0"
            )
        return original_read_bytes(path)

    monkeypatch.setattr(lxd_dev.os, "pidfd_open", lambda _pid: 89)
    monkeypatch.setattr(lxd_dev.os, "close", lambda _pidfd: None)
    monkeypatch.setattr(
        lxd_dev.signal,
        "pidfd_send_signal",
        lambda pidfd, sig: pidfd_signals.append((pidfd, sig)),
    )
    monkeypatch.setattr(Path, "read_bytes", fake_read_bytes)

    assert (
        lxd_dev.signal_nginx_pid(
            456,
            Path("/tmp/lxd-dev/nginx.conf"),
            Path("/var/lib/test-observer-lxd-dev/nginx"),
            lxd_dev.signal.SIGQUIT,
        )
        is True
    )

    assert pidfd_signals == [(89, lxd_dev.signal.SIGQUIT)]


def test_stop_treats_mismatched_nginx_pid_as_stale_cleanup(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "nginx.conf").touch()
    system_state_dir = tmp_path / "system-state"
    pid_path = system_state_dir / "nginx/nginx.pid"
    monkeypatch.setattr(lxd_dev, "STATE_DIR", state_dir)
    monkeypatch.setattr(lxd_dev, "STATE_FILE", state_dir / "state.json")
    monkeypatch.setattr(lxd_dev, "SYSTEM_STATE_DIR", system_state_dir)
    monkeypatch.setattr(lxd_dev, "privileged_path_exists", lambda path: path == pid_path)
    monkeypatch.setattr(lxd_dev, "stop_api", lambda *_args: None)
    monkeypatch.setattr(lxd_dev.os, "pidfd_open", lambda _pid: 89)
    monkeypatch.setattr(lxd_dev.os, "close", lambda _pidfd: None)
    monkeypatch.setattr(
        lxd_dev.signal,
        "pidfd_send_signal",
        lambda *_args: pytest.fail("reused nginx PID was signaled"),
    )
    original_read_bytes = Path.read_bytes

    def fake_read_bytes(path: Path) -> bytes:
        if path == Path("/proc/456/cmdline"):
            return b"unrelated-service\0--worker\0"
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", fake_read_bytes)
    commands: list[list[str]] = []

    def fake_sudo(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(args)
        if args[:2] == ["cat", str(pid_path)]:
            return subprocess.CompletedProcess(args, 0, stdout="456\n")
        assert args[2] == "--signal-nginx"
        status = lxd_dev.nginx_signal_command(args[3:])
        return subprocess.CompletedProcess(args, status)

    monkeypatch.setattr(lxd_dev, "sudo", fake_sudo)

    lxd_dev.stop({})

    assert commands[0] == ["cat", str(pid_path)]
    assert commands[1][2:] == [
        "--signal-nginx",
        "456",
        str(state_dir / "nginx.conf"),
        str(system_state_dir / "nginx"),
        "QUIT",
    ]
    assert all("-s" not in command and "kill" not in command for command in commands)


def test_privileged_path_exists_distinguishes_sudo_failure_from_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "nginx.pid"
    statuses = iter([1, 10, 0])
    commands: list[list[str]] = []

    def fake_sudo(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(args)
        return subprocess.CompletedProcess(args, next(statuses))

    monkeypatch.setattr(lxd_dev, "sudo", fake_sudo)

    with pytest.raises(RuntimeError, match="exit status 1"):
        lxd_dev.privileged_path_exists(path)
    assert lxd_dev.privileged_path_exists(path) is False
    assert lxd_dev.privileged_path_exists(path) is True
    assert all(command[1:3] == [str(SCRIPT_PATH), "--path-exists"] for command in commands)


def test_privileged_path_exists_helper_returns_distinct_missing_status(tmp_path: Path) -> None:
    existing_file = tmp_path / "existing"
    existing_file.touch()

    assert lxd_dev.privileged_path_exists_command([str(tmp_path / "missing"), "any"]) == 10
    assert lxd_dev.privileged_path_exists_command([str(existing_file), "any"]) == 0
    assert lxd_dev.privileged_path_exists_command([str(existing_file), "directory"]) == 10


def test_privileged_path_exists_helper_reports_stat_errors(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail_stat(_path: Path) -> os.stat_result:
        raise PermissionError("inspection denied")

    monkeypatch.setattr(Path, "stat", fail_stat)

    assert lxd_dev.privileged_path_exists_command(["/restricted/path", "any"]) == 2
    assert "inspection denied" in capsys.readouterr().err


def test_stop_retains_nginx_state_when_privileged_path_check_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    state_file = tmp_path / "state.json"
    state = {"api_pid": 123}
    state_file.write_text(lxd_dev.json.dumps(state))
    monkeypatch.setattr(lxd_dev, "STATE_FILE", state_file)
    monkeypatch.setattr(lxd_dev, "STATE_DIR", tmp_path)
    monkeypatch.setattr(lxd_dev, "SYSTEM_STATE_DIR", tmp_path / "system-state")
    monkeypatch.setattr(lxd_dev, "stop_api", lambda *_args: None)

    def sudo_status_one(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        assert "--path-exists" in args
        return subprocess.CompletedProcess(args, 1)

    monkeypatch.setattr(lxd_dev, "sudo", sudo_status_one)

    with pytest.raises(SystemExit) as error:
        lxd_dev.stop(state)

    assert error.value.code == 1
    assert lxd_dev.json.loads(state_file.read_text()) == state


def test_stop_cleans_state_when_nginx_pid_path_is_verified_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    state_file = tmp_path / "state.json"
    state = {"api_pid": 123}
    state_file.write_text(lxd_dev.json.dumps(state))
    monkeypatch.setattr(lxd_dev, "STATE_FILE", state_file)
    monkeypatch.setattr(lxd_dev, "STATE_DIR", tmp_path)
    monkeypatch.setattr(lxd_dev, "SYSTEM_STATE_DIR", tmp_path / "system-state")
    monkeypatch.setattr(lxd_dev, "stop_api", lambda *_args: None)

    def missing_path(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        assert "--path-exists" in args
        return subprocess.CompletedProcess(args, 10)

    monkeypatch.setattr(lxd_dev, "sudo", missing_path)

    lxd_dev.stop(state)

    assert not state_file.exists()


@pytest.mark.parametrize("failure", ["pid-file-read", "helper-invocation", "helper-permission"])
def test_stop_retains_state_when_nginx_identity_cannot_be_verified(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, failure: str
) -> None:
    state_file = tmp_path / "state.json"
    state = {"api_pid": 123}
    state_file.write_text(lxd_dev.json.dumps(state))
    config_path = tmp_path / "nginx.conf"
    config_path.touch()
    pid_path = tmp_path / "system-state/nginx/nginx.pid"
    pid_path.parent.mkdir(parents=True)
    monkeypatch.setattr(lxd_dev, "STATE_DIR", tmp_path)
    monkeypatch.setattr(lxd_dev, "STATE_FILE", state_file)
    monkeypatch.setattr(lxd_dev, "SYSTEM_STATE_DIR", tmp_path / "system-state")
    monkeypatch.setattr(lxd_dev, "stop_api", lambda *_args: None)
    monkeypatch.setattr(lxd_dev, "privileged_path_exists", lambda _path: True)
    original_unlink = Path.unlink
    state_unlinks: list[Path] = []

    def track_unlink(path: Path, *args: object, **kwargs: object) -> None:
        if path == state_file:
            state_unlinks.append(path)
        original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", track_unlink)

    def fake_sudo(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if args[:2] == ["cat", str(pid_path)]:
            if failure == "pid-file-read":
                return subprocess.CompletedProcess(args, 1, stdout="")
            return subprocess.CompletedProcess(args, 0, stdout="456\n")
        if "--signal-nginx" in args:
            if failure == "helper-invocation":
                raise PermissionError("sudo could not invoke helper")
            if failure == "helper-permission":
                # sudo uses status 1 when permission policy denies a command;
                # that must not be confused with the helper's stale-PID result.
                return subprocess.CompletedProcess(args, 1)
        pytest.fail(f"Unexpected privileged command: {args}")

    monkeypatch.setattr(lxd_dev, "sudo", fake_sudo)

    with pytest.raises(SystemExit) as error:
        lxd_dev.stop(state)

    assert error.value.code == 1
    assert lxd_dev.json.loads(state_file.read_text()) == state
    assert state_unlinks == []


@pytest.mark.parametrize(
    ("read_error", "expected"),
    [(FileNotFoundError("process exited"), False), (PermissionError("proc denied"), RuntimeError)],
)
def test_nginx_identity_inspection_distinguishes_disappearance_from_access_failure(
    monkeypatch: pytest.MonkeyPatch,
    read_error: OSError,
    expected: bool | type[RuntimeError],
) -> None:
    def fail_read(_path: Path) -> bytes:
        raise read_error

    monkeypatch.setattr(Path, "read_bytes", fail_read)

    if expected is RuntimeError:
        with pytest.raises(RuntimeError, match="could not inspect nginx PID"):
            lxd_dev.nginx_process_matches(456, Path("/tmp/nginx.conf"), Path("/tmp/nginx"))
    else:
        assert lxd_dev.nginx_process_matches(456, Path("/tmp/nginx.conf"), Path("/tmp/nginx")) is expected


def test_stop_api_retries_transient_empty_session_discovery(monkeypatch: pytest.MonkeyPatch) -> None:
    session_scans = iter([[], [456], *([[]] * 20)])
    signals: list[int] = []
    now = [0.0]

    monkeypatch.setattr(lxd_dev, "api_session_processes", lambda _pid, _token: next(session_scans, []))
    monkeypatch.setattr(lxd_dev, "signal_api_session", lambda _pid, _token, sig: signals.append(sig))
    monkeypatch.setattr(lxd_dev.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(lxd_dev.time, "sleep", lambda delay: now.__setitem__(0, now[0] + delay))

    lxd_dev.stop_api(123, "test-token")

    assert signals == [lxd_dev.signal.SIGTERM, lxd_dev.signal.SIGTERM]
    assert now[0] >= 0.6


def test_signal_api_session_reports_missing_pidfd_support(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(lxd_dev.os, "pidfd_open", None)
    monkeypatch.setattr(lxd_dev.signal, "pidfd_send_signal", None)

    assert lxd_dev.signal_api_session(123, "test-token", lxd_dev.signal.SIGTERM) is False


@pytest.mark.parametrize("pidfd_mode", ["unavailable", "signal-denied"])
def test_stop_retains_state_when_api_cleanup_cannot_be_verified(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    pidfd_mode: str,
) -> None:
    state_file = tmp_path / "state.json"
    state = {"api_pid": 123, "api_group_token": "test-token"}
    state_file.write_text(lxd_dev.json.dumps(state))
    monkeypatch.setattr(lxd_dev, "STATE_DIR", tmp_path)
    monkeypatch.setattr(lxd_dev, "STATE_FILE", state_file)
    monkeypatch.setattr(lxd_dev, "privileged_path_exists", lambda _path: False)
    monkeypatch.setattr(lxd_dev, "ensure_privileges", lambda: None)
    monkeypatch.setattr(lxd_dev, "api_session_processes", lambda _pid, _token: [456])
    monkeypatch.setattr(lxd_dev.os, "killpg", lambda *_args: pytest.fail("unsafe process-group signal attempted"))
    now = [0.0]
    monkeypatch.setattr(lxd_dev.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(lxd_dev.time, "sleep", lambda delay: now.__setitem__(0, now[0] + delay))

    if pidfd_mode == "unavailable":
        monkeypatch.setattr(lxd_dev.os, "pidfd_open", None)
        monkeypatch.setattr(lxd_dev.signal, "pidfd_send_signal", None)
    else:
        monkeypatch.setattr(lxd_dev.os, "pidfd_open", lambda _pid: os.open(os.devnull, os.O_RDONLY))

        def deny_signal(_pidfd: int, _sig: int) -> None:
            raise PermissionError("signal denied")

        monkeypatch.setattr(lxd_dev.signal, "pidfd_send_signal", deny_signal)

    with pytest.raises(SystemExit) as error:
        lxd_dev.down()

    assert error.value.code == 1
    assert lxd_dev.json.loads(state_file.read_text()) == state
    output = capsys.readouterr()
    assert "Could not stop the API safely" in output.err
    assert f"State retained at {state_file}" in output.err
    assert "development services stopped" not in output.out


@pytest.mark.parametrize("failure_point", ["stat", "environ", "identity-recheck"])
def test_down_retains_state_when_process_identity_scan_is_incomplete(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    failure_point: str,
) -> None:
    state_file = tmp_path / "state.json"
    state = {"api_pid": 123, "api_group_token": "test-token"}
    state_file.write_text(lxd_dev.json.dumps(state))
    monkeypatch.setattr(lxd_dev, "STATE_DIR", tmp_path)
    monkeypatch.setattr(lxd_dev, "STATE_FILE", state_file)
    monkeypatch.setattr(lxd_dev, "privileged_path_exists", lambda _path: False)
    monkeypatch.setattr(lxd_dev, "ensure_privileges", lambda: None)
    monkeypatch.setattr(lxd_dev.os, "killpg", lambda *_args: pytest.fail("unsafe process-group signal attempted"))

    proc_dir = Path("/proc/456")
    proc_stat = proc_dir / "stat"
    proc_environ = proc_dir / "environ"
    process_stat = "456 (api) S 0 0 123 0\n"
    original_iterdir = Path.iterdir
    original_read_text = Path.read_text
    original_read_bytes = Path.read_bytes
    procfd_opened = False
    environment_reads = 0

    def fake_iterdir(path: Path) -> Iterator[Path]:
        if path == Path("/proc"):
            return iter([proc_dir])
        return original_iterdir(path)

    def fake_read_text(path: Path, *args: object, **kwargs: object) -> str:
        if path == proc_stat:
            if failure_point == "stat":
                raise PermissionError("stat denied")
            return process_stat
        return original_read_text(path, *args, **kwargs)

    def fake_read_bytes(path: Path) -> bytes:
        nonlocal environment_reads
        if path == proc_environ:
            environment_reads += 1
            if failure_point == "environ" or (
                failure_point == "identity-recheck" and procfd_opened and environment_reads > 1
            ):
                raise PermissionError("environment denied")
            return b"LXD_DEV_API_GROUP_TOKEN=test-token\0"
        return original_read_bytes(path)

    opened_pids: list[int] = []
    signals: list[tuple[int, int]] = []

    def fake_pidfd_open(pid: int) -> int:
        nonlocal procfd_opened
        procfd_opened = True
        opened_pids.append(pid)
        return 987

    monkeypatch.setattr(Path, "iterdir", fake_iterdir)
    monkeypatch.setattr(Path, "read_text", fake_read_text)
    monkeypatch.setattr(Path, "read_bytes", fake_read_bytes)
    monkeypatch.setattr(lxd_dev.os, "pidfd_open", fake_pidfd_open, raising=False)
    monkeypatch.setattr(
        lxd_dev.signal,
        "pidfd_send_signal",
        lambda pidfd, sig: signals.append((pidfd, sig)),
        raising=False,
    )
    monkeypatch.setattr(lxd_dev.os, "close", lambda _fd: None)

    with pytest.raises(SystemExit) as error:
        lxd_dev.down()

    assert error.value.code == 1
    assert lxd_dev.json.loads(state_file.read_text()) == state
    assert signals == []
    assert opened_pids == ([456] if failure_point == "identity-recheck" else [])
    output = capsys.readouterr()
    assert "Could not stop the API safely" in output.err
    assert f"State retained at {state_file}" in output.err
    assert "development services stopped" not in output.out


@pytest.mark.parametrize("vanish_at", ["stat", "environ"])
def test_api_session_process_scan_tolerates_process_disappearance(
    monkeypatch: pytest.MonkeyPatch, vanish_at: str
) -> None:
    proc_dir = Path("/proc/456")
    proc_stat = proc_dir / "stat"
    proc_environ = proc_dir / "environ"
    original_iterdir = Path.iterdir
    original_read_text = Path.read_text
    original_read_bytes = Path.read_bytes

    def fake_iterdir(path: Path) -> Iterator[Path]:
        if path == Path("/proc"):
            return iter([proc_dir])
        return original_iterdir(path)

    def fake_read_text(path: Path, *args: object, **kwargs: object) -> str:
        if path == proc_stat:
            if vanish_at == "stat":
                raise FileNotFoundError("process exited")
            return "456 (api) S 0 0 123 0\n"
        return original_read_text(path, *args, **kwargs)

    def fake_read_bytes(path: Path) -> bytes:
        if path == proc_environ:
            raise ProcessLookupError("process exited")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "iterdir", fake_iterdir)
    monkeypatch.setattr(Path, "read_text", fake_read_text)
    monkeypatch.setattr(Path, "read_bytes", fake_read_bytes)

    assert lxd_dev.api_session_processes(123, "test-token") == []


def start_failed_api_wrapper(tmp_path: Path, token: str) -> tuple[subprocess.Popen[bytes], int]:
    child_pid_path = tmp_path / "uvicorn.pid"
    wrapper = tmp_path / "dev_entrypoint.sh"
    wrapper.write_text(
        "#!/bin/bash\n"
        "set -e\n"
        "bash -c 'exec -a uvicorn /bin/sleep 120' &\n"
        f"echo $! > {child_pid_path}\n"
        "false # Simulates seed_data.py exiting after uvicorn has started.\n"
    )
    wrapper.chmod(0o755)
    env = os.environ.copy()
    env["LXD_DEV_API_GROUP_TOKEN"] = token
    process = subprocess.Popen([str(wrapper)], start_new_session=True, env=env)
    assert process.wait(timeout=5) == 1
    return process, int(child_pid_path.read_text())


def process_is_running(pid: int) -> bool:
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    except OSError:
        return False
    return fields[0] != "Z"


def test_stop_api_cleans_up_uvicorn_after_seed_failure_exits_wrapper(tmp_path: Path) -> None:
    token = "seed-failure-test-token"
    wrapper, child_pid = start_failed_api_wrapper(tmp_path, token)

    try:
        assert process_is_running(child_pid)
        # Do not require a one-shot /proc scan to discover the child; stop_api
        # must cope with transient misses and still remove this orphan.
        lxd_dev.stop_api(wrapper.pid, token)

        deadline = time.monotonic() + 2
        while process_is_running(child_pid) and time.monotonic() < deadline:
            time.sleep(0.02)
        assert not process_is_running(child_pid)
        assert lxd_dev.api_session_processes(wrapper.pid, token) == []
    finally:
        lxd_dev.stop_api(wrapper.pid, token)


def test_stop_api_does_not_signal_mismatched_api_group_identity(tmp_path: Path) -> None:
    token = "actual-api-group-token"
    wrapper, child_pid = start_failed_api_wrapper(tmp_path, token)

    try:
        lxd_dev.stop_api(wrapper.pid, "different-api-group-token")

        assert process_is_running(child_pid)
    finally:
        lxd_dev.stop_api(wrapper.pid, token)


def test_runtime_environment_uses_current_address() -> None:
    env: dict[str, str] = {}

    lxd_dev.configure_runtime_environment(env, "192.0.2.42")

    assert env == {
        "SAML_IDP_METADATA_URL": "http://192.0.2.42:8080/simplesaml/saml2/idp/metadata.php",
        "SAML_SP_BASE_URL": "http://192.0.2.42:30000",
        "FRONTEND_URL": "http://192.0.2.42:30001",
    }


def test_running_stack_with_unchanged_address_only_refreshes_saml(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(lxd_dev, "STATE_DIR", tmp_path)
    monkeypatch.setattr(lxd_dev, "STATE_FILE", state_file)
    lxd_dev.write_state({"api_pid": 42, "public_ip": "192.0.2.42"})
    monkeypatch.setattr(lxd_dev, "service_ip", lambda: "192.0.2.42")
    monkeypatch.setattr(lxd_dev, "is_process_alive", lambda *_args: True)
    monkeypatch.setattr(lxd_dev, "read_simple_saml_secrets", lambda: {"secretsalt": "test"})
    refreshed: list[str] = []
    monkeypatch.setattr(lxd_dev, "ensure_simple_saml", lambda _secrets, ip: refreshed.append(ip))
    monkeypatch.setattr(lxd_dev, "stop", lambda _state: pytest.fail("unchanged stack was stopped"))
    monkeypatch.setattr(lxd_dev, "build_frontend", lambda *_args: pytest.fail("frontend was rebuilt"))

    lxd_dev.up_stack(None)

    assert refreshed == ["192.0.2.42"]
    assert lxd_dev.read_state()["public_ip"] == "192.0.2.42"
    assert "API: http://192.0.2.42:30000" in capsys.readouterr().out


def test_running_stack_with_changed_address_restarts_and_uses_new_configuration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(lxd_dev, "STATE_DIR", tmp_path)
    monkeypatch.setattr(lxd_dev, "STATE_FILE", state_file)
    lxd_dev.write_state({"api_pid": 42, "public_ip": "192.0.2.41"})
    monkeypatch.setattr(lxd_dev, "service_ip", lambda: "192.0.2.42")
    monkeypatch.setattr(lxd_dev, "is_process_alive", lambda *_args: True)
    stopped: list[dict[str, object]] = []
    monkeypatch.setattr(lxd_dev, "stop", lambda state: stopped.append(state))
    monkeypatch.setattr(lxd_dev, "service_active", lambda _name: False)
    monkeypatch.setattr(lxd_dev, "ensure_apt_packages", lambda: None)
    monkeypatch.setattr(lxd_dev, "ensure_uv", lambda: Path("/uv"))
    monkeypatch.setattr(lxd_dev, "ensure_node", lambda: Path("/node"))
    monkeypatch.setattr(lxd_dev, "ensure_flutter", lambda: Path("/flutter"))
    monkeypatch.setattr(
        lxd_dev, "run", lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0, stdout="uv 0.11.15")
    )
    monkeypatch.setattr(lxd_dev, "source_fingerprint", lambda *_args, **_kwargs: "fingerprint")
    monkeypatch.setattr(lxd_dev, "read_build_cache", lambda: {})
    monkeypatch.setattr(lxd_dev, "save_build_cache", lambda _cache: None)
    frontend_config: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        lxd_dev,
        "build_frontend",
        lambda env, _flutter, _node, ip, _cache: frontend_config.append(
            (ip, env["SAML_IDP_METADATA_URL"], env["FRONTEND_URL"])
        ),
    )
    saml_addresses: list[str] = []
    monkeypatch.setattr(lxd_dev, "read_simple_saml_secrets", lambda: {})
    monkeypatch.setattr(
        lxd_dev,
        "ensure_simple_saml",
        lambda _secrets, ip: saml_addresses.append(ip) or tmp_path / "saml",
    )
    monkeypatch.setattr(lxd_dev, "systemctl", lambda *_args: None)
    monkeypatch.setattr(lxd_dev, "ensure_database", lambda: None)
    monkeypatch.setattr(lxd_dev, "should_seed_database", lambda: False)
    monkeypatch.setattr(lxd_dev, "write_nginx_config", lambda _saml: (tmp_path / "nginx.conf", tmp_path))
    monkeypatch.setattr(lxd_dev, "sudo", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(lxd_dev, "wait_http", lambda *_args, **_kwargs: None)
    api_environment: list[dict[str, str]] = []

    def fake_popen(*_args: object, **kwargs: object) -> SimpleNamespace:
        api_environment.append(kwargs["env"])
        return SimpleNamespace(pid=99)

    monkeypatch.setattr(lxd_dev.subprocess, "Popen", fake_popen)

    lxd_dev.up_stack(None)

    assert stopped == [{"api_pid": 42, "public_ip": "192.0.2.41"}]
    assert frontend_config == [
        (
            "192.0.2.42",
            "http://192.0.2.42:8080/simplesaml/saml2/idp/metadata.php",
            "http://192.0.2.42:30001",
        )
    ]
    assert saml_addresses == ["192.0.2.42"]
    assert lxd_dev.read_state()["public_ip"] == "192.0.2.42"
    assert api_environment[0]["SAML_SP_BASE_URL"] == "http://192.0.2.42:30000"
    assert api_environment[0]["SAML_IDP_METADATA_URL"].startswith("http://192.0.2.42:")
    assert api_environment[0]["FRONTEND_URL"] == "http://192.0.2.42:30001"
    output = capsys.readouterr().out
    assert "API:       http://192.0.2.42:30000" in output
    assert "Frontend:  http://192.0.2.42:30001" in output
    assert "SAML IdP:  http://192.0.2.42:8080/simplesaml/" in output


def test_swap_database_restores_existing_database_if_snapshot_promotion_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    databases = {lxd_dev.DB_NAME, "staging"}
    statements: list[str] = []

    monkeypatch.setattr(lxd_dev, "database_exists", lambda name: name in databases)

    def fake_psql(_database: str, statement: str, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        statements.append(statement)
        if statement.startswith("ALTER DATABASE"):
            parts = statement.split()
            database_name, new_name = parts[2], parts[5]
            if database_name == "staging":
                raise subprocess.CalledProcessError(1, statement)
            databases.remove(database_name)
            databases.add(new_name)
        return subprocess.CompletedProcess([], 0)

    monkeypatch.setattr(lxd_dev, "postgres_psql", fake_psql)

    with pytest.raises(subprocess.CalledProcessError):
        lxd_dev.swap_database("staging")

    assert lxd_dev.DB_NAME in databases
    assert "staging" in databases
    assert not any(name.startswith("test_observer_old_") for name in databases)
    assert any(
        statement.startswith("ALTER DATABASE") and statement.endswith(f"TO {lxd_dev.DB_NAME}")
        for statement in statements
    )
