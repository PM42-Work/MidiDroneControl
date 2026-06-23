#!/bin/bash

# Configuration: Blender 4.3 uses Python 3.11
PY_VER="3.11"
TARGET_DIR="./dependencies"

mkdir -p "$TARGET_DIR"

install_platform() {
    PLATFORM=$1  
    OS_NAME=$2   
    echo "--- Processing $OS_NAME ($PLATFORM) ---"
    
    mkdir -p "temp_$OS_NAME"
    mkdir -p "$TARGET_DIR/$OS_NAME"
    
    # Download Mido and python-rtmidi
    pip download \
        --dest "temp_$OS_NAME" \
        --platform "$PLATFORM" \
        --python-version "$PY_VER" \
        --implementation cp \
        --only-binary=:all: \
        mido python-rtmidi
    
    # Extract all downloaded wheels
    for WHEEL_FILE in temp_$OS_NAME/*.whl; do
        if [ -f "$WHEEL_FILE" ]; then
            echo "Extracting $WHEEL_FILE..."
            unzip -q -o "$WHEEL_FILE" -d "$TARGET_DIR/$OS_NAME"
        fi
    done

    # Clean up temp folder
    rm -rf "temp_$OS_NAME"
}

# Download for all major platforms
install_platform "win_amd64" "win"
install_platform "manylinux_2_17_x86_64" "linux"
install_platform "macosx_11_0_arm64" "mac"

echo "Dependencies installed in $TARGET_DIR"