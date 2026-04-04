---
name: take_effect
description: Check uncommitted changes, determine if rebuild/restart needed, and apply changes.
---

Check uncommitted changes and apply them:

```bash
cd /home/bf/ragflow
git status
git diff --name-only
```

**Decision Logic:**

1. **Frontend changes** (anything under `web/`):
   - Run `cd /home/bf/ragflow/web && npm run build`
   - Wait for build to complete (check for errors)
   - No Docker restart needed (volume-mounted)

2. **Backend Python changes** (anything under `api/`, `rag/`, `common/`):
   - No rebuild needed
   - Restart Docker container: `sudo docker restart docker-ragflow-cpu-1`
   - Wait ~10 seconds for container to be ready

3. **Config/Docker changes** (docker-compose.yml, etc.):
   - Restart Docker: `sudo docker restart docker-ragflow-cpu-1`
   - Wait ~10 seconds

**Execute (if needed):**

Frontend rebuild:
```bash
cd /home/bf/ragflow/web
npm run build
```

Docker restart:
```bash
echo "bf" | sudo -S docker restart docker-ragflow-cpu-1

# Wait and verify using /v1/system/ping endpoint (more reliable)
for i in {1..20}; do
    sleep 2
    http_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9380/v1/system/ping 2>/dev/null)
    if [ "$http_code" = "200" ]; then
        echo "Application is ready"
        break
    fi
    echo "Waiting for application... ($i/20)"
done
```

**Note:** sudo password is `bf`.