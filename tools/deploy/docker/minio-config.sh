#!/bin/sh
# /scripts/create_buckets.sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Variables (passed from docker-compose environment)
MINIO_ALIAS="object-storage"
# Bucket names
BUCKET_PUBLIC="public"
BUCKET_PRIVATE="private"
BUCKET_LOGS="logs"

echo "Waiting for MinIO server at $MINIO_SERVER_URL..."

# Wait for MinIO to be reachable (optional, depends_on with healthcheck should handle this)
# Although depends_on with healthcheck is used, this adds an extra layer
# It might be useful if the healthcheck passes but the service isn't fully ready for mc operations
# We will rely on the depends_on condition primarily.

echo "Configuring MinIO client (mc)..."
# Add alias for the MinIO server using environment variables
mc alias set $MINIO_ALIAS $MINIO_SERVER_URL $MINIO_ACCESS_KEY $MINIO_SECRET_KEY

echo "MinIO client configured."

# --- Create Buckets ---
echo "Creating buckets..."

# Create bucket 1 (public read)
mc mb $MINIO_ALIAS/$BUCKET_PUBLIC || echo "Bucket $BUCKET_PUBLIC already exists."
echo "Setting policy for $BUCKET_PUBLIC..."
mc policy set download $MINIO_ALIAS/$BUCKET_PUBLIC
echo "Policy set to 'download' (read-only anonymous) for $BUCKET_PUBLIC."

# Create bucket 2 (private)
mc mb $MINIO_ALIAS/$BUCKET_PRIVATE || echo "Bucket $BUCKET_PRIVATE already exists."
echo "Setting policy for $BUCKET_PRIVATE..."
mc policy set none $MINIO_ALIAS/$BUCKET_PRIVATE
echo "Policy set to 'none' (private) for $BUCKET_PRIVATE."

# Create bucket 3 (logs - public write/upload)
mc mb $MINIO_ALIAS/$BUCKET_LOGS || echo "Bucket $BUCKET_LOGS already exists."
echo "Setting policy for $BUCKET_LOGS..."
mc policy set upload $MINIO_ALIAS/$BUCKET_LOGS
echo "Policy set to 'upload' (write-only anonymous) for $BUCKET_LOGS."


echo "Bucket creation and policy setting complete."

exit 0
