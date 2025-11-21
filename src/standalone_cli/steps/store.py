import shutil
import logging
import os
import subprocess
from . import Step
from ..config import Paths

logger = logging.getLogger(__name__)

class StoreAIPStep(Step):
    def execute(self):
        logger.info("Storing AIP...")
        sip_path = self.context['sip_path']
        sip_name = os.path.basename(sip_path)
        if not sip_name: # handle trailing slash
            sip_name = os.path.basename(os.path.dirname(sip_path))
            
        # AIP Name usually includes UUID
        aip_name = f"{sip_name}-{self.context.get('sip_uuid', 'no-uuid')}"
        dest_path = os.path.join(self.context['aip_path'], aip_name)
        
        # Compression
        if self.context['config'].COMPRESSION_ALGORITHM == "7z":
            archive_name = f"{dest_path}.7z"
            logger.info(f"Compressing AIP to {archive_name}...")
            try:
                cmd = [Paths.SEVEN_ZIP_CMD, "a", archive_name, sip_path]
                subprocess.run(cmd, check=True, capture_output=True)
                logger.info("AIP compressed and stored.")
            except Exception as e:
                logger.error(f"Failed to compress AIP: {e}")
        else:
            # Uncompressed copy
            logger.info(f"Copying AIP to {dest_path}...")
            try:
                shutil.copytree(sip_path, dest_path)
                logger.info("AIP stored.")
            except Exception as e:
                logger.error(f"Failed to store AIP: {e}")

class StoreDIPStep(Step):
    def execute(self):
        logger.info("Storing DIP...")
        # For DIP, we usually only want the access copies and some metadata.
        # Since we didn't strictly separate access/preservation in NormalizeStep (we just made files),
        # we'll simulate creating a DIP by copying the whole SIP structure but filtering for access formats if possible.
        # Or just copy the whole thing for now as a "DIP".
        
        sip_path = self.context['sip_path']
        sip_name = os.path.basename(sip_path)
        dip_name = f"{sip_name}-{self.context.get('sip_uuid', 'no-uuid')}-DIP"
        dest_path = os.path.join(self.context['dip_path'], dip_name)
        
        logger.info(f"Storing DIP at {dest_path}...")
        try:
            shutil.copytree(sip_path, dest_path)
            logger.info("DIP stored.")
        except Exception as e:
            logger.error(f"Failed to store DIP: {e}")
