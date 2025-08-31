"""
Test suite for the treatment pathways service.
"""

import asyncio

from amt_nano.services.treatment_pathways import find_recommendations, migrate

# --- Sample Clinical Data ---
# In a real scenario, this would come from an EMR/EHR system.
PATIENTS = [
    {
        "id": "patient:p001",
        "summary": "65-year-old male with a history of hypertension and type 2 diabetes, presenting with stable angina. Non-smoker. EGFR > 60. Recent stress test showed moderate ischemia in the anterior wall.",
    },
    {
        "id": "patient:p002",
        "summary": "58-year-old female, smoker, with recently diagnosed unstable angina. History of hyperlipidemia. No diabetes. Shows good left ventricular function. Allergic to aspirin.",
    },
    {
        "id": "patient:p003",
        "summary": "68-year-old male with hypertension and chronic kidney disease (EGFR 45). Presents with stable angina pectoris. Previous PCI two years ago. Good medication adherence.",
    },
    {
        "id": "patient:p004",
        "summary": "72-year-old female with type 2 diabetes, controlled hypertension, presenting with symptoms of stable angina. Shows diffuse non-obstructive coronary artery disease. Considered high-risk for surgery.",
    },
]

TREATMENTS = [
    {"id": "treatment:t01", "name": "Percutaneous Coronary Intervention (PCI)"},
    {"id": "treatment:t02", "name": "Coronary Artery Bypass Grafting (CABG)"},
    {"id": "treatment:t03", "name": "Optimal Medical Therapy (OMT)"},
]

OUTCOMES = [
    {"id": "outcome:positive", "status": "Positive"},
    {"id": "outcome:negative", "status": "Negative"},
]

# --- Relationships (Patient -> Treatment -> Outcome) ---
TREATMENT_RECORDS = [
    # Patient 1 had OMT with a positive outcome
    {
        "patient": "patient:p001",
        "treatment": "treatment:t03",
        "outcome": "outcome:positive",
    },
    # Patient 2 had PCI with a positive outcome
    {
        "patient": "patient:p002",
        "treatment": "treatment:t01",
        "outcome": "outcome:positive",
    },
    # Patient 3 had Medical Therapy, which wasn't enough (negative)
    {
        "patient": "patient:p003",
        "treatment": "treatment:t03",
        "outcome": "outcome:negative",
    },
    # Patient 3 then had PCI, which was positive
    {
        "patient": "patient:p003",
        "treatment": "treatment:t01",
        "outcome": "outcome:positive",
    },
    # Patient 4 had Medical Therapy which was positive
    {
        "patient": "patient:p004",
        "treatment": "treatment:t03",
        "outcome": "outcome:positive",
    },
]

if __name__ == "__main__":
    asyncio.run(migrate(PATIENTS, TREATMENTS, OUTCOMES, TREATMENT_RECORDS))
    asyncio.run(
        find_recommendations(
            "65-year-old male with a history of hypertension and type 2 diabetes, presenting with stable angina."
        )
    )
