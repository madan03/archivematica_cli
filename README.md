# Standalone Archivematica CLI

This is a standalone Python CLI for processing digital archives, inspired by Archivematica's automated workflow. It performs virus scanning, format identification, normalization, and packaging (AIP/DIP) using standard external tools.

## Prerequisites

Ensure the following tools are installed and available in your system PATH:

1.  **Python 3.8+**
2.  **ClamAV** (`clamscan`) - For virus scanning.
3.  **FIDO** (`fido`) - For file format identification.
4.  **7-Zip** (`7z`) - For extraction and compression.
5.  **FFmpeg** (`ffmpeg`) - For audio/video normalization.
6.  **ImageMagick** (`magick` or `convert`) - For image normalization and thumbnails.
7.  **Tree** (`tree`) - For generating directory structure reports.

### Python Dependencies

Install the required Python packages:

```bash
pip install -r src/standalone_cli/requirements.txt
```

## Configuration

The CLI uses a `.env` file for configuration.

1.  Create a `.env` file in the root directory (or copy the example if provided).
2.  Define the following variables:

    ```ini
    # Path to the directory containing transfers to be processed
    AM_TRANSFER_SOURCE=C:\path\to\transfers

    # Path where AIPs (Archival Information Packages) will be stored
    AM_AIP_STORAGE=C:\path\to\storage\aips

    # Path where DIPs (Dissemination Information Packages) will be stored
    AM_DIP_STORAGE=C:\path\to\storage\dips
    ```

3.  You can also adjust advanced settings (like disabling specific steps) in `src/standalone_cli/config.py`.

## Usage

Run the CLI from the root of the repository:

```bash
python -m src.standalone_cli.main
```

By default, it will look for transfers in the configured `AM_TRANSFER_SOURCE` directory.

### Command Line Overrides

You can still override paths via command line arguments if desired:

```bash
python -m src.standalone_cli.main --transfer-path /path/to/transfer --aip-storage /path/to/aips --dip-storage /path/to/dips
```

## Workflow Steps

The CLI performs the following "Automated" workflow:

1.  **Scan for viruses**: Scans the transfer directory using ClamAV.
2.  **Assign UUIDs**: Renames directories with unique identifiers.
3.  **Structure Report**: Generates a directory tree text file.
4.  **Identify Formats**: Uses FIDO to identify file formats.
5.  **Extract Packages**: Extracts compressed files (zip, rar, etc.).
6.  **Normalize**: Converts media to preservation and access formats.
7.  **Create SIP (BagIt)**: Restructures the transfer into a BagIt-compliant SIP.
    *   Creates `bagit.txt`, `bag-info.txt`, and manifests.
    *   Moves content to `data/objects`.
    *   Generates dummy METS and README files.
8.  **Store AIP**: Packages the SIP and moves it to AIP storage.
9.  **Store DIP**: Moves access copies to DIP storage.

## Troubleshooting

*   **Tool not found errors**: Ensure the external tools (clamscan, ffmpeg, etc.) are in your system's PATH or update the `Tool Paths` in `config.py` with absolute paths.
*   **Permission errors**: Ensure the script has read/write access to the source and storage directories.
