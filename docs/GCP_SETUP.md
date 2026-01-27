
# GCP Setup Guide for Video Creator

## Quick Start (Free Tier Demo)

### 1. Create GCP Project
```bash
# Using gcloud CLI
gcloud projects create video-creator-demo --name="Video Creator Demo"
gcloud config set project video-creator-demo
```

Or via [Google Cloud Console](https://console.cloud.google.com/):
- Click "Select a Project" → "New Project"
- Name: `video-creator-demo`
- Click "Create"

### 2. Enable Cloud Storage API
```bash
gcloud services enable storage-api.googleapis.com
```

Or via Console:
- Navigation Menu → "APIs & Services" → "Library"
- Search "Cloud Storage API" → Click → "Enable"

### 3. Create GCS Bucket
```bash
# Set your project ID and bucket name
export PROJECT_ID="video-creator-demo"
export BUCKET_NAME="video-creator-bucket-$(date +%s)"

# Create bucket (must be globally unique name)
gcloud storage buckets create gs://${BUCKET_NAME} \
  --project=${PROJECT_ID} \
  --location=US \
  --uniform-bucket-level-access
```

### 4. Create Service Account (for local dev)
```bash
# Create service account
gcloud iam service-accounts create video-creator-sa \
  --display-name="Video Creator Service Account"

# Grant Storage Admin role
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:video-creator-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Generate JSON key
gcloud iam service-accounts keys create ./gcp-credentials.json \
  --iam-account=video-creator-sa@${PROJECT_ID}.iam.gserviceaccount.com
```

### 5. Configure Environment

Create `.env` file in project root:
```bash
# Copy from template
cp .env.example .env

# Edit .env with your values
STORAGE_TYPE=gcp
GCP_PROJECT_ID=video-creator-demo
GCP_BUCKET_NAME=video-creator-bucket-TIMESTAMP
GCP_CREDENTIALS_PATH=./gcp-credentials.json

# Keep other settings
OPENAI_API_KEY=sk-your-openai-key
MINIMAX_API_KEY=your-minimax-key
```

### 6. Install Dependencies
```bash
# Update dependencies with GCP support
uv sync
```

### 7. Test Connection
```python
import asyncio
from src.config import Settings
from utils.storage import get_storage_client

async def test_gcp():
    settings = Settings()
    storage = get_storage_client(
        storage_type=settings.storage_type,
        project_id=settings.gcp_project_id,
        bucket_name=settings.gcp_bucket_name,
        credentials_path=settings.gcp_credentials_path,
    )
    
    # Test upload
    test_file = "./test.txt"
    with open(test_file, "w") as f:
        f.write("Hello GCP!")
    
    url = await storage.upload_file(test_file, "test/test.txt")
    print(f"✅ Uploaded to: {url}")
    
    # Test signed URL
    signed_url = await storage.get_signed_url("test/test.txt")
    print(f"✅ Signed URL (24h): {signed_url}")
    
    # Cleanup
    await storage.delete_file("test/test.txt")
    print("✅ Cleanup done")

asyncio.run(test_gcp())
```

## Environment Variables Reference

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `STORAGE_TYPE` | Yes | `gcp` | Set to `gcp` for GCP backend |
| `GCP_PROJECT_ID` | Yes | `video-creator-demo` | Your GCP project ID |
| `GCP_BUCKET_NAME` | Yes | `video-creator-bucket-1234567890` | Must be globally unique |
| `GCP_CREDENTIALS_PATH` | No | `./gcp-credentials.json` | If empty, uses `GOOGLE_APPLICATION_CREDENTIALS` env var |

## Cost Optimization (Free Tier)

### Free Tier Limits (as of 2026)
- **Storage**: 5 GB/month free
- **Operations**: 5,000 class A operations, 50,000 class B operations free
- **Egress**: 1 GB/month free within same region

### Tips for Cost Control
1. **Keep credentials.json in `.gitignore`** (don't commit it)
2. **Use `GOOGLE_APPLICATION_CREDENTIALS` env var** instead of file path:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-credentials.json
   ```
3. **Set bucket lifecycle policies** (auto-delete old segments after 30 days):
   ```bash
   gcloud storage buckets describe gs://${BUCKET_NAME} \
     --format=json | jq '.lifecycle' # View current
   ```
4. **Monitor usage**:
   ```bash
   gcloud storage du gs://${BUCKET_NAME}
   ```

## Switching Back to Local Storage

If you need to switch back to local storage during development:
```bash
# Update .env
STORAGE_TYPE=local
```

The `get_storage_client()` factory will automatically use `LocalStorage` instead.

## Troubleshooting

### Error: `google.auth.exceptions.DefaultCredentialsError`
**Solution**: Set `GOOGLE_APPLICATION_CREDENTIALS` env var:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-credentials.json
```

### Error: `google.cloud.exceptions.NotFound: 404 Bucket not found`
**Solution**: Verify bucket exists and is accessible:
```bash
gcloud storage buckets list
gcloud storage ls gs://${BUCKET_NAME}
```

### Error: `Permission denied: service account not authorized`
**Solution**: Grant correct IAM role to service account:
```bash
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:video-creator-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```

## References

- [GCP Getting Started](https://cloud.google.com/docs/get-started)
- [Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Service Accounts Guide](https://cloud.google.com/docs/authentication/application-default-credentials)
- [gcloud CLI Reference](https://cloud.google.com/sdk/gcloud/reference)
