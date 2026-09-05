# Authentication & Authorization

UDYOGSETU uses **JWT bearer tokens** issued by `app/core/security.py` and
enforced by `app/api/deps.py`.

## Roles

| Role | Purpose |
|------|---------|
| `ENTREPRENEUR` | Create projects, upload documents, submit & track own applications |
| `OFFICER` | Review, approve/reject, raise queries, run analytics |
| `ADMIN` | Fast-track approvals, mark expired, full system control |

`UserRole` enum: `app/models/__init__.py`.

## Flow

1. `POST /api/auth/register` — create a user (`UserRegister`:
   email, name, phone, password, role).
2. `POST /api/auth/login` — returns `{access_token, token_type, expires_in}`.
3. Send `Authorization: Bearer <token>` on all subsequent requests.
4. `POST /api/auth/refresh` — issue a fresh token for a still-valid token.
5. `POST /api/auth/logout` — client-side token discard.

## Token payload

```python
create_access_token(data={"sub": user_id, "email": ..., "role": ...})
```

`get_current_user` decodes the token and returns a dict with `sub` (user UUID)
and `role`. `get_current_user` is an async dependency used by protected routes.

## Ownership enforcement

`app/api/deps.py` provides:

- `require_auth` — any authenticated user.
- `require_project_owner` — user must own the project.
- `get_owned_approval` / `_ensure_owner` — approval must belong to a project the
  user owns (used for document, application and synchronization endpoints).

## Configuration

- `JWT_SECRET_KEY` (required; set a long random value).
- `JWT_ALGORITHM` (default `HS256`).
- `JWT_EXPIRATION_HOURS` (default `24`).

> In the Docker Compose dev environment the secret is not persisted, so a
> container restart regenerates it and clients must log in again.
