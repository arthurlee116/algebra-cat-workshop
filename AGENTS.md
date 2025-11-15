# Repository Guidelines

## Project Structure & Module Organization
The backend (`backend/`) is a FastAPI + SQLAlchemy service: `main.py` wires routes, `question_generator.py` builds algebra prompts, `services.py` holds scoring utilities, and `database.py` bootstraps SQLite (`data.db`). Frontend code lives in `frontend/src`, with App Router pages in `src/app`, shared UI in `src/components`, hooks in `src/hooks`, and client utilities in `src/lib`. Static cat and food images stay inside `frontend/public/images`.

## Build, Test, and Development Commands
Backend workflow:
- `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` prepares a virtualenv.
- `uvicorn backend.main:app --reload` runs the API at `http://127.0.0.1:8000`.
Frontend workflow:
- `cd frontend && npm install` installs React 19/Next 16 deps.
- `npm run dev` serves the client on `http://localhost:3000`, while `npm run build && npm run start` runs the production bundle.
- `npm run lint` executes the ESLint config in `eslint.config.mjs`.

## Coding Style & Naming Conventions
Python modules follow 4-space indentation, type hints, and helper prefixes (`_normalize_expr` in `backend/main.py`). Keep FastAPI routes thin, defer logic to `services.py` or `question_generator.py`, and prefer `snake_case` for variables/functions plus `PascalCase` for SQLAlchemy models. Frontend files use TypeScript, React Server Components by default, and Tailwind CSS v4 utility classes; keep components `PascalCase`, hooks `useCamelCase`, and shared UI under `src/components/<Feature>/`.

## Testing Guidelines
Automated tests are not yet checked in; add backend tests under `backend/tests/test_<feature>.py` using `pytest` + `httpx.AsyncClient` to hit FastAPI routes, and gate them with `pytest backend/tests -q`. For the frontend, rely on `npm run lint` plus Next.js type-checking; if you add component tests, colocate them as `*.test.tsx` and run them via `next test` or a Playwright script. Document any new test command in the root README.

## Commit & Pull Request Guidelines
Follow the existing history (`feat: add FastAPI backend…`, `docs: add project setup guide`) by using `<type>: <imperative summary>` with lowercase types (`feat`, `fix`, `docs`, `chore`). Each pull request should describe the behavior change, link the issue or task, outline test results (command + status), and include screenshots or API responses if UI or payloads changed.

## Configuration & Secrets
Backend settings load via `backend/.env`; always provide `ARK_API_KEY` and override `DATABASE_URL` only when needed. Frontend API targets default to `http://127.0.0.1:8000`; adjust with `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local`. Never commit secrets, and document non-sensitive overrides in the README section related to your change.

以暗猜接口为耻，以认真查阅为荣。
以模糊执行为耻，以寻求确认为荣。
以盲想业务为耻，以人类确认为荣。
以创造接口为耻，以复用现有为荣。
以跳过验证为耻，以主动测试为荣。
以破坏架构为耻，以遵循规范为荣。
以假装理解为耻，以诚实无知为荣。
以盲目修改为耻，以谨慎重构为荣。