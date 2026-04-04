---
name: db_size
description: Check disk usage of all databases (MySQL, MinIO, Redis)
---

Check database storage sizes:

```bash
echo "bf" | sudo -S docker volume ls | grep -E "mysql|minio|redis|ragflow"

echo "bf" | sudo -S du -sh /var/lib/docker/volumes/docker_mysql_data/_data
echo "bf" | sudo -S du -sh /var/lib/docker/volumes/docker_minio_data/_data
echo "bf" | sudo -S du -sh /var/lib/docker/volumes/docker_redis_data/_data
```

**Summary:**
- **MySQL**: Relational database - users, KB, documents, chunks, configs
- **MinIO**: Object storage - document files, embeddings, binary data
- **Redis**: In-memory cache - sessions, tokens,实时缓存

**Note:** sudo password is `bf`.