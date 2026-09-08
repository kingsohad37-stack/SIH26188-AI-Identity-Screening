# SIH26188 — AI-Based Fake Identity & Document Screening System

A production-oriented Smart India Hackathon system for identity-document screening.

## Current capabilities
- Supabase-authenticated screening workspace
- Private document upload to Supabase Storage
- OCR extraction for uploaded images/PDF pages
- Passport TD3 MRZ parsing and check-digit/date validation
- Conservative image-forensics signals including ELA-style recompression analysis
- OpenCV YuNet + SFace face-similarity screening
- Deterministic risk scoring from recorded checks
- Screening findings, report view, and audit trail
- Apple-inspired translucent frontend with reduced-motion/transparency handling
- Vercel + Render deployment configuration and GitHub CI/security workflows

## Architecture
Next.js / React -> FastAPI -> Supabase Auth + Postgres + private Storage

## Important limitation
The current tampering component is a forensic signal layer, not a validated forgery classifier. A suspicious signal is a reason for review, not proof that a document is fake. Face similarity is also a screening signal, not a legal identity determination.

## Deployment
See `DEPLOYMENT.md`. Never commit `.env` files, service-role keys, or real identity documents.
