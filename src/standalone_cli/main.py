import argparse
import logging
import sys
import os
from .engine import WorkflowEngine
from .config import Paths, ProcessingConfiguration

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Standalone Archivematica CLI")
    parser.add_argument('--transfer-path', help="Path to the transfer directory", default=Paths.TRANSFER_SOURCE)
    parser.add_argument('--aip-storage', help="Path to store AIPs", default=Paths.AIP_STORAGE)
    parser.add_argument('--dip-storage', help="Path to store DIPs", default=Paths.DIP_STORAGE)

    args = parser.parse_args()

    # Validate paths
    if not os.path.exists(args.transfer_path):
        logging.error(f"Transfer path does not exist: {args.transfer_path}")
        sys.exit(1)
    
    # Create storage directories if they don't exist
    os.makedirs(args.aip_storage, exist_ok=True)
    os.makedirs(args.dip_storage, exist_ok=True)

    engine = WorkflowEngine(
        transfer_path=args.transfer_path,
        aip_path=args.aip_storage,
        dip_path=args.dip_storage,
        config=ProcessingConfiguration
    )
    try:
        engine.run()
    except Exception as e:
        logging.exception("Workflow failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
