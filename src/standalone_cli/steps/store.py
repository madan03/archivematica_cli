
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
        
        sip_path = self.context['sip_path']
        sip_uuid = self.context.get('sip_uuid', 'no-uuid')
        sip_name = os.path.basename(sip_path)
        
        # DIP Name: <SIP_Name>-<UUID> (or just UUID in some configs, but usually Name-UUID)
        dip_name = f"{sip_name}-{sip_uuid}"
        dest_path = os.path.join(self.context['dip_path'], dip_name)
        
        logger.info(f"Storing DIP at {dest_path}...")
        os.makedirs(dest_path, exist_ok=True)
        
        # DIP Structure:
        #   objects/ (Access copies)
        #   thumbnails/
        #   METS.<uuid>.xml
        
        # Source paths in SIP
        data_dir = os.path.join(sip_path, 'data')
        content_dir = os.path.join(data_dir, 'content')
        
        # 1. Copy Objects
        src_objects = os.path.join(content_dir, 'objects')
        dst_objects = os.path.join(dest_path, 'objects')
        if os.path.exists(src_objects):
            try:
                shutil.copytree(src_objects, dst_objects)
            except Exception as e:
                logger.warning(f"Failed to copy objects to DIP: {e}")
        
        # 2. Copy Thumbnails
        src_thumbs = os.path.join(data_dir, 'thumbnails')
        dst_thumbs = os.path.join(dest_path, 'thumbnails')
        if os.path.exists(src_thumbs):
            try:
                shutil.copytree(src_thumbs, dst_thumbs)
            except Exception as e:
                logger.warning(f"Failed to copy thumbnails to DIP: {e}")

        # 3. Copy METS
        # Find METS file in data/
        mets_file = None
        for f in os.listdir(data_dir):
            if f.startswith("METS.") and f.endswith(".xml"):
                mets_file = f
                break
        
        if mets_file:
            src_mets = os.path.join(data_dir, mets_file)
            dst_mets = os.path.join(dest_path, mets_file)
            try:
                shutil.copy2(src_mets, dst_mets)
            except Exception as e:
                logger.warning(f"Failed to copy METS to DIP: {e}")
        else:
            logger.warning("No METS file found in SIP data directory for DIP.")

        # 4. Create Metadata
        dst_metadata = os.path.join(dest_path, 'metadata')
        os.makedirs(dst_metadata, exist_ok=True)
        with open(os.path.join(dst_metadata, 'dip-metadata.xml'), 'w') as f:
            f.write('<dip_metadata>Placeholder</dip_metadata>')
        with open(os.path.join(dst_metadata, 'rights-summary.txt'), 'w') as f:
            f.write('Rights Summary Placeholder')

        logger.info("DIP structure created.")

        # 5. Compress DIP
        if self.context['config'].COMPRESSION_ALGORITHM == "7z":
            archive_name = f"{dest_path}.7z"
            logger.info(f"Compressing DIP to {archive_name}...")
            try:
                # 7z a archive.7z path/to/dip/*
                # We want the archive to contain the DIP folder or just contents?
                # Usually DIPs are zipped folders.
                cmd = [Paths.SEVEN_ZIP_CMD, "a", archive_name, dest_path]
                subprocess.run(cmd, check=True, capture_output=True)
                logger.info("DIP compressed and stored.")
            except Exception as e:
                logger.error(f"Failed to compress DIP: {e}")
        else:
            logger.info("DIP stored (uncompressed).")
