FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and language runtimes
# The developer agent detects project languages and uses these tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        wget \
        unzip \
        # Node.js (for MCP servers via npx + JS/TS projects)
        nodejs \
        npm \
        # Go
        golang \
        # Java (JDK for maven/gradle projects)
        default-jdk \
        # General
        jq \
    && rm -rf /var/lib/apt/lists/*

# Install modern Node.js (LTS) via n for better npm/npx support
RUN npm install -g n && n lts && hash -r

# Install common package managers and dev tools
RUN npm install -g yarn pnpm && \
    pip install --no-cache-dir poetry uv

# Install glab CLI for GitLab operations
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "arm64" ]; then GLAB_ARCH="arm64"; else GLAB_ARCH="amd64"; fi && \
    GLAB_VERSION=$(curl -fsSL "https://gitlab.com/api/v4/projects/34675721/releases" | jq -r '.[0].tag_name' | sed 's/^v//') && \
    curl -fsSL "https://gitlab.com/gitlab-org/cli/-/releases/v${GLAB_VERSION}/downloads/glab_${GLAB_VERSION}_linux_${GLAB_ARCH}.tar.gz" \
    -o /tmp/glab.tar.gz && \
    tar -xzf /tmp/glab.tar.gz -C /usr/local/bin --strip-components=1 bin/glab && \
    rm /tmp/glab.tar.gz

# Install Maven
RUN curl -fsSL https://dlcdn.apache.org/maven/maven-3/3.9.16/binaries/apache-maven-3.9.16-bin.tar.gz \
    | tar -xz -C /opt && \
    ln -s /opt/apache-maven-3.9.16/bin/mvn /usr/local/bin/mvn

# Copy dependency files first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Install the project
RUN pip install --no-cache-dir -e .

# Default command
CMD ["python", "-m", "src.main"]
