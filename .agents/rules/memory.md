# Rules for AI Assistant

## Git Commits

- **ALWAYS get user permission before committing**. Do NOT commit without explicit user approval.
- Ask for confirmation before running `git commit` commands.

## Environment

- Docker container: `docker-ragflow-cpu-1`
- sudo password: `bf`

## Deployment

- Frontend builds are volume-mounted from `web/dist/`
- Deploy frontend using: `npm run build` (volume-mounted, auto-reload)
- Python code changes require Docker restart