#!/bin/bash
# gVisor Installation Script for Serverless Project

set -e

echo "======================================"
echo "gVisor Integration for Serverless Project"
echo "======================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
  . /etc/os-release
  OS=$ID
else
  echo "Cannot detect OS. Please install gVisor manually."
  exit 1
fi

# Install gVisor based on OS
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
  echo "Installing gVisor for $OS..."
  
  # Add gVisor repo
  curl -fsSL https://gvisor.dev/archive.key | sudo gpg --dearmor -o /usr/share/keyrings/gvisor-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gvisor-archive-keyring.gpg] https://storage.googleapis.com/gvisor/releases release main" | sudo tee /etc/apt/sources.list.d/gvisor.list > /dev/null
  
  # Update and install
  apt-get update
  apt-get install -y runsc
  
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
  echo "Installing gVisor for $OS..."
  
  # For RHEL-based systems
  curl -fsSL https://gvisor.dev/archive.key | sudo gpg --dearmor -o /usr/share/keyrings/gvisor-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gvisor-archive-keyring.gpg] https://storage.googleapis.com/gvisor/releases release main" | sudo tee /etc/yum.repos.d/gvisor.repo > /dev/null
  
  # Install
  yum install -y runsc
  
else
  echo "Unsupported OS: $OS"
  echo "Please install gVisor manually by following the instructions at:"
  echo "https://gvisor.dev/docs/user_guide/install/"
  exit 1
fi

# Check if gVisor was installed correctly
if ! command -v runsc &> /dev/null; then
  echo "❌ Error: gVisor installation failed. 'runsc' command not found."
  exit 1
fi

# Configure Docker to use gVisor
echo "Configuring Docker to use gVisor..."

# Create Docker daemon configuration
DOCKER_CONFIG_DIR="/etc/docker"
DOCKER_CONFIG_FILE="$DOCKER_CONFIG_DIR/daemon.json"

# Ensure Docker config directory exists
mkdir -p "$DOCKER_CONFIG_DIR"

# Create or update daemon.json
if [ -f "$DOCKER_CONFIG_FILE" ]; then
  # Check if file is valid JSON
  if ! jq '.' "$DOCKER_CONFIG_FILE" > /dev/null 2>&1; then
    echo "❌ Warning: Existing daemon.json is not valid JSON. Creating backup and replacing."
    cp "$DOCKER_CONFIG_FILE" "$DOCKER_CONFIG_FILE.bak"
    echo '{
  "runtimes": {
    "runsc": {
      "path": "/usr/bin/runsc",
      "runtimeArgs": [
        "--platform=kvm"
      ]
    }
  }
}' > "$DOCKER_CONFIG_FILE"
  else
    # Update existing config
    TMP_CONFIG=$(mktemp)
    jq '.runtimes = (.runtimes // {}) | .runtimes.runsc = {"path": "/usr/bin/runsc", "runtimeArgs": ["--platform=kvm"]}' "$DOCKER_CONFIG_FILE" > "$TMP_CONFIG"
    mv "$TMP_CONFIG" "$DOCKER_CONFIG_FILE"
  fi
else
  # Create new config
  echo '{
  "runtimes": {
    "runsc": {
      "path": "/usr/bin/runsc",
      "runtimeArgs": [
        "--platform=kvm"
      ]
    }
  }
}' > "$DOCKER_CONFIG_FILE"
fi

# Restart Docker to apply changes
echo "Restarting Docker service..."
if systemctl is-active --quiet docker; then
  systemctl restart docker
  echo "Docker service restarted."
else
  echo "Docker service not running. Please start it manually."
fi

echo "✅ gVisor installation and configuration complete."
echo "Run the test script to verify the installation:"
echo "python -m execution_engine.test_gvisor"
