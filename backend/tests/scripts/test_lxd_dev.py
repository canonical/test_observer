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
import subprocess
import zipfile
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
