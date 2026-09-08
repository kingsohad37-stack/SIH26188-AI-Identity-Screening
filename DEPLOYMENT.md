# SIH26188 deployment

## Architecture
Vercel (Next.js) -> Render (FastAPI) -> Supabase (Auth, Postgres, private Storage)

## Vercel
Set these production environment variables:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`
- `NEXT_PUBLIC_SCREENING_API_URL=https://sih26188-ai-identity-screening.onrender.com`

The publishable Supabase key is intended for browser use. Never expose a Supabase secret/service-role key to the browser.

## Render
Deploy the root Docker service from the `main` branch. The root Dockerfile builds the FastAPI backend and includes the OCR/forensics dependencies and OpenCV face models.

The backend is designed to authenticate requests with the signed-in user's Supabase JWT and perform database/storage operations under that user's RLS permissions. A Supabase service-role key is not required by the current backend architecture.

Recommended Render environment override:
- `ALLOWED_ORIGIN` = the production Vercel origin

Supabase URL and publishable key have safe project defaults in backend configuration and can also be supplied through environment variables.

## Supabase Auth
Add the Vercel production URL to the Supabase Auth Site URL / Redirect URLs before testing production login.

## Test flow
1. Sign in.
2. Create a screening.
3. Upload a synthetic test document.
4. Confirm OCR/MRZ/document-validation and forensic checks.
5. Optionally run face similarity with a separate reference image.
6. Review the risk assessment, report and audit trail.

Do not commit `.env` files, secrets, or real identity documents.
