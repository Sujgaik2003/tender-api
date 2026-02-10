# Enterprise SaaS Tender Platform - Implementation Plan

## 1. Executive Summary
This document outlines the strategic roadmap to transform the existing codebase into a **Multi-Tenant Enterprise SaaS Platform** compliant with SOC2/ISO27001. This plan is directly mapped to the "Automated Bid Submission" FRD.

## 2. Architecture & Foundation (Mandatory)
*Objective: Convert to Multi-tenant, Event-Driven, Scalable Architecture.*

### 2.1 Core Infrastructure
- **Tenancy:** Strict row-level isolation using `tenant_id` on all tables.
- **Microservices:** Modular Monolith initially, split into logical domains (Ingestion, Intelligence, Bid Engine).
- **Event Bus:** Redis/Celery for async processing (Ingestion, AI generation).
- **API:** FastAPI with versioning (`/api/v1`) and centralized Gateway features (Rate limiting).

## 3. Implementation Roadmap aligned with FRD Modules

### Phase 1: Foundation & Security (Weeks 1-2)
*Covers: Architecture, Module 9 (Multi-Tenant Config), Security.*
- **Database:** Create `tenants` table, migrate all entities to include `tenant_id`.
- **IAM:** Implement Organization/Tenant setups, RBAC (Admin, Manager, Writer).
- **Security:** Enforce RLS policies, audit logging setup (`audit_logs`).
- **Infra:** setup Redis for queuing.

### Phase 2: Discovery & Knowledge Base (Weeks 3-5)
*Covers: Module 1 (Discovery) & Module 2 (Company Profile).*
- **Module 1 (ingestion):** Support 500MB+ files, background OCR (Tesseract/Textract), Multi-source (Email/API).
- **Module 2 (Profile):** Create schemas for `certifications`, `past_performance`, `team_profiles`.
- **Search:** Implement vector search for new Knowledge Base structure.

### Phase 3: AI Bid Engine & Workflows (Weeks 6-9)
*Covers: Module 3 (AI Bid Gen) & Module 4 (Review).*
- **Module 3 (Bid Gen):** Upgrade `composer.py` for "Requirement-to-response" mapping.
- **Compliance:** Implement "Mandatory vs Optional" classification validation.
- **Module 4 (Workflow):** Build state machine for Multi-stage approvals (Draft -> Review -> Approve).

### Phase 4: Integration & Reporting (Weeks 10-12)
*Covers: Module 5 (Portals), Module 6 (Docs), Module 7 (Deadlines), Module 8 (Reporting).*
- **Module 5:** Portal Adapter framework (abstract base class for portal submission).
- **Module 6:** Document Assembly engine (pixel-perfect DOCX generation).
- **Module 7:** Deadline tracking & Notification system (Email/Slack).
- **Module 8:** Analytics dashboards (Win/Loss, Pipeline).

## 4. Immediate Next Steps (Phase 1)
We will immediately begin with **Phase 1: Foundation**.

1.  **Schema Migration:** Create `005_enterprise_foundation.sql` to introduce `tenants` and update all existing tables.
2.  **Backend Update:** Update FastAPI dependency injection to resolve `current_tenant`.
3.  **Auth Update:** Ensure user registration assigns/creates a tenant.

## 5. Definition of Done
- System builds and runs with new Multi-tenant schema.
- Existing tests pass (after refactoring for tenant_id).
- New Tenant creation flow is functional.
