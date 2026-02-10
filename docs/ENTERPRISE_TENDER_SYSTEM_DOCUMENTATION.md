# Enterprise Tender Management System
## Complete End-to-End Documentation

**Document Version:** 1.0  
**Last Updated:** February 6, 2026  
**Classification:** Internal Technical Documentation

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Database Schema](#4-database-schema)
5. [Frontend Application](#5-frontend-application)
6. [Backend Services](#6-backend-services)
7. [AI/ML Pipeline](#7-aiml-pipeline)
8. [Tender Discovery Module](#8-tender-discovery-module)
9. [Knowledge Base System](#9-knowledge-base-system)
10. [Enterprise Matrix (Company Profile)](#10-enterprise-matrix-company-profile)
11. [Role-Based Access Control (RBAC)](#11-role-based-access-control-rbac)
12. [Workflow & Approval System](#12-workflow--approval-system)
13. [Document Export](#13-document-export)
14. [API Reference](#14-api-reference)
15. [Deployment Guide](#15-deployment-guide)
16. [Recent Enhancements](#16-recent-enhancements)

---

## 1. Executive Summary

The **Enterprise Tender Management System** is a comprehensive, AI-powered platform designed to automate and streamline the entire tender response lifecycle. From discovering new opportunities on government portals to generating professional bid documents, the system provides end-to-end automation while maintaining human oversight and approval workflows.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Tender Discovery** | Autonomous scraping of government portals (GeM) with AI-based relevance scoring |
| **Document Analysis** | OCR-enabled PDF/DOCX parsing with intelligent requirement extraction |
| **Knowledge Matching** | FAISS vector search for semantic matching against company data |
| **Response Generation** | RAG-based AI composition with <30% AI content enforcement |
| **Multi-Tenant SaaS** | Complete tenant isolation with row-level security |
| **Enterprise RBAC** | Four-tier role system (Admin, Manager, Bid Writer, Auditor) |
| **Professional Export** | Big-4 style DOCX generation with branding |

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│                         Next.js 14 + TailwindCSS                            │
│                            (Vercel Hosted)                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY                                     │
│                        FastAPI (Python 3.11+)                               │
│                           (Railway Hosted)                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Documents│  │ Responses│  │ Discovery│  │ Company  │  │Knowledge │      │
│  │   API    │  │   API    │  │   API    │  │   API    │  │Base API  │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│      SUPABASE        │  │    CELERY WORKER     │  │    MISTRAL LLM       │
│  ┌──────────────┐    │  │  ┌──────────────┐    │  │  ┌──────────────┐    │
│  │ PostgreSQL   │    │  │  │ Document     │    │  │  │ Chat         │    │
│  │ + pgvector   │    │  │  │ Processing   │    │  │  │ Completions  │    │
│  ├──────────────┤    │  │  ├──────────────┤    │  │  ├──────────────┤    │
│  │ Auth (JWT)   │    │  │  │ Discovery    │    │  │  │ Response     │    │
│  ├──────────────┤    │  │  │ Scanning     │    │  │  │ Generation   │    │
│  │ Storage      │    │  │  ├──────────────┤    │  │  ├──────────────┤    │
│  │ (Documents)  │    │  │  │ AI Matching  │    │  │  │ Refinement   │    │
│  └──────────────┘    │  │  └──────────────┘    │  │  └──────────────┘    │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
                                      │
                                      ▼
                    ┌──────────────────────────────────┐
                    │         FAISS VECTOR STORE       │
                    │   sentence-transformers embeddings│
                    │   Semantic Knowledge Retrieval    │
                    └──────────────────────────────────┘
```

### Data Flow

1. **Upload**: User uploads tender document → Stored in Supabase Storage
2. **Parse**: Celery worker extracts text (OCR if scanned)
3. **Extract**: NLP engine identifies requirements by category
4. **Match**: FAISS finds relevant company knowledge
5. **Compose**: Mistral LLM generates responses (<30% AI)
6. **Review**: Human approval workflow (Draft → Review → Approved)
7. **Export**: Professional DOCX with company branding

---

## 3. Technology Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| Next.js 14 | React framework with App Router |
| TypeScript | Type-safe development |
| TailwindCSS | Utility-first CSS |
| Lucide React | Icon library |
| React Hook Form | Form management |
| Zustand | State management |
| React Hot Toast | Notifications |

### Backend
| Technology | Purpose |
|------------|---------|
| FastAPI | High-performance Python API |
| Uvicorn | ASGI server |
| Celery | Distributed task queue |
| Redis | Message broker & cache |
| Pydantic | Data validation |
| Python-Jose | JWT authentication |

### AI/ML
| Technology | Purpose |
|------------|---------|
| Mistral 7B | LLM for response generation |
| FAISS | Vector similarity search |
| Sentence-Transformers | Text embeddings |
| LangDetect | Language detection |
| NLTK | NLP utilities |

### Document Processing
| Technology | Purpose |
|------------|---------|
| PDFPlumber | PDF text extraction |
| PyMuPDF (fitz) | PDF rendering |
| python-docx | DOCX generation |
| Pytesseract | OCR for scanned docs |
| OpenCV | Image preprocessing |
| Pillow | Image manipulation |

### Scraping
| Technology | Purpose |
|------------|---------|
| Playwright | Browser automation |
| BeautifulSoup | HTML parsing |
| HTTPX | Async HTTP client |

### Database
| Technology | Purpose |
|------------|---------|
| PostgreSQL | Relational database |
| Supabase | BaaS (Auth, Storage, RLS) |
| pgvector | Vector embeddings (future) |

---

## 4. Database Schema

### Core Tables

#### `tenants`
Multi-tenant foundation table.
```sql
id UUID PRIMARY KEY
name VARCHAR(255)
subscription_tier VARCHAR(50) DEFAULT 'trial'
settings JSONB DEFAULT '{}'
created_at TIMESTAMPTZ
```

#### `user_profiles`
Extended user information with RBAC.
```sql
id UUID PRIMARY KEY REFERENCES auth.users(id)
tenant_id UUID REFERENCES tenants(id)
full_name VARCHAR(255)
role VARCHAR(50) DEFAULT 'BID_WRITER'
-- Roles: ADMIN, MANAGER, BID_WRITER, AUDITOR
```

#### `documents`
Uploaded tender documents.
```sql
id UUID PRIMARY KEY
tenant_id UUID REFERENCES tenants(id)
user_id UUID REFERENCES auth.users(id)
tender_name VARCHAR(255)
file_name VARCHAR(255)
file_path TEXT
file_type VARCHAR(50)
status VARCHAR(50) -- UPLOADED, PARSING, EXTRACTING, MATCHING, READY, ERROR
processing_progress INTEGER
```

#### `requirements`
Extracted requirements from documents.
```sql
id UUID PRIMARY KEY
document_id UUID REFERENCES documents(id)
text TEXT
category VARCHAR(50) -- ELIGIBILITY, TECHNICAL, COMPLIANCE
subcategory VARCHAR(255)
priority VARCHAR(50) -- Mandatory, Optional
confidence DECIMAL
extraction_order INTEGER
```

#### `responses`
AI-generated responses with approval workflow.
```sql
id UUID PRIMARY KEY
requirement_id UUID REFERENCES requirements(id)
document_id UUID REFERENCES documents(id)
content TEXT
status VARCHAR(50) -- DRAFT, PENDING_REVIEW, APPROVED
ai_percentage DECIMAL
approved_by UUID
approved_at TIMESTAMPTZ
```

#### `knowledge_base`
Company knowledge for RAG.
```sql
id UUID PRIMARY KEY
tenant_id UUID REFERENCES tenants(id)
title VARCHAR(255)
content TEXT
category VARCHAR(255) -- Company Profile System, Certifications, etc.
is_active BOOLEAN
```

#### `company_profiles`
Enterprise company information.
```sql
id UUID PRIMARY KEY
tenant_id UUID REFERENCES tenants(id) UNIQUE
legal_name VARCHAR(255)
tax_id VARCHAR(100)
registration_number VARCHAR(100)
company_address TEXT
website VARCHAR(255)
contact_email VARCHAR(255)
contact_phone VARCHAR(100)
capabilities TEXT[] -- Array of capability strings
certifications JSONB -- [{name, issuer, expiry}]
insurance JSONB
```

#### `discovered_tenders`
Scraped tender opportunities.
```sql
id UUID PRIMARY KEY
tenant_id UUID REFERENCES tenants(id)
external_ref_id VARCHAR(255)
title TEXT
authority VARCHAR(255)
publish_date TIMESTAMPTZ
submission_deadline TIMESTAMPTZ
source_portal VARCHAR(255)
status VARCHAR(50) -- PENDING, APPROVED, REJECTED
match_score DECIMAL
match_explanation TEXT
domain_tags TEXT[]
```

### Row-Level Security (RLS)

All tables enforce tenant isolation:
```sql
CREATE POLICY "Tenant isolation" ON [table]
    FOR ALL USING (tenant_id = get_current_tenant_id());
```

---

## 5. Frontend Application

### Directory Structure
```
frontend/src/
├── app/
│   ├── dashboard/
│   │   ├── page.tsx              # Main dashboard
│   │   ├── discovery/            # Tender discovery
│   │   ├── documents/            # Document management
│   │   │   └── [id]/             # Document analysis view
│   │   ├── knowledge-base/       # KB management
│   │   ├── settings/
│   │   │   └── company/          # Enterprise Matrix
│   │   ├── upload/               # Document upload
│   │   └── analytics/            # Reporting
│   ├── login/                    # Authentication
│   └── layout.tsx                # Root layout
├── components/
│   ├── ui/                       # Base components (Card, Button, Modal)
│   ├── layout/                   # Navigation, Sidebar
│   ├── documents/                # Document-specific components
│   ├── analysis/                 # Analysis views
│   └── responses/                # Response editor
├── lib/
│   ├── api-client.ts             # Backend API wrapper
│   ├── supabase/                 # Supabase client
│   ├── i18n.ts                   # Internationalization
│   └── utils.ts                  # Utility functions
└── types/
    └── index.ts                  # TypeScript definitions
```

### Key Pages

#### Dashboard (`/dashboard`)
- Active tenders overview
- Match score visualization
- Quick actions (Upload, Discover)
- Recent activity feed

#### Tender Discovery (`/dashboard/discovery`)
- Scraped tender cards with AI match scores
- Filter by status (Pending, Approved, Rejected)
- One-click approval to bid workflow
- Domain tag visualization

#### Document Analysis (`/dashboard/documents/[id]`)
- Requirement list with category badges
- Match percentage per requirement
- Response editor with regeneration
- Approval workflow controls

#### Enterprise Matrix (`/dashboard/settings/company`)
- **Profile Tab**: Legal company information
- **Past Performance Tab**: Historical project data
- **Team Tab**: Key personnel profiles
- **Certifications Tab**: ISO, SOC2, etc.
- **Governance Tab**: Compliance policies

#### Knowledge Base (`/dashboard/knowledge-base`)
- Content cards with categories
- Add/Edit/Delete functionality
- Category filtering pills
- RBAC-protected (Admin/Manager only)

---

## 6. Backend Services

### Service Layer Architecture

```
backend/app/services/
├── parser.py        # Document text extraction
├── extractor.py     # Requirement identification
├── matcher.py       # FAISS vector matching
├── composer.py      # Response generation
├── ai_detector.py   # AI content analysis
├── exporter.py      # DOCX generation
├── pipeline.py      # Orchestration
└── discovery/
    ├── base.py      # Abstract scraper
    ├── scanner.py   # Discovery orchestration
    ├── matcher.py   # Tender-company matching
    └── scrapers/
        ├── gem_scraper.py   # GeM portal
        └── mock_scraper.py  # Testing
```

### Key Services

#### Parser (`parser.py`)
Extracts text from PDF/DOCX documents.
- **PDF**: Uses `pdfplumber` for native text, `pytesseract` for scanned pages
- **DOCX**: Uses `python-docx` for text extraction
- **OCR Pipeline**: Grayscale → Threshold → Denoise → Tesseract

#### Extractor (`extractor.py`)
Identifies requirements from raw text.
- **Pattern Matching**: Regex for eligibility, technical, compliance keywords
- **LLM Extraction**: Falls back to Mistral for non-English or complex docs
- **Categorization**: Assigns category, subcategory, and priority (Mandatory/Optional)

#### Matcher (`matcher.py`)
Vector similarity search against Knowledge Base.
- **Embeddings**: `paraphrase-multilingual-MiniLM-L12-v2`
- **Index**: FAISS `IndexFlatIP` (Inner Product)
- **Output**: Top-K matches with similarity scores

#### Composer (`composer.py`)
Generates human-like responses using RAG.
- **Context Injection**: Includes KB matches in prompt
- **AI Limit**: Enforces <30% AI-generated content
- **Refinement Loop**: Up to 10 iterations to reduce AI percentage

#### AI Detector (`ai_detector.py`)
Analyzes content for AI-generated text.
- **Perplexity Analysis**: Statistical language patterns
- **Burstiness Check**: Sentence variation analysis
- **Similarity Scoring**: Comparison with source KB

#### Exporter (`exporter.py`)
Generates professional DOCX documents.
- **Cover Page**: Company logo, tender title, date
- **Table of Contents**: Auto-generated
- **Compliance Matrix**: Requirement-response table
- **Branding**: Custom colors, fonts

---

## 7. AI/ML Pipeline

### RAG (Retrieval-Augmented Generation) Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Requirement │────▶│  Embedding  │────▶│   FAISS     │
│   Text      │     │   Model     │     │   Search    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
                    ┌──────────────────────────────────┐
                    │        TOP-3 KB MATCHES          │
                    └──────────────────┬───────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      MISTRAL LLM                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ System: You are a professional bid writer.          │    │
│  │ Use ONLY the provided company knowledge.            │    │
│  │ Do NOT add external information.                    │    │
│  │ Maintain professional, confident tone.              │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ User: Generate response for: {requirement}          │    │
│  │ Context: {kb_match_1}, {kb_match_2}, {kb_match_3}   │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   QUALITY GATE       │
                    │   AI % < 30%?        │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │ YES                             │ NO
              ▼                                 ▼
    ┌──────────────────┐            ┌──────────────────┐
    │  APPROVED DRAFT  │            │  RETRY (max 10)  │
    └──────────────────┘            └──────────────────┘
```

### Embedding Model
- **Model**: `paraphrase-multilingual-MiniLM-L12-v2`
- **Dimensions**: 384
- **Normalization**: L2 normalized for cosine similarity

### LLM Configuration
- **Provider**: Mistral AI (self-hosted or API)
- **Model**: Mistral 7B Instruct
- **Temperature**: 0.3 (for consistency)
- **Max Tokens**: 1024

---

## 8. Tender Discovery Module

### Architecture

The Discovery Module autonomously scans government tender portals and evaluates opportunities.

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   SCHEDULER      │────▶│     SCRAPERS     │────▶│    MATCHER       │
│   (Celery Beat)  │     │   (Playwright)   │     │   (LLM + KB)     │
└──────────────────┘     └──────────────────┘     └────────┬─────────┘
                                                           │
                                                           ▼
                                               ┌──────────────────────┐
                                               │  discovered_tenders  │
                                               │        TABLE         │
                                               └──────────────────────┘
```

### Supported Portals

| Portal | URL | Status |
|--------|-----|--------|
| GeM (Government e-Marketplace) | bidplus.gem.gov.in | ✅ Active |
| CPPP | eprocure.gov.in | 🔜 Planned |
| TenderTiger | tendertiger.com | 🔜 Planned |

### GeM Scraper (`gem_scraper.py`)

#### Capabilities
- Headless browser automation (Playwright Chromium)
- Bot detection bypass (realistic user-agent, headers)
- Dual structure support (old `border-bid` + new `card`)
- Robust date parsing (5 format variations)

#### Extracted Fields
| Field | Source |
|-------|--------|
| `external_ref_id` | Bid number element |
| `title` | Item name / popover content |
| `authority` | Department container |
| `publish_date` | Start date span |
| `submission_deadline` | End date span |
| `doc_url` | Bid document link |

### AI Matching (`discovery/matcher.py`)

For each discovered tender:
1. **Vector Search**: Matches tender description against KB
2. **LLM Analysis**: Mistral evaluates relevance based on:
   - Preferred domains (from `discovery_config`)
   - Keywords of interest
   - Historical project alignment
3. **Scoring**: 0-100 match score with explanation
4. **Tagging**: Extracts 3-5 domain tags

---

## 9. Knowledge Base System

### Purpose
The Knowledge Base (KB) is the "corporate memory" that powers RAG. It contains verified company information that the AI uses to generate responses.

### Categories
| Category | Content Type |
|----------|--------------|
| Company Profile System | Legal info, contacts, capabilities |
| Certifications | ISO, SOC2, compliance credentials |
| Past Performance | Historical project descriptions |
| Technical Capabilities | Service offerings, technology stack |
| Team Profiles | Key personnel bios |

### Sync Mechanism

When company profile is updated:
```python
# From company/routes.py
kb_content = f"""
Company Legal Profile:
- Name: {profile_data.get('legal_name')}
- Capabilities: {', '.join(capabilities)}
...
"""
supabase.table('knowledge_base').upsert(kb_item_data)
matcher.add_item(kb_id, kb_content, metadata)
```

### Certifications Sync (New Feature)
Certifications now have their own dedicated KB category:
```python
cert_content = "Company Certifications & Compliance:\n" + 
    "\n".join([f"- {c.get('name')} (Issuer: {c.get('issuer')})" for c in certs])

# Creates separate KB entry with category='Certifications'
```

---

## 10. Enterprise Matrix (Company Profile)

### Tabs

#### Profile
Core company information synced to KB.
| Field | KB Sync |
|-------|---------|
| Legal Name | ✅ |
| Tax ID | ✅ |
| Registration Number | ✅ |
| Address | ✅ |
| Website | ✅ |
| Contact Email/Phone | ✅ |

#### Capabilities
List of service offerings (string array).
- Synced to KB as comma-separated list
- Used for tender matching

#### Certifications (New)
Structured certification records.
| Field | Type |
|-------|------|
| Name | Text (e.g., "ISO 27001") |
| Issuing Authority | Text (e.g., "BSI Group") |
| Expiry Date | Date (optional) |

- **Dedicated KB Category**: Creates separate "Certifications" item
- **RBAC**: Only Admin/Manager can modify

#### Past Performance
Historical project records.
| Field | Type |
|-------|------|
| Project Name | Text |
| Client | Text |
| Value | Currency |
| Duration | Text |
| Description | Textarea |

#### Team Profiles
Key personnel for proposals.
| Field | Type |
|-------|------|
| Name | Text |
| Title | Text |
| Qualifications | Text |
| Experience | Number (years) |

---

## 11. Role-Based Access Control (RBAC)

### Role Hierarchy

| Role | Level | Permissions |
|------|-------|-------------|
| **ADMIN** | 4 | Full system access, user management |
| **MANAGER** | 3 | Approve bids, manage KB, view analytics |
| **BID_WRITER** | 2 | Create/edit responses, upload documents |
| **AUDITOR** | 1 | Read-only access to all data |

### Page Access Matrix

| Page | ADMIN | MANAGER | BID_WRITER | AUDITOR |
|------|-------|---------|------------|---------|
| Dashboard | ✅ | ✅ | ✅ | ✅ (readonly) |
| Discovery | ✅ | ✅ | ❌ | ✅ (readonly) |
| Upload | ✅ | ✅ | ✅ | ❌ |
| Documents | ✅ | ✅ | ✅ | ✅ (readonly) |
| Knowledge Base | ✅ | ✅ | ❌ | ❌ |
| Enterprise Matrix | ✅ | ✅ | ❌ | ❌ |
| Analytics | ✅ | ✅ | ❌ | ✅ (readonly) |
| Settings | ✅ | ✅ | ❌ | ❌ |

### Implementation

```typescript
// Frontend: Role check
const isAuthorized = ['ADMIN', 'MANAGER'].includes(currentUserRole);

// Backend: JWT validation
@router.post("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    if user['role'] not in ['ADMIN', 'MANAGER']:
        raise HTTPException(403, "Insufficient permissions")
```

---

## 12. Workflow & Approval System

### Response Lifecycle

```
┌──────────┐     ┌──────────────┐     ┌──────────┐     ┌──────────┐
│  DRAFT   │────▶│ PENDING_REVIEW│────▶│ APPROVED │────▶│ EXPORTED │
└──────────┘     └──────────────┘     └──────────┘     └──────────┘
     │                  │                   │
     │                  │                   │
     ▼                  ▼                   ▼
  Auto-created     Reviewer action     Final state
  by AI/Manual     required            Ready for DOCX
```

### Actions by Role

| Action | Who Can Perform |
|--------|-----------------|
| Generate Response | BID_WRITER, MANAGER, ADMIN |
| Edit Draft | BID_WRITER, MANAGER, ADMIN |
| Submit for Review | BID_WRITER, MANAGER, ADMIN |
| Approve | MANAGER, ADMIN |
| Regenerate | BID_WRITER, MANAGER, ADMIN |
| Export DOCX | All (after approval) |

---

## 13. Document Export

### DOCX Generation (`exporter.py`)

#### Template Structure
1. **Cover Page**
   - Company logo (if provided)
   - Tender title
   - Submission date
   - Company name & tagline

2. **Table of Contents**
   - Auto-generated from headings

3. **Executive Summary**
   - Company introduction
   - Proposal overview

4. **Technical Response**
   - Requirement-by-requirement answers
   - Category grouping

5. **Compliance Matrix**
   - Table format: Requirement | Response | Status

6. **Appendices**
   - Certifications list
   - Team profiles

#### Styling
- **Primary Color**: Configurable (default: `#0ea5e9`)
- **Fonts**: Professional serif for headings
- **Tables**: Alternating row colors

---

## 14. API Reference

### Authentication
All endpoints require JWT Bearer token.
```
Authorization: Bearer <access_token>
```

### Endpoints

#### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents` | List all documents |
| GET | `/api/documents/{id}` | Get document details |
| POST | `/api/documents/{id}/process` | Trigger processing |
| DELETE | `/api/documents/{id}` | Delete document |
| GET | `/api/documents/{id}/requirements` | Get extracted requirements |
| POST | `/api/documents/{id}/export` | Generate DOCX |

#### Responses
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/responses/{doc_id}/requirement/{req_id}` | Get response |
| POST | `/api/responses/generate` | Generate AI response |
| PUT | `/api/responses/{id}` | Update response |
| POST | `/api/responses/{id}/submit` | Submit for review |
| POST | `/api/responses/{id}/approve` | Approve response |

#### Discovery
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/discovery/scan` | Trigger portal scan |
| GET | `/discovery/tenders` | List discovered tenders |
| POST | `/discovery/tenders/{id}/approve` | Approve for bidding |
| POST | `/discovery/tenders/{id}/reject` | Reject tender |
| DELETE | `/discovery/tenders/{id}` | Delete tender |

#### Company
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/company/profile` | Get company profile |
| POST | `/api/company/profile` | Update company profile |
| GET | `/api/company/past-performance` | Get past projects |
| POST | `/api/company/past-performance` | Add past project |

#### Knowledge Base
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/knowledge-base` | List KB items |
| POST | `/api/knowledge-base` | Add KB item |
| PUT | `/api/knowledge-base/{id}` | Update KB item |
| DELETE | `/api/knowledge-base/{id}` | Delete KB item |

---

## 15. Deployment Guide

### Prerequisites
- Node.js 18+
- Python 3.11+
- Redis server
- Supabase account
- Mistral API key (or self-hosted)

### Frontend (Vercel)
```bash
cd frontend
npm install
npm run build
vercel --prod
```

Environment variables:
```
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Backend (Railway/Docker)
```bash
cd backend
pip install -r requirements.txt

# Start API
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start Worker (separate process)
celery -A app.core.celery_app worker --pool=solo --loglevel=info
```

Environment variables:
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
LLM_API_URL=https://api.mistral.ai/v1
LLM_API_KEY=xxx
LLM_MODEL=mistral-small-latest
REDIS_URL=redis://localhost:6379
```

### Database
Run migrations in order:
```bash
psql -f supabase/migrations/001_initial_schema.sql
psql -f supabase/migrations/005_enterprise_foundation.sql
# ... etc
```

---

## 16. Recent Enhancements

### February 2026

#### Certifications Module
- **Feature**: New "Certifications" tab in Enterprise Matrix
- **Files Modified**: 
  - `frontend/src/app/dashboard/settings/company/page.tsx`
  - `backend/app/api/company/routes.py`
- **What it does**:
  - Add, view, delete company certifications (ISO, SOC2, etc.)
  - RBAC: Only Admin/Manager can modify
  - Automatic sync to Knowledge Base under dedicated "Certifications" category
  - AI can now reference certifications in bid responses

#### GeM Scraper Date Fix
- **Issue**: Submission deadlines were incorrectly parsed
- **Files Modified**: 
  - `backend/app/services/discovery/scrapers/gem_scraper.py`
- **Solution**:
  - Robust `_parse_gem_date()` method with 5 format variations
  - Regex-based label stripping ("Bid End Date:" → date only)
  - Fallback text search for date elements

#### Knowledge Base Sync Enhancement
- **Before**: Certifications were only listed in main profile
- **After**: Dedicated KB entry with `category='Certifications'`
- **Benefit**: Better visibility in KB UI and cleaner vector search

---

## Appendix A: File Inventory

### Backend (`backend/app/`)
| File | Lines | Purpose |
|------|-------|---------|
| `api/documents.py` | 400 | Document CRUD & export |
| `api/responses.py` | ~500 | Response generation & workflow |
| `api/discovery.py` | 104 | Tender discovery endpoints |
| `api/company/routes.py` | ~300 | Company profile management |
| `services/parser.py` | ~300 | PDF/DOCX text extraction |
| `services/extractor.py` | 346 | Requirement identification |
| `services/matcher.py` | 271 | FAISS vector search |
| `services/composer.py` | ~600 | Response generation |
| `services/exporter.py` | ~600 | DOCX generation |
| `services/discovery/gem_scraper.py` | 215 | GeM portal scraper |

### Frontend (`frontend/src/`)
| File | Lines | Purpose |
|------|-------|---------|
| `app/dashboard/page.tsx` | ~800 | Main dashboard |
| `app/dashboard/discovery/page.tsx` | 331 | Tender discovery |
| `app/dashboard/documents/[id]/page.tsx` | ~600 | Document analysis |
| `app/dashboard/settings/company/page.tsx` | ~600 | Enterprise Matrix |
| `app/dashboard/knowledge-base/page.tsx` | 362 | KB management |
| `lib/api-client.ts` | ~260 | Backend API wrapper |

---

## Appendix B: Database Migrations

| Migration | Purpose |
|-----------|---------|
| 001_initial_schema.sql | Core tables (documents, requirements, responses) |
| 002_storage_setup.sql | Supabase storage buckets |
| 003_complete_rls_policies.sql | Row-level security |
| 005_enterprise_foundation.sql | Multi-tenant (tenants table) |
| 007_company_profile_kb.sql | Company profiles & KB |
| 008_workflow_approval.sql | Approval workflow fields |
| 011_smart_role_assignment.sql | RBAC triggers |
| 012_tender_discovery.sql | Discovery module tables |

---

*Document generated by Enterprise Tender System v1.0*
