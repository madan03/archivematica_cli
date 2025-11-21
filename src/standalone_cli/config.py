import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ProcessingConfiguration:
    # Processing Configuration
    SCAN_FOR_VIRUSES = True
    ASSIGN_UUIDS = True
    GENERATE_STRUCTURE_REPORT = True
    IDENTIFY_FORMAT_TRANSFER = True
    EXTRACT_PACKAGES = True
    DELETE_PACKAGE_AFTER_EXTRACTION = True
    CHECK_ORIGINALS_POLICY = True
    EXAMINE_CONTENTS = True
    CREATE_SIP = True
    IDENTIFY_FORMAT_INGEST = True
    NORMALIZE = True
    APPROVE_NORMALIZATION = True
    THUMBNAIL_MODE = True
    CHECK_PRESERVATION_POLICY = True
    CHECK_ACCESS_POLICY = False
    BIND_PIDS = False
    DOCUMENT_EMPTY_DIRECTORIES = True
    TRANSCRIBE_SIP_CONTENTS = False
    IDENTIFY_FORMAT_SUBMISSION = True
    COMPRESSION_ALGORITHM = "Uncompressed" # Options: "Uncompressed", "7z", "tar"
    COMPRESSION_LEVEL = 1 # 1 (fastest) to 9 (ultra)
    STORE_AIP = True
    UPLOAD_DIP = True
    STORE_DIP = True

class Paths:
    # Default paths - EDIT THESE or set via environment variables
    TRANSFER_SOURCE = os.getenv("AM_TRANSFER_SOURCE", r"C:\Users\madan\Documents\archivematica\transfers")
    AIP_STORAGE = os.getenv("AM_AIP_STORAGE", r"C:\Users\madan\Documents\archivematica\storage\aips")
    DIP_STORAGE = os.getenv("AM_DIP_STORAGE", r"C:\Users\madan\Documents\archivematica\storage\dips")

    # Tool Paths (Ensure these are in PATH or provide absolute paths)
    CLAMSCAN_CMD = "clamscan"
    TREE_CMD = "tree" # Windows: might need 'tree.com' or similar if using GnuWin32, or just 'tree' for cmd built-in (but cmd built-in is limited)
    FIDO_CMD = "fido"
    SEVEN_ZIP_CMD = "7z"
    FFMPEG_CMD = "ffmpeg"
    CONVERT_CMD = "magick" # ImageMagick v7+ uses 'magick', v6 uses 'convert'
