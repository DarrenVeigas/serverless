#!/bin/bash
# gVisor Integration Script for Serverless Project

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script with sudo or as root"
  exit 1
fi

echo "Starting gVisor integration for serverless project..."

# Step 1: Check if gVisor is already installed
if command -v runsc &> /dev/null; then
  echo "gVisor is already installed. Checking version..."
  runsc --version
else
  echo "Installing gVisor..."
  # Using the latest installation method from Google's gVisor repository
  curl -fsSL https://storage.googleapis.com/gvisor/releases/release/latest/install.sh | bash
  apt-get update && apt-get install -y runsc
fi

# Step 2: Configure Docker to use gVisor
echo "Configuring Docker to use gVisor runtime..."
mkdir -p /etc/docker

# Backup existing daemon.json if it exists
if [ -f /etc/docker/daemon.json ]; then
  cp /etc/docker/daemon.json /etc/docker/daemon.json.backup
  echo "Backed up existing daemon.json to daemon.json.backup"
  
  # Check if runtimes is already configured
  if grep -q "runtimes" /etc/docker/daemon.json; then
    echo "Runtime configuration exists. Adding gVisor runtime to existing configuration..."
    # Use jq to add runsc runtime if jq is available
    if command -v jq &> /dev/null; then
      jq '.runtimes.runsc = {"path": "/usr/bin/runsc", "runtimeArgs": ["--platform=kvm"]}' /etc/docker/daemon.json > /tmp/daemon.json
      mv /tmp/daemon.json /etc/docker/daemon.json
    else
      echo "jq not found. Please manually edit /etc/docker/daemon.json to add the runsc runtime."
      echo "Refer to the gVisor installation documentation for guidance."
    fi
  else
    # Merge with existing configuration
    echo "Adding gVisor runtime configuration to daemon.json..."
    TMP_FILE=$(mktemp)
    jq -s '.[0] * {"runtimes": {"runsc": {"path": "/usr/bin/runsc", "runtimeArgs": ["--platform=kvm"]}}}' /etc/docker/daemon.json > "$TMP_FILE"
    mv "$TMP_FILE" /etc/docker/daemon.json
  fi
else
  # Create new daemon.json with gVisor runtime
  echo '{
  "runtimes": {
    "runsc": {
      "path": "/usr/bin/runsc",
      "runtimeArgs": [
        "--platform=kvm"
      ]
    }
  }
}' > /etc/docker/daemon.json
  echo "Created new daemon.json with gVisor runtime configuration"
fi

# Step 3: Restart Docker service
echo "Restarting Docker service..."
systemctl restart docker
sleep 3

# Step 4: Verify installation
echo "Verifying gVisor installation..."
docker info | grep -A 5 "Runtimes"

# Step 5: Update serverless project configuration
echo "Updating serverless project configuration..."

# Create a runsc configuration file
mkdir -p /etc/runsc
echo '{
  "debug": true,
  "log_dir": "/var/log/runsc",
  "debug_log": "/var/log/runsc/debug.log"
}' > /etc/runsc/config.json

# Create log directory
mkdir -p /var/log/runsc

# Test gVisor with a sample container
echo "Testing gVisor with a sample container..."
docker run --runtime=runsc --rm hello-world

echo "gVisor integration completed!"
echo "You can now use gVisor for your serverless functions by adding --runtime=runsc to your Docker run commands"
echo "Or by updating your deployment configurations to use the runsc runtime."
