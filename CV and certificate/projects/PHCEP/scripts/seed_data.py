#!/usr/bin/env python3
"""
PHCEP Seed Data Script
Populates the database with sample EBM entries and a demo patient observation
for development and testing purposes.

Run after the backend is started:
  python scripts/seed_data.py
"""

import requests
import sys
import json

BASE_URL = "http://localhost:8080"
HEADERS = {}  # Populated after login


def login(username: str, password: str) -> str:
    resp = requests.post(f"{BASE_URL}/api/auth/login",
                         json={"username": username, "password": password})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        sys.exit(1)
    token = resp.json()["token"]
    print(f"✓ Logged in as {username}")
    return token


def seed_ebm_entries(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    entries = [
        {
            "statement": "Metformin is recommended as first-line pharmacotherapy for type 2 diabetes mellitus in the absence of contraindications.",
            "pmid": "28214667",
            "articleUrl": "https://pubmed.ncbi.nlm.nih.gov/28214667/",
            "icd10Codes": "E11",
            "specialty": "Endocrinology",
        },
        {
            "statement": "HbA1c < 7% is the target glycaemic control for most non-pregnant adults with type 2 diabetes.",
            "pmid": "34270136",
            "articleUrl": "https://pubmed.ncbi.nlm.nih.gov/34270136/",
            "icd10Codes": "E11",
            "specialty": "Endocrinology",
        },
        {
            "statement": "Aspirin 100 mg daily is indicated for secondary prevention of cardiovascular events in patients with established atherosclerotic cardiovascular disease.",
            "pmid": "30145972",
            "articleUrl": "https://pubmed.ncbi.nlm.nih.gov/30145972/",
            "icd10Codes": "I25",
            "specialty": "Cardiology",
        },
        {
            "statement": "tPA (alteplase) should be given within 4.5 hours of ischaemic stroke onset in eligible patients.",
            "pmid": "18815396",
            "articleUrl": "https://pubmed.ncbi.nlm.nih.gov/18815396/",
            "icd10Codes": "I63",
            "specialty": "Neurology",
        },
        {
            "statement": "Low-dose CT screening for lung cancer is recommended annually for high-risk adults aged 50–80 with ≥20 pack-year smoking history.",
            "pmid": "34590683",
            "articleUrl": "https://pubmed.ncbi.nlm.nih.gov/34590683/",
            "icd10Codes": "C34",
            "specialty": "Pulmonology",
        },
    ]
    for entry in entries:
        resp = requests.post(f"{BASE_URL}/api/ebm", json=entry, headers=headers)
        if resp.status_code in (200, 201):
            print(f"  ✓ EBM entry: {entry['statement'][:60]}...")
        else:
            print(f"  ✗ Failed ({resp.status_code}): {resp.text[:80]}")


def seed_observations(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    observations = [
        {
            "observationType": "LAB",
            "loincCode": "4548-4",
            "observationText": "Glycated haemoglobin (HbA1c) measurement",
            "numericValue": 7.2,
            "unit": "%",
            "referenceRangeLow": 4.0,
            "referenceRangeHigh": 5.6,
            "effectiveDateTime": "2024-01-15T08:30:00",
        },
        {
            "observationType": "LAB",
            "loincCode": "4548-4",
            "observationText": "Glycated haemoglobin (HbA1c) measurement",
            "numericValue": 6.9,
            "unit": "%",
            "referenceRangeLow": 4.0,
            "referenceRangeHigh": 5.6,
            "effectiveDateTime": "2024-04-10T09:00:00",
        },
        {
            "observationType": "VITAL_SIGN",
            "loincCode": "55284-4",
            "observationText": "Blood pressure measurement",
            "numericValue": 128.0,
            "unit": "mmHg",
            "referenceRangeLow": 90.0,
            "referenceRangeHigh": 140.0,
            "effectiveDateTime": "2024-04-10T09:05:00",
        },
    ]
    for obs in observations:
        resp = requests.post(f"{BASE_URL}/api/patient/observations", json=obs, headers=headers)
        if resp.status_code in (200, 202):
            print(f"  ✓ Observation: {obs['observationText']}")
        else:
            print(f"  ✗ Failed ({resp.status_code}): {resp.text[:80]}")


if __name__ == "__main__":
    print("PHCEP Seed Data")
    print("───────────────")
    # Default demo credentials — change in production
    admin_token = login("admin", "phcep-admin-password")

    print("\nSeeding EBM entries...")
    seed_ebm_entries(admin_token)

    print("\nSeeding demo observations (as admin/patient)...")
    seed_observations(admin_token)

    print("\n✓ Seed complete.")
