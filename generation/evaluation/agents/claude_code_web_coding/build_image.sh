CURRENT_DIR=$(cd "$(dirname "$0")";pwd)

cd ${CURRENT_DIR}

# Build Docker image
# Note: If you need proxy, uncomment and configure the proxy args below
docker build \
    --network host \
    -f Dockerfile.web_coding \
    -t web_bench/base:latest .

# With proxy (uncomment if needed):
# docker build \
#     --network host \
#     --build-arg http_proxy=http://your-proxy:port \
#     --build-arg https_proxy=http://your-proxy:port \
#     -f Dockerfile.web_coding \
#     -t web_bench/base:latest .