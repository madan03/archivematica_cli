# Standalone Archivematica CLI

A lightweight, standalone Python CLI for processing digital archives, inspired by Archivematica's automated workflow. It performs virus scanning, format identification, normalization, and packaging (AIP/DIP) using standard external tools.

## Features

- **Virus Scanning**: ClamAV integration.
- **Format Identification**: FIDO integration.
- **Normalization**: Converts images to TIFF (preservation) and JPG (access), videos to MKV (preservation) and MP4 (access).
- **Packaging**: Creates BagIt-compliant AIPs and DIPs.
- **Metadata**: Generates METS, PREMIS, MODS, and Dublin Core metadata.
- **Batch Processing**: Automatically processes all subdirectories in the transfer folder.

## Prerequisites

Ensure the following tools are installed on your system:

1.  **Python 3.10+**
2.  **ClamAV** (`clamscan`)
3.  **7-Zip** (`7z`)
4.  **FFmpeg** (`ffmpeg`)
5.  **ImageMagick** (`convert`)
6.  **Tree** (`tree`)

## Installation

We provide a script to install all system dependencies (Debian/Ubuntu) and Python requirements.

1.  **Run the installation script**:
    ```bash
    chmod +x install_package.sh
    ./install_package.sh
    ```

    This script will:
    - Update `apt` repositories.
    - Install system tools (ClamAV, 7-Zip, FFmpeg, ImageMagick, Tree).
    - Install Python dependencies from `requirements.txt`.

2.  **Verify Python Dependencies**:
    If you prefer to install Python dependencies manually:
    ```bash
    pip3 install -r src/standalone_cli/requirements.txt
    ```

## Configuration

The CLI uses a `.env` file for configuration.

1.  **Create `.env`**:
    Create a file named `.env` in the root directory.

2.  **Configure Paths**:
    Add the following variables to `.env`, adjusting the paths to your system:

    ```ini
    # Path to the directory containing transfers to be processed
    AM_TRANSFER_SOURCE=/path/to/your/transfers

    # Path where AIPs (Archival Information Packages) will be stored
    AM_AIP_STORAGE=/path/to/your/storage/aips

    # Path where DIPs (Dissemination Information Packages) will be stored
    AM_DIP_STORAGE=/path/to/your/storage/dips
    ```

3.  **Advanced Configuration (Optional)**:
    You can adjust settings in `src/standalone_cli/config.py`, such as:
    - `COMPRESSION_LEVEL`: Set to `0` for uncompressed DIPs, or `1-9` for 7-Zip compression.
    - `SCAN_FOR_VIRUSES`: True/False to enable/disable virus scanning.

## Usage

Run the CLI from the root of the repository:

```bash
python3 -m src.standalone_cli.main
```

The CLI will:
1.  Scan `AM_TRANSFER_SOURCE` for transfer subdirectories.
2.  Process each transfer individually.
3.  Generate an AIP in `AM_AIP_STORAGE`.
4.  Generate a DIP in `AM_DIP_STORAGE`.

### Command Line Overrides

You can override paths via command line arguments:

```bash
python3 -m src.standalone_cli.main --transfer-path /custom/transfers --aip-storage /custom/aips --dip-storage /custom/dips
```

## Output Structure

### AIP (Archival Information Package)
Stored as an uncompressed BagIt directory.

```
storage/aips/mptest_01-<UUID>/
├── bagit.txt
├── bag-info.txt
├── manifest-sha256.txt
├── tagmanifest-sha256.txt
└── data/
    ├── README.html
    ├── content/
    │   ├── objects/
    │   │   └── [Original Files]
    │   ├── logs/
    │   │   ├── structure_report.txt
    │   │   ├── virus_scan.log
    │   │   └── ...
    │   └── metadata/
    │       ├── dublin_core.xml
    │       ├── premis.xml
    │       ├── mods.xml
    │       ├── metadata.csv
    │       └── submissionDocumentation/
    │           ├── processingMCP.xml
    │           └── rights.csv
    ├── manifests/
    │   ├── manifests.json
    │   └── checksums.sha256
    └── thumbnails/
        └── [Thumbnail Images]
```

### DIP (Dissemination Information Package)
Stored as a `.7z` archive (default) or directory (if `COMPRESSION_LEVEL=0`).

```
storage/dips/mptest_01-<UUID>.7z
(Contents)
├── objects/
│   └── [Access Copies (JPG, MP4)]
├── thumbnails/
│   └── [Thumbnail Images]
└── metadata/
    ├── dip-metadata.xml
    └── rights-summary.txt
```

## Troubleshooting


-   **Tool not found errors**: Ensure external tools (clamscan, ffmpeg, etc.) are installed and in your system PATH.
