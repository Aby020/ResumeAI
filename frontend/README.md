# ResumeAI Frontend

React + TypeScript + Vite + Tailwind CSS + Motion frontend that will eventually
replace the Django-template UI. Built in Task 3 as a **foundation** — it ships
with placeholder pages, the design-token system, the API client, and auth
plumbing. The old Django frontend remains fully functional alongside it.

## Stack

| Layer     | Choice                                  |
| --------- | --------------------------------------- |
| Build     | Vite                                     |
| Language  | TypeScript (strict)                      |
| UI        | React 19                                 |
| Styling   | Tailwind CSS v4 (verified against CSS design tokens) |
| Animation | Motion (framer-motion successor), reduced-motion aware |
| Routing   | React Router v7                          |

## Getting started

```bash
cp .env.example .env        # set VITE_API_URL
npm install
npm run dev                 # http://localhost:5173
```

Start the Django API first (`python manage.py runserver` on :8000). The Vite
dev server proxies `/api` to it (see `vite.config.ts`), so development is
same-origin and needs no CORS configuration.

## Commands

```bash
npm run dev      # Vite dev server
npm run build    # tsc -b && vite build
npm run preview  # preview the production build
npm run lint     # oxlint
```

## Structure

```
src/
├── components/
│   ├── ui/        # Button, ThemeToggle, LoadingState, ErrorState, icons
│   ├── layout/    # PageShell
│   └── shared/    # Container
├── pages/
│   ├── landing/   # Landing page (placeholder)
│   ├── auth/      # Sign in / sign up
│   ├── dashboard/
│   ├── upload/
│   ├── analysis/
│   ├── history/
│   └── profile/
├── contexts/      # AuthContext, ThemeContext
├── hooks/         # useAuth, useTheme, useLocalStorage, useReducedMotion
├── lib/
│   ├── api/       # centralized API client (client, auth, resumes, dashboard)
│   └── utils/     # cn, format
├── motion/        # reusable motion variants (fade-up, stagger, page transition)
├── routes/        # route definitions + ProtectedRoute
├── types/         # strict shared types mirroring the Django API responses
├── assets/
├── App.tsx
└── main.tsx
```

## API

- Base URL is environment-aware (`src/lib/api/client.ts`):
  - **Development:** same-origin `/api`, proxied to the Django backend by the
    Vite dev server (`vite.config.ts`) — no CORS, no cross-origin requests.
  - **Production builds:** `VITE_API_URL` is **required** (baked in at build
    time, e.g. `https://api.example.com/api`). Without it the build falls back
    to same-origin `/api`, correct only when the SPA and API share an origin.
- The client handles JSON + FormData uploads, JWT `Authorization` headers,
  automatic access-token refresh on 401, and a consistent `ApiError` shape
  (status / detail / field errors). Network-level failures surface as a clear
  "Unable to reach ResumeAI" error instead of the generic fallback.
- Auth uses JWT refresh tokens from `POST /api/auth/login/` and
  `POST /api/auth/token/refresh/`; access tokens live **15 minutes**, refresh
  tokens **7 days** (configured in `settings.py`).

## Design tokens

The token system mirrors the existing "Career Signal" system in
`static/css/style.css` — warm paper neutrals + deep ink + restrained teal,
Syne for display type, Inter for body, muted motion. Tokens live in
`src/index.css` (`:root` lights, `:root[data-theme="dark"]` darks) and are
surfaced to Tailwind via `@theme inline`, so utilities like `bg-surface`,
`text-ink`, and `border-line` resolve per theme.

Theme state is stored under the same `resumeAI.theme` localStorage key as the
legacy app, so the two frontends share a theme preference.