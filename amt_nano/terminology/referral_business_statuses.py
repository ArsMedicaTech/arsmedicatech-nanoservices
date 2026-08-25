"""
Pan-Canadian eReferral/eConsult (CA:eReC) referral business status terminology.

Generated from the Canada Health Infoway terminology artifacts:

  CodeSystem https://fhir.infoway-inforoute.ca/CodeSystem/ca-referralbusinessstatus
             version 1.2.0, urn:oid:2.16.840.1.113883.6.8163, dated 2026-05-12
  ValueSet   https://fhir.infoway-inforoute.ca/ValueSet/ca-referralbusinessstatus
             version 1.2.0, urn:oid:2.16.840.1.113883.2.20.3.518

Why this module exists
----------------------
The CA:eReC Task profile binds ``Task.businessStatus`` to the ValueSet above with
strength *preferred*, and ``Task.status`` to the core FHIR ``TaskStatus`` ValueSet
with strength *required*. The CodeSystem records, for each of the 38 pan-Canadian
codes, exactly one core ``Task.status`` the code is applicable to -- but it records
that pairing as **prose inside ``concept.definition``**, not as a formal property,
extension, or invariant. No FHIR validator will enforce it. This module lifts that
prose into an enforceable map.

Two further hazards this module guards against:

1. The CodeSystem redefines all 12 core ``task-status`` codes under the Infoway
   system URI, and the ValueSet also includes them from ``http://hl7.org/fhir/task-status``.
   The same concept therefore exists under two system URIs, and a ``businessStatus``
   may legally restate ``Task.status``. The CA:eReC Business Rules direct receivers to
   reject a payload outright when redundant fields disagree, so echoing status into
   businessStatus creates a drift hazard for no benefit. ``validate_pairing`` rejects
   the core codes by default; pass ``allow_core_echo=True`` to permit them.

2. Three core statuses -- ``draft``, ``ready`` and ``accepted`` -- have no applicable
   pan-Canadian code at all. A Task in one of those states must omit
   ``businessStatus`` or fall back to ``.text``.

Scope: terminology only. No I/O, no FHIR client, no dependency beyond the stdlib.

Note on ``.text``: the binding is *preferred*, not *required*, so an uncoded
``businessStatus.text`` remains conformant. Use ``coding_for`` when you want a coded
value and ``local_text_only`` for deployment-specific states that have no
pan-Canadian equivalent.
"""

from __future__ import annotations

from typing import Dict, List, NamedTuple, Optional, Tuple

__all__ = [
    "SYSTEM",
    "VALUESET",
    "VERSION",
    "TASK_STATUS_SYSTEM",
    "BusinessStatus",
    "BUSINESS_STATUSES",
    "CORE_TASK_STATUSES",
    "STATUSES_WITHOUT_BUSINESS_STATUS",
    "PairingError",
    "applicable_status",
    "codes_for_status",
    "validate_pairing",
    "coding_for",
    "local_text_only",
    "business_status_of",
    "task_status_of",
]

SYSTEM = "https://fhir.infoway-inforoute.ca/CodeSystem/ca-referralbusinessstatus"
VALUESET = "https://fhir.infoway-inforoute.ca/ValueSet/ca-referralbusinessstatus"
VERSION = "1.2.0"
TASK_STATUS_SYSTEM = "http://hl7.org/fhir/task-status"


class BusinessStatus(NamedTuple):
    """A single pan-Canadian referral business status concept."""

    code: str
    display: str
    task_status: str
    note: Optional[str]


_C = BusinessStatus

#: The 38 pan-Canadian codes, keyed by code. Excludes the 12 core ``task-status``
#: codes that the CodeSystem also redefines (see module docstring, hazard 1).
BUSINESS_STATUSES: Dict[str, BusinessStatus] = {
    "cancelled-by-health-system": _C("cancelled-by-health-system", "Cancelled by Health System", "cancelled", "Cancellation with a systemic cause"),
    "cancelled-by-health-system-other": _C("cancelled-by-health-system-other", "Cancelled by Health System (Other)", "cancelled", None),
    "cancelled-by-patient": _C("cancelled-by-patient", "Cancelled by Patient", "cancelled", "Patient-directed cancellation"),
    "cancelled-by-patient-other": _C("cancelled-by-patient-other", "Cancelled by Patient (Other)", "cancelled", None),
    "cancelled-by-performer": _C("cancelled-by-performer", "Cancelled by Performer", "cancelled", "Performer-directed cancellation"),
    "cancelled-by-performer-other": _C("cancelled-by-performer-other", "Cancelled by Performer (Other)", "cancelled", None),
    "cancelled-by-requester": _C("cancelled-by-requester", "Cancelled by Requester", "cancelled", "Requester-directed cancellation"),
    "cancelled-by-requester-other": _C("cancelled-by-requester-other", "Cancelled by Requester (Other)", "cancelled", None),
    "cancelled-by-triage": _C("cancelled-by-triage", "Cancelled by Triage", "cancelled", None),
    "service-no-longer-available": _C("service-no-longer-available", "Service No Longer Available", "cancelled", None),
    "service-no-longer-required": _C("service-no-longer-required", "Service No Longer Required", "cancelled", None),
    "service-refused-by-patient": _C("service-refused-by-patient", "Service Refused by Patient", "cancelled", None),
    "completed-with-advice": _C("completed-with-advice", "Completed with Advice", "completed", None),
    "duplicate-request": _C("duplicate-request", "Duplicate Request", "entered-in-error", None),
    "deceased": _C("deceased", "Deceased", "failed", None),
    "no-show": _C("no-show", "No Show", "failed", "Patient did not attend a booked appointment"),
    "unable-to-contact": _C("unable-to-contact", "Unable To Contact", "failed", "Unable to contact patient"),
    "awaiting-booking": _C("awaiting-booking", "Awaiting Booking", "in-progress", "Ready for scheduling"),
    "booked": _C("booked", "Booked", "in-progress", "Appointment Booked. Encourage using the presence of the Appointment resource over this, as booked is not mutually exclusive to this status"),
    "deferred-booking": _C("deferred-booking", "Deferred Booking", "on-hold", "Not ready for scheduling"),
    "deferred-by-health-system": _C("deferred-by-health-system", "Deferred by Health System", "on-hold", None),
    "deferred-by-patient": _C("deferred-by-patient", "Deferred by Patient", "on-hold", None),
    "deferred-by-performer": _C("deferred-by-performer", "Deferred by Performer", "on-hold", None),
    "deferred-other": _C("deferred-other", "Deferred (Other)", "on-hold", None),
    "request-for-information": _C("request-for-information", "Request For Information", "on-hold", "RFI, waiting for the requester to provide more information"),
    "wait-listed": _C("wait-listed", "Wait Listed", "on-hold", "The referral is waitlist but will be moved to completed later (note: in some referral flows, \"wait listed\" is a completed status from a referral processing perspective"),
    "waiting-for-authorization": _C("waiting-for-authorization", "Waiting For Authorization", "on-hold", "e.g., for funding authorization"),
    "awaiting-triage": _C("awaiting-triage", "Awaiting Triage", "received", "Acknowledge receipt awaiting triage"),
    "incomplete-request": _C("incomplete-request", "Incomplete Request", "rejected", "The referral did not contain enough information"),
    "ineligible": _C("ineligible", "Ineligible", "rejected", "a.k.a., Criteria not met"),
    "no-capacity": _C("no-capacity", "No Capacity", "rejected", "The service is full"),
    "out-of-region": _C("out-of-region", "Out Of Region", "rejected", "Patient is out of region"),
    "redirected": _C("redirected", "Redirected", "rejected", "Rejected and redirected to more appropriate performer/service"),
    "rejected-by-central-triage": _C("rejected-by-central-triage", "Rejected by Central Triage", "rejected", "Referral will not proceed to booking because it was rejected/declined by Central Intake / CAT"),
    "rejected-by-performer": _C("rejected-by-performer", "Rejected by Performer", "rejected", "Referral will not proceed to booking after triage by a specialist/provider because it was rejected/declined"),
    "rejected-other": _C("rejected-other", "Rejected (Other)", "rejected", None),
    "invitation-expired": _C("invitation-expired", "Invitation Expired", "requested", "When an invitation is not filled before an expiry period"),
    "invited": _C("invited", "Invited", "requested", "When a referral is sent for a patient to fill out for themselves"),}

#: The 12 core FHIR TaskStatus codes. Valid for ``Task.status``; deliberately not
#: valid for ``Task.businessStatus`` under this module's default policy.
CORE_TASK_STATUSES: Tuple[str, ...] = (
    "draft",
    "requested",
    "received",
    "accepted",
    "ready",
    "in-progress",
    "on-hold",
    "rejected",
    "cancelled",
    "failed",
    "completed",
    "entered-in-error",
)

#: Core statuses with no applicable pan-Canadian business status.
STATUSES_WITHOUT_BUSINESS_STATUS: Tuple[str, ...] = tuple(
    s for s in CORE_TASK_STATUSES if not any(
        b.task_status == s for b in BUSINESS_STATUSES.values()
    )
)


class PairingError(ValueError):
    """Raised when a Task.status / Task.businessStatus pairing is not conformant."""


def applicable_status(business_status: str) -> str:
    """Return the single ``Task.status`` a business status code applies to.

    Raises ``KeyError`` if the code is not a pan-Canadian business status.
    """
    return BUSINESS_STATUSES[business_status].task_status


def codes_for_status(task_status: str) -> List[BusinessStatus]:
    """Return every business status applicable to ``task_status``, code-sorted.

    Returns an empty list for ``draft``, ``ready`` and ``accepted``, and for any
    string that is not a core task status.
    """
    return sorted(
        (b for b in BUSINESS_STATUSES.values() if b.task_status == task_status),
        key=lambda b: b.code,
    )


def validate_pairing(
    task_status: str,
    business_status: Optional[str] = None,
    allow_core_echo: bool = False,
) -> None:
    """Validate a ``Task.status`` / ``Task.businessStatus`` pairing.

    Returns ``None`` when conformant; raises ``PairingError`` otherwise. A
    ``business_status`` of ``None`` is always conformant -- the element is 0..1 and
    the binding is only *preferred*.

    Set ``allow_core_echo=True`` to permit a business status that merely restates the
    core task status. This is legal per the ValueSet but creates the redundant-data
    drift hazard described in the module docstring, so it is off by default.
    """
    if task_status not in CORE_TASK_STATUSES:
        raise PairingError(
            "%r is not a core FHIR TaskStatus code; Task.status has a required "
            "binding to %s" % (task_status, TASK_STATUS_SYSTEM)
        )

    if business_status is None:
        return

    if business_status in BUSINESS_STATUSES:
        expected = BUSINESS_STATUSES[business_status].task_status
        if expected != task_status:
            raise PairingError(
                "businessStatus %r applies to Task.status %r, not %r "
                "(CA:eReC CodeSystem %s v%s)"
                % (business_status, expected, task_status, SYSTEM, VERSION)
            )
        return

    if business_status in CORE_TASK_STATUSES:
        if not allow_core_echo:
            raise PairingError(
                "businessStatus %r restates a core TaskStatus code. This is legal per "
                "the ValueSet but duplicates Task.status; CA:eReC directs receivers to "
                "reject payloads whose redundant fields disagree. Pass "
                "allow_core_echo=True to permit it." % (business_status,)
            )
        if business_status != task_status:
            raise PairingError(
                "businessStatus %r echoes a core TaskStatus code but disagrees with "
                "Task.status %r" % (business_status, task_status)
            )
        return

    raise PairingError(
        "%r is not in CA:eReC ValueSet %s v%s. If this is a deployment-specific "
        "state, use local_text_only() to emit businessStatus.text instead."
        % (business_status, VALUESET, VERSION)
    )


def coding_for(business_status: str) -> Dict[str, object]:
    """Build a coded ``Task.businessStatus`` CodeableConcept.

    Raises ``KeyError`` for codes outside the 38 pan-Canadian concepts -- core echo
    codes included, since emitting those defeats the point of coding at all.
    """
    concept = BUSINESS_STATUSES[business_status]
    return {
        "coding": [
            {
                "system": SYSTEM,
                "version": VERSION,
                "code": concept.code,
                "display": concept.display,
            }
        ],
        "text": concept.display,
    }


def local_text_only(text: str) -> Dict[str, object]:
    """Build an uncoded ``Task.businessStatus`` for a deployment-specific state.

    Conformant because the binding is *preferred*. Use for operational states with no
    pan-Canadian equivalent rather than forcing a near-miss code -- for example, do not
    reach for ``service-refused-by-patient`` (which resolves to ``Task.status:
    cancelled``, i.e. the referral itself is cancelled) to record something narrower
    such as a patient opting out of notifications.
    """
    if not text or not text.strip():
        raise ValueError("businessStatus.text must be non-empty")
    return {"text": text.strip()}


def business_status_of(task: Dict[str, object]) -> Optional[str]:
    """Extract the pan-Canadian businessStatus code from a Task resource, if any.

    Ignores codings from other systems and never falls back to ``.text``.
    """
    bs = task.get("businessStatus")
    if not isinstance(bs, dict):
        return None
    codings = bs.get("coding")
    if not isinstance(codings, list):
        return None
    for coding in codings:
        if not isinstance(coding, dict):
            continue
        if coding.get("system") == SYSTEM:
            code = coding.get("code")
            if isinstance(code, str):
                return code
    return None


def task_status_of(task: Dict[str, object]) -> Optional[str]:
    """Extract ``Task.status`` from a Task resource, if present and a string."""
    status = task.get("status")
    return status if isinstance(status, str) else None
