import subprocess
from types import SimpleNamespace

import pytest
from PIL import Image

from kinderbuch_bildlabor import ocr, review
from tests.test_review import _imported_record

LISTING = 'List of available languages in "{}" (2):\nfra\ndeu\n'


@pytest.fixture
def fake_tesseract(tmp_path, monkeypatch):
    (tmp_path / "deu.traineddata").write_bytes(b"model")
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        if "--list-langs" in command:
            return SimpleNamespace(stdout=LISTING.format(tmp_path), stderr="")
        if "--version" in command:
            return SimpleNamespace(stdout="tesseract 5.5.0\n", stderr="")
        return SimpleNamespace(stdout="Die Heimath\n", stderr="")

    monkeypatch.setattr(ocr.subprocess, "run", run)
    monkeypatch.setattr(ocr, "executable", lambda: "tesseract")
    return calls


def test_run_uses_argument_list_timeout_model_and_records_provenance(fake_tesseract):
    image = Image.new("RGB", (50, 40), "white")
    result = ocr.run_crop_ocr(image, "imagehash", [5, 5, 20, 10], "deu", 7)
    command, kwargs = fake_tesseract[-2]
    assert command[2] == "stdout"
    assert command[-4:] == ["-l", "deu", "--psm", "7"]
    assert kwargs["timeout"] == ocr.TIMEOUT and "shell" not in kwargs
    assert result["text"] == "Die Heimath"
    assert result["model_sha256"] and result["engine_version"] == "tesseract 5.5.0"
    assert result["xywh"] == [5, 5, 20, 10] and result["image_sha256"] == "imagehash"


def test_uninstalled_model_and_failures_are_actionable(fake_tesseract, monkeypatch):
    image = Image.new("RGB", (10, 10))
    with pytest.raises(ocr.OcrUnavailable, match="nicht installiert"):
        ocr.run_crop_ocr(image, "h", [0, 0, 5, 5], "frk", 7)

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("t", 1)

    monkeypatch.setattr(ocr.subprocess, "run", timeout)
    with pytest.raises(ocr.OcrUnavailable, match="Sekunden"):
        ocr.available_models()


def test_text_diff_is_literal():
    assert ocr.text_diff("Heimath", "Heimat") == [
        ("gleich", "Heimat"),
        ("entfernt", "h"),
    ]
    assert ocr.text_diff("ſo", "so") == [
        ("entfernt", "ſ"),
        ("hinzugefügt", "s"),
        ("gleich", "o"),
    ]


def candidate(record, text="Neu", crop="c1"):
    region = record["region_annotations"][1]
    return {
        "text": text,
        "engine_version": "t",
        "model": "deu",
        "model_sha256": "m",
        "psm": 7,
        "created_at": "2026-11-12T00:00:00+00:00",
        "image_sha256": "i",
        "crop_sha256": crop,
        "xywh": region["xywh"],
    }


def test_candidates_dedupe_reject_stale_and_do_not_confirm_transcription():
    record = _imported_record()
    review.add_region(record, "text", "Zeile", [1, 1, 5, 5], 1)
    region_id = record["region_annotations"][1]["id"]
    field = "text_02"
    review.confirm_transcription(record, field, "P", "")
    record["status"] = review.FINAL_APPROVED
    record["final_approval"] = {"by": "P"}
    assert review.save_ocr_candidate(record, region_id, candidate(record), "c1")
    assert record["status"] != review.FINAL_APPROVED
    assert not review.save_ocr_candidate(record, region_id, candidate(record), "c1")
    assert len(record["ocr_candidates"]) == 1
    assert (
        record["transcription"]["review_status_by_field"][field]
        == review.TRANSCRIPTION_REVIEWED
    )
    with pytest.raises(review.ContentChanged):
        review.save_ocr_candidate(
            record, region_id, candidate(record, "X"), "other-crop"
        )
    with pytest.raises(review.ContentChanged):
        review.adopt_ocr_candidate(
            record, region_id, record["ocr_candidates"][0]["id"], "", "other"
        )
    assert review.adopt_ocr_candidate(
        record, region_id, record["ocr_candidates"][0]["id"], "", "c1"
    )
    assert record["transcription"][field] == "Neu"
    assert (
        record["transcription"]["review_status_by_field"][field]
        == review.TRANSCRIPTION_PROVISIONAL
    )
