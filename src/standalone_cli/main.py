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
    # Validate paths
    if not os.path.exists(args.transfer_path):
        logging.error(f"Transfer path does not exist: {args.transfer_path}")
        sys.exit(1)
    
    # Create storage directories if they don't exist
    os.makedirs(args.aip_storage, exist_ok=True)
    os.makedirs(args.dip_storage, exist_ok=True)

    # Iterate over subdirectories in transfer_path
    transfer_items = os.listdir(args.transfer_path)
    transfers_found = False

    for item in transfer_items:
        item_path = os.path.join(args.transfer_path, item)
        
        if os.path.isdir(item_path):
            transfers_found = True
            logging.info(f"Found transfer: {item}")
            
            engine = WorkflowEngine(
                transfer_path=item_path,
                aip_path=args.aip_storage,
                dip_path=args.dip_storage,
                config=ProcessingConfiguration
            )
            try:
                engine.run()
            except Exception as e:
                logging.exception(f"Workflow failed for transfer {item}")
                # We continue to the next transfer instead of exiting
                continue

    if not transfers_found:
        logging.warning(f"No transfer directories found in {args.transfer_path}")

if __name__ == "__main__":
    main()
