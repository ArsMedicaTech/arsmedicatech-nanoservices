"""Tests for amt_nano.terminology.referral_business_status."""

import json

import pytest

from amt_nano.terminology.referral_business_status import (
    BUSINESS_STATUSES,
    CORE_TASK_STATUSES,
    STATUSES_WITHOUT_BUSINESS_STATUS,
    SYSTEM,
    VERSION,
    PairingError,
    applicable_status,
    business_status_of,
    codes_for_status,
    coding_for,
    local_text_only,
    task_status_of,
    validate_pairing,
)


@pytest.mark.unit
def test_concept_count_matches_valueset():
    """The ValueSet's first include carries exactly 38 pan-Canadian codes."""
    assert len(BUSINESS_STATUSES) == 38


@pytest.mark.unit
def test_every_concept_maps_to_a_core_status():
    for code, concept in BUSINESS_STATUSES.items():
        assert concept.task_status in CORE_TASK_STATUSES, code


@pytest.mark.unit
def test_key_matches_code():
    for code, concept in BUSINESS_STATUSES.items():
        assert code == concept.code


@pytest.mark.unit
def test_three_statuses_have_no_business_status():
    assert set(STATUSES_WITHOUT_BUSINESS_STATUS) == {"draft", "ready", "accepted"}


@pytest.mark.unit
@pytest.mark.parametrize(
    "business_status,expected",
    [
        ("awaiting-triage", "received"),
        ("awaiting-booking", "in-progress"),
        ("booked", "in-progress"),
        ("wait-listed", "on-hold"),
        ("redirected", "rejected"),
        ("no-capacity", "rejected"),
        ("service-refused-by-patient", "cancelled"),
        ("duplicate-request", "entered-in-error"),
        ("completed-with-advice", "completed"),
        ("invited", "requested"),
    ],
)
def test_applicable_status(business_status, expected):
    assert applicable_status(business_status) == expected


@pytest.mark.unit
def test_wait_listed_is_on_hold_not_in_progress():
    """Guards a plausible misreading: waitlisting is a held state, not an active one."""
    assert applicable_status("wait-listed") == "on-hold"


@pytest.mark.unit
def test_redirected_is_a_rejection():
    """`redirected` is 'rejected and redirected', not neutral routing."""
    assert applicable_status("redirected") == "rejected"


@pytest.mark.unit
def test_codes_for_status_is_sorted_and_complete():
    rejected = [b.code for b in codes_for_status("rejected")]
    assert rejected == sorted(rejected)
    assert "no-capacity" in rejected
    assert len(rejected) == 8


@pytest.mark.unit
@pytest.mark.parametrize("status", STATUSES_WITHOUT_BUSINESS_STATUS)
def test_codes_for_status_empty_for_unmapped(status):
    assert codes_for_status(status) == []


@pytest.mark.unit
def test_valid_pairing_passes():
    validate_pairing("rejected", "no-capacity")
    validate_pairing("in-progress", "booked")


@pytest.mark.unit
def test_absent_business_status_is_conformant():
    validate_pairing("accepted", None)
    validate_pairing("draft")


@pytest.mark.unit
def test_mismatched_pairing_raises():
    with pytest.raises(PairingError, match="applies to Task.status 'rejected'"):
        validate_pairing("completed", "no-capacity")


@pytest.mark.unit
def test_non_core_task_status_raises():
    with pytest.raises(PairingError, match="not a core FHIR TaskStatus"):
        validate_pairing("awaiting-triage", None)


@pytest.mark.unit
def test_unknown_business_status_raises():
    with pytest.raises(PairingError, match="local_text_only"):
        validate_pairing("cancelled", "opted-out")


@pytest.mark.unit
def test_core_echo_rejected_by_default():
    with pytest.raises(PairingError, match="restates a core TaskStatus"):
        validate_pairing("completed", "completed")


@pytest.mark.unit
def test_core_echo_allowed_when_opted_in():
    validate_pairing("completed", "completed", allow_core_echo=True)


@pytest.mark.unit
def test_core_echo_must_still_agree():
    with pytest.raises(PairingError, match="disagrees with"):
        validate_pairing("completed", "cancelled", allow_core_echo=True)


@pytest.mark.unit
def test_coding_for_shape():
    cc = coding_for("awaiting-triage")
    assert cc["coding"][0]["system"] == SYSTEM
    assert cc["coding"][0]["version"] == VERSION
    assert cc["coding"][0]["code"] == "awaiting-triage"
    assert cc["text"] == "Awaiting Triage"


@pytest.mark.unit
def test_coding_for_rejects_core_codes():
    with pytest.raises(KeyError):
        coding_for("completed")


@pytest.mark.unit
def test_local_text_only_shape():
    assert local_text_only("  Awaiting manager approval ") == {
        "text": "Awaiting manager approval"
    }


@pytest.mark.unit
def test_local_text_only_rejects_blank():
    with pytest.raises(ValueError):
        local_text_only("   ")


@pytest.mark.unit
def test_round_trip_through_a_task_resource():
    task = {
        "resourceType": "Task",
        "status": "in-progress",
        "businessStatus": coding_for("awaiting-booking"),
    }
    task = json.loads(json.dumps(task))  # survives serialisation
    status = task_status_of(task)
    bs = business_status_of(task)
    assert (status, bs) == ("in-progress", "awaiting-booking")
    validate_pairing(status, bs)


@pytest.mark.unit
def test_business_status_of_ignores_foreign_systems():
    task = {
        "status": "in-progress",
        "businessStatus": {
            "coding": [{"system": "http://example.org/local", "code": "booked"}]
        },
    }
    assert business_status_of(task) is None


@pytest.mark.unit
def test_business_status_of_ignores_text_only():
    task = {"status": "in-progress", "businessStatus": {"text": "Ping sent"}}
    assert business_status_of(task) is None


@pytest.mark.unit
def test_business_status_of_handles_missing_and_malformed():
    assert business_status_of({}) is None
    assert business_status_of({"businessStatus": "nope"}) is None
    assert business_status_of({"businessStatus": {"coding": "nope"}}) is None


@pytest.mark.unit
def test_task_status_of_handles_missing():
    assert task_status_of({}) is None
    assert task_status_of({"status": 7}) is None
