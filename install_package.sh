#!/bin/bash

# Exit on any error
set -e

# Function to check and install packages
install_if_missing() {
    PACKAGE_NAME=$1
    COMMAND_NAME=$2

    echo "Checking for $PACKAGE_NAME..."

    if command -v "$COMMAND_NAME" >/dev/null 2>&1; then
        echo "$PACKAGE_NAME is already installed. Skipping..."
    else
        echo "$PACKAGE_NAME not found. Installing..."
        sudo apt update
        sudo apt install -y "$PACKAGE_NAME"
        echo "$PACKAGE_NAME installed successfully!"
    fi

    echo "-----------------------------------------"
    echo "-----------------------------------------"
    echo "-----------------------------------------"
}

# Install ClamAV
install_if_missing "clamav" "clamscan"

# Install 7-Zip
install_if_missing "p7zip-full" "7z"

# Install FFmpeg
install_if_missing "ffmpeg" "ffmpeg"

# Install ImageMagick
install_if_missing "imagemagick" "convert"

# Install Tree
install_if_missing "tree" "tree"

# Install python3-pip
install_if_missing "python3-pip" "pip3"

# Install Python Requirements
echo "Installing Python dependencies..."
pip3 install -r src/standalone_cli/requirements.txt

echo "All installations completed!"
