# PHCEP Platform — Agent Task Log

This file tracks all tasks completed by Copilot agents, with dates, so you can follow progress.

---

## 2026-04-20 — Session: Expand ICD Scopes + SOAP Template + Multi-ICD Append Fixes

### Completed

- **Task.md created** — this file, to track agent progress across sessions.

- **Phase-1 Chinese ICD-10 2023 data** (`frontend/src/data/icd_cn_2023.ts`)  
  Added ~150 codes (Phase 1 scope: neuro/cerebrovascular/cardio/epilepsy/migraine/
  dementia/parkinson/TIA/sleep/head-injury). Each entry has `code`, `cn` (Chinese
  2023 National Standard), and `en` (English). Helper functions `icdLabel()` and
  `icdShortLabel()` exported for use in autocomplete.

- **Multi-ICD support in DailyIntakePage** (`frontend/src/pages/DailyIntakePage.tsx`)  
  - Replaced single `<Input>` ICD field with `<AutoComplete>` backed by the Phase-1
    ICD dataset (search by code prefix, Chinese name, or English keyword).  
  - Selecting a code **appends** to the tag list — previous codes are **never erased**.  
  - Multiple codes stored as comma-separated string in `icd10Code` field.  
  - Each tag can be individually removed via ×.

- **New SoapNotePage** (`frontend/src/pages/SoapNotePage.tsx`)  
  Full SOAP note editor with:
  - Science-based category selector (9 neurology/cardiology categories).
  - **Multi-ICD selector** with append mode (same as DailyIntakePage).
  - Four text sections: Subjective (S), Objective (O), Assessment (A), Plan (P).
  - Per-section **template ghost/autocomplete window** — shows ONLY templates saved
    in the **same category** as the current note (not all templates).
  - Template insert: inserts only the text **before the first ":"** in the template
    name, so `"急性腦中風: 標準處置流程"` inserts only `"急性腦中風"`.
  - Insert **appends** to existing section text (no replace/erase).
  - Template management modal: add/delete templates per category.
  - Save SOAP note via `POST /api/soap-notes`.

- **App.tsx** — added `FormOutlined`, imported `SoapNotePage`, added `/soap` route
  and "SOAP 病歷" menu item between Daily Intake and Abbreviation Glossary.

- **Backend: SoapTemplate entity** (`backend/.../model/SoapTemplate.java`)  
  JPA entity with: `id` (UUID), `name`, `category`, `content`, `createdAt`.

- **Backend: SoapTemplateRepository** (`backend/.../repository/SoapTemplateRepository.java`)  
  JPA repository with `findByCategoryOrderByCreatedAtAsc` and `findAllByOrderByCreatedAtAsc`.

- **Backend: SoapTemplateService** (`backend/.../service/SoapTemplateService.java`)  
  CRUD service with listAll, listByCategory, create, update, delete.

- **Backend: SoapTemplateController** (`backend/.../controller/SoapTemplateController.java`)  
  REST controller:
  - `GET /api/soap-templates` (optional `?category=` filter)
  - `POST /api/soap-templates`
  - `PUT /api/soap-templates/{id}`
  - `DELETE /api/soap-templates/{id}` (HCP/Admin only)

- **DB migration** (`004-soap-templates.xml`) — creates `soap_template` table with
  `category` index.

- **db.changelog-master.xml** — includes `004-soap-templates.xml`.

---

## ICD Code Expansion Roadmap

Codes added gradually to limit computation per session.

| Phase | ICD Chapter(s) | Status |
|-------|----------------|--------|
| 1 (current) | I60–I69 腦血管, I10–I13 高血壓, I20–I25 冠心病, I48 心房顫動, G40–G41 癲癇, G43–G44 頭痛, G20–G26 帕金森, F00–F03+G30 失智, G35–G37 脫髓鞘, G45–G46 TIA, G47 睡眠, G50–G62 週邊神經, S06 頭傷 | ✅ Done |
| 2 | I (循環系統, 完整章節), J (呼吸系統) | ⏳ Pending |
| 3 | M (肌肉骨骼), N (泌尿生殖), K (消化系統) | ⏳ Pending |
| 4 | C (腫瘤), E (內分泌/代謝), F (完整精神疾患) | ⏳ Pending |
| 5 | A–B (感染), D (血液), H (眼/耳), L (皮膚), O (妊娠), P (周産), Q (先天), R (症狀), S–T (外傷其餘), V–Z (外因) | ⏳ Pending |

---

## Previous Sessions

*(No prior agent sessions before 2026-04-20.)*
