---
sidebar_position: 4
slug: /scan_local_directory
sidebar_custom_props: {
  categoryIcon: SiDirectory
}
---
# Scan Local Directory

RAGFlow supports scanning directories on the server's local filesystem and importing files into your knowledge base. Unlike traditional file upload, this feature does NOT store the original files in MinIO storage - it only stores the file paths and creates embedding vectors for retrieval.

## When to Use This Feature

- **Large files**: When you have large files that you don't want to duplicate in MinIO storage
- **Shared directories**: When multiple knowledge bases need to access the same files
- **Server access**: When the RAGFlow server has direct access to the files (e.g., network drives, local disks)
- **Dynamic content**: When files are updated frequently and you want automatic synchronization

## Differences from Traditional Upload

| Feature | Traditional Upload | Local Directory Scan |
|---------|------------------|---------------------|
| Storage | Files stored in MinIO | Only file paths and index vector stored |
| File access | Through MinIO database | Direct filesystem access |
| Auto-sync | Manual re-upload | Configurable automatic scan |
| Storage cost | Uses MinIO storage | No additional storage |

## Using the Feature

### 1. Open Scan Directory Dialog

Navigate to your knowledge base and click **Scan Local Directory** button.

### 2. Configure Scan Settings

- **Directory Path**: Enter the absolute path of the directory on the server (e.g., `/home/user/documents`)
- **Scan Interval**: Choose how often to automatically scan for new files:
  - Every 10 minutes
  - Every 30 minutes
  - Every 1 hour
  - Every 3 hours
  - Every day
  - Every week
  - Every 4 weeks (default)

### 3. Supported File Types

The feature supports a wide range of file types:

- **Documents**: PDF, DOC, DOCX, PPT, PPTX, TXT, MD, RTF, etc.
- **Spreadsheets**: XLS, XLSX, CSV
- **Code**: PY, JS, JAVA, C, C++, PHP, GO, etc.
- **Data**: JSON, JSONL, XML, YAML
- **Images**: JPG, JPEG, PNG, GIF, TIFF, SVG, etc. (with OCR support)
- **Audio**: MP3, WAV, FLAC, AAC, OGG, etc. (with transcription support)

### 4. File Size and Count Limits

- **File size limit**: 512MB per file (for visual models like OCR/VLM)
- **File count limit**: 10,000 files per directory
  - If a directory exceeds this limit, split it into multiple subdirectories and add them separately

### 5. Managing Scanned Directories

After first scanning, you can:

- **View scanned directories**: See all directories linked to the knowledge base
- **Update scan interval**: Change how often automatic scanning occurs
- **Remove directories**: Delete a directory from the scan list (will delete relative files from the knowledge base).

## Synchronization Logic

The scanner automatically handles file changes in the scanned directory:

1. **New files**: If a new file is added to the directory, it will be added to the database and parsing will be triggered automatically.

2. **Modified files**: If a scanned file is modified (detected by file size or modification time change), the existing record will be updated and re-parsing will be triggered.

3. **Deleted files**: If a file is deleted from the local directory, the corresponding record in the database will be automatically removed.

4. **Unchanged files**: Files that have not been modified (same size and mtime) will be skipped to save processing time.

## Viewing Scanned Files

Clicking on a reference document in chat will open the file in a new browser window. The file is read directly from the local filesystem.

## Notes

- The user running the RAGFlow container must have read permissions to the scanned directories
- Automatic scanning runs in the background at the configured interval

## Security Restrictions

For security reasons, scanned directories must be **Docker-mounted volumes**. The system automatically detects mounted volumes from `/proc/self/mountinfo` and only allows scanning paths within these directories.

**Allowed mount points** (automatically detected):
- Volumes mounted to the RAGFlow container (e.g., `/hdd1`, `/hdd2`, `/data`)
- System directories like `/proc`, `/dev`, `/sys` are excluded

If you try to scan a directory outside the mounted volumes, you will receive an error message indicating which volumes are allowed.
