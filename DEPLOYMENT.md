# SIH26188 deployment

## Architecture
Vercel (Next.js) -> Render (FastAPI) -> Supabase (Auth, Postgres, private Storage)

## Vercel
Set:
- NEXT_PUBLIC_SUPABASE_URL
- NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
- NEXT_PUBLIC_SCREENING_API_URL (Render API URL)

## Render
Deploy `backend/` as a Docker web service. Set:
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- ALLOWED_ORIGIN (Vercel URL)

The service-role key is backend-only and must never be exposed to the browser.

## Supabase Auth
Add the Vercel production URL to the Auth redirect/site URL configuration before testing production login.

## Test flow
1. Sign in.
2. Create a screening.
3. Upload a synthetic test document.
4. Confirm OCR/MRZ/forensic checks.
5. Optionally run face similarity with a separate reference image.
6. Review the report and audit trail.

Do not commit `.env` files, secrets, or real identity documents.
