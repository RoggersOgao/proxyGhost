#!/bin/bash

# Function to check if a command is installed
command_installed() {
    command -v "$1" &>/dev/null
}

# Function to install a package using apt
install_apt_package() {
    echo "Installing $1..."
    sudo apt install -y "$1"
}

# Determine the Python version

install_python_packages() {
    # Get the Python version
    PYTHON_VERSION=$(python3 --version | cut -d ' ' -f2)

    # Validate the Python version
    if [ -z "$PYTHON_VERSION" ]; then
        echo "Error: Unable to determine Python version."
        return 1
    fi

    # Print the Python version
    echo "Python version: $PYTHON_VERSION"

    # Remove the EXTERNALLY-MANAGED file
    if [ -f "/usr/lib/python${PYTHON_VERSION:0:4}/EXTERNALLY-MANAGED" ]; then
        echo "Removing /usr/lib/python${PYTHON_VERSION:0:4}/EXTERNALLY-MANAGED file..."
        sudo rm /usr/lib/python${PYTHON_VERSION:0:4}/EXTERNALLY-MANAGED
    else
        echo "Warning: /usr/lib/python${PYTHON_VERSION:0:4}/EXTERNALLY-MANAGED file not found."
    fi

    # Function to install required Python packages
    echo "Installing required packages: python3-stem, python3-requests..."

    # Install build-essential and python3-dev
    if sudo apt-get install build-essential python3-dev; then
        echo "build-essential and python3-dev installed successfully."
    else
        echo "Error: Failed to install build-essential and python3-dev."
        return 1
    fi

    # Install python3-stem and python3-requests
    if sudo apt install -y python3-stem python3-requests; then
        echo "python3-stem and python3-requests installed successfully."
    else
        echo "Error: Failed to install python3-stem and python3-requests."
        return 1
    fi

    # Install Cython using pip3
    if pip3 install Cython; then
        echo "Cython installed successfully."
    else
        echo "Error: Failed to install Cython."
        return 1
    fi
}

# Check and install Python 3
if ! command_installed python3; then
    echo "Python 3 not found. Installing..."
    sudo apt update
    install_apt_package python3
fi

# Check and install pip
if ! command_installed pip3; then
    echo "pip not found. Installing..."
    install_apt_package python3-pip
fi

# Install Python packages
install_python_packages

# Determine Python version
PYTHON_VERSION=$(python3 --version | awk '{print $2}' | cut -d. -f1-2)
PYTHON_INCLUDE_DIR="/usr/include/python${PYTHON_VERSION}"
PYTHON_LIB="-lpython${PYTHON_VERSION}"

# Set the path to the proxyghost.py file
PROXYGHOST_PY_FILE="./proxyghost.py"
if [ ! -f "${PROXYGHOST_PY_FILE}" ]; then
    echo "[ERROR] ${PROXYGHOST_PY_FILE} not found in the current directory."
    exit 1
fi

# Build process
echo "Building Proxyghost..."
mkdir -p build
cd build || { echo "Failed to enter build directory."; exit 1; }

# Generate C code from Python script
cython "../${PROXYGHOST_PY_FILE}" --embed -o proxyghost.c --verbose
if [ $? -eq 0 ]; then
    echo "[SUCCESS] Generated C code"
else
    echo "[ERROR] Build failed. Unable to generate C code using cython3"
    exit 1
fi

# Compile the C code
gcc -Os -I "${PYTHON_INCLUDE_DIR}" -o proxyghost proxyghost.c "${PYTHON_LIB}" -lpthread -lm -lutil -ldl
if [ $? -eq 0 ]; then
    echo "[SUCCESS] Compiled to static binary"
else
    echo "[ERROR] Build failed"
    exit 1
fi

# Copy the binary to /usr/bin/
if [ $(id -u) -ne 0 ]; then
    echo "Running as non-root user. Using sudo to copy binary to /usr/bin/"
    sudo cp -r proxyghost /usr/bin/
else
    echo "Running as root user. Copying binary to /usr/bin/"
    cp -r proxyghost /usr/bin/
fi
if [ $? -eq 0 ]; then
    echo "[SUCCESS] Copied binary to /usr/bin"
else
    echo "[ERROR] Unable to copy"
    exit 1
fi

echo "Proxyghost installation and setup complete."
