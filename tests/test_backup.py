"""Sicherung und Wiederherstellung; alle Daten liegen in Temp-Ordnern."""

import zipfile

import pytest

from kinderbuch_bildlabor import backup, store


@pytest.fixture(autouse=True)
def temp_data(tmp_path, monkeypatch):
    data = tmp_path / "live"
    monkeypatch.setattr(store, "DATA_DIR", data)
    monkeypatch.setattr(store, "WORK_DIR", data / "data" / "work")
    monkeypatch.setattr(store, "EXPORT_DIR", data / "exports")
    for rel, text in {
        "data/work/a.json": '{"a": 1}',
        "data/work/.history/h1": "alt",
        "data/imports/buch/x.json": "{}",
        "exports/a.csv": "x;y",
    }.items():
        path = data / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return data


def rewrite(src, dst, change):
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w") as zout:
        for info in zin.infolist():
            data = change(info.filename, zin.read(info))
            if data is not None:
                zout.writestr(info.filename, data)


@pytest.fixture
def pkg(tmp_path):
    path = tmp_path / "out" / "p.zip"
    assert backup.create_backup(path) == 4
    return path


def test_roundtrip_and_sources_excluded(pkg, tmp_path):
    with zipfile.ZipFile(pkg) as zf:
        names = set(zf.namelist())
    assert names == {
        backup.MANIFEST,
        "data/work/a.json",
        "data/work/.history/h1",
        "data/imports/buch/x.json",
        "exports/a.csv",
    }
    assert backup.verify_backup(pkg) == []
    target = tmp_path / "neu"
    assert backup.restore_backup(pkg, target) == 4
    assert (target / "data/work/.history/h1").read_text() == "alt"
    assert (target / "exports/a.csv").read_text() == "x;y"


def test_create_refuses_existing_and_inside_data(pkg, tmp_path):
    with pytest.raises(backup.BackupError):
        backup.create_backup(pkg)
    with pytest.raises(backup.BackupError):
        backup.create_backup(store.EXPORT_DIR / "p.zip")


def test_tampered_missing_extra(pkg, tmp_path):
    def tamper(name, data):
        return b"x" if name == "exports/a.csv" else data

    def drop(name, data):
        return None if name == "data/work/a.json" else data

    def extra(name, data):
        return data

    for fn, text in (
        (tamper, "weicht ab"),
        (drop, "Fehlt"),
        (extra, "Nicht im Manifest"),
    ):
        out = tmp_path / f"{fn.__name__}.zip"
        rewrite(pkg, out, fn)
        if fn is extra:
            with zipfile.ZipFile(out, "a") as zf:
                zf.writestr("data/work/zusatz.json", "{}")
        assert any(text in p for p in backup.verify_backup(out))
        with pytest.raises(backup.BackupError):
            backup.restore_backup(out, tmp_path / f"t_{fn.__name__}")
        assert not (tmp_path / f"t_{fn.__name__}").exists()


def test_zip_slip_rejected(pkg, tmp_path):
    out = tmp_path / "slip.zip"
    rewrite(pkg, out, lambda n, d: d)
    with zipfile.ZipFile(out, "a") as zf:
        zf.writestr("data/../../evil.txt", "x")
    assert any("Unzulässig" in p for p in backup.verify_backup(out))
    with pytest.raises(backup.BackupError):
        backup.restore_backup(out, tmp_path / "t")
    assert not (tmp_path / "evil.txt").exists()


def test_nonempty_target_untouched(pkg, tmp_path):
    target = tmp_path / "voll"
    target.mkdir()
    (target / "mein.txt").write_text("wichtig")
    with pytest.raises(backup.BackupError):
        backup.restore_backup(pkg, target)
    assert [p.name for p in target.iterdir()] == ["mein.txt"]
    empty = tmp_path / "leer"
    empty.mkdir()
    backup.restore_backup(pkg, empty)
    assert (empty / "exports/a.csv").exists()


def test_cli(pkg, tmp_path, capsys):
    assert backup.main(["verify", str(pkg)]) == 0
    assert backup.main(["restore", str(pkg), str(tmp_path / "cli")]) == 0
    assert (tmp_path / "cli/data/work/a.json").exists()
    assert backup.main(["restore", str(pkg), str(tmp_path / "cli")]) == 1
    assert backup.main(["create", str(pkg)]) == 1
    assert "nichts überschrieben" in capsys.readouterr().err
