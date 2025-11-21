import logging
import os
import subprocess
import shutil
import hashlib
import datetime
from . import Step
from ..config import Paths

logger = logging.getLogger(__name__)

class NormalizeStep(Step):
    def execute(self):
        logger.info("Normalizing content for preservation and access...")
        # Simple normalization logic:
        # - Images -> TIFF (Preservation), JPG (Access)
        # - Video -> MKV (Preservation), MP4 (Access)
        # - Audio -> WAV (Preservation), MP3 (Access)
        
        # Note: CreateSIPStep runs BEFORE NormalizeStep in our engine list, 
        # so we expect the structure to be in 'data/objects' now.
        # Let's find where the objects are.
        
        sip_root = self.context['sip_path']
        objects_dir = os.path.join(sip_root, 'data', 'objects')
        
        if not os.path.exists(objects_dir):
            # Fallback if CreateSIPStep hasn't run or failed
            objects_dir = sip_root
            
        for root, dirs, files in os.walk(objects_dir):
            for file in files:
                file_path = os.path.join(root, file)
                filename, ext = os.path.splitext(file)
                ext = ext.lower()
                
                # Images
                if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                    # Preservation: TIFF
                    preservation_path = os.path.join(root, f"{filename}_preservation.tif")
                    try:
                        cmd = [Paths.CONVERT_CMD, file_path, "-compress", "lzw", preservation_path]
                        subprocess.run(cmd, check=True, capture_output=True)
                        logger.info(f"Normalized {file} to TIFF")
                    except Exception as e:
                        logger.warning(f"Failed to normalize image {file}: {e}")

                # Video
                elif ext in ['.avi', '.mov', '.mp4', '.flv']:
                    # Preservation: MKV (FFV1)
                    preservation_path = os.path.join(root, f"{filename}_preservation.mkv")
                    try:
                        # ffmpeg -i input -c:v ffv1 -level 3 -g 1 -coder 1 -context 1 -c:a pcm_s24le output.mkv
                        cmd = [Paths.FFMPEG_CMD, "-i", file_path, "-c:v", "ffv1", "-level", "3", "-c:a", "pcm_s24le", preservation_path, "-y"]
                        subprocess.run(cmd, check=True, capture_output=True)
                        logger.info(f"Normalized {file} to MKV")
                    except Exception as e:
                         logger.warning(f"Failed to normalize video {file}: {e}")

class CreateSIPStep(Step):
    def execute(self):
        logger.info("Creating BagIt SIP structure...")
        
        sip_root = self.context['sip_path']
        sip_uuid = self.context.get('sip_uuid', 'no-uuid')
        
        # BagIt Structure:
        # <base>/
        #   data/
        #     objects/
        #     logs/
        #     thumbnails/
        #     METS.<uuid>.xml
        #     README.html
        #   bagit.txt
        #   bag-info.txt
        #   manifest-sha512.txt
        #   tagmanifest-md5.txt
        
        data_dir = os.path.join(sip_root, 'data')
        objects_dir = os.path.join(data_dir, 'objects')
        logs_dir = os.path.join(data_dir, 'logs')
        thumbnails_dir = os.path.join(data_dir, 'thumbnails')
        
        os.makedirs(objects_dir, exist_ok=True)
        os.makedirs(logs_dir, exist_ok=True)
        os.makedirs(thumbnails_dir, exist_ok=True)
        
        # Move existing content to data/objects
        # Be careful not to move the 'data' dir itself if we are running this multiple times or if it already exists
        items = os.listdir(sip_root)
        for item in items:
            if item == 'data':
                continue
            
            src = os.path.join(sip_root, item)
            dst = os.path.join(objects_dir, item)
            try:
                shutil.move(src, dst)
            except Exception as e:
                logger.warning(f"Could not move {item} to objects: {e}")

        # Move specific logs to data/logs if they exist in objects (moved from root)
        for log_file in ['structure_report.txt', 'fido.xml']:
            src = os.path.join(objects_dir, log_file)
            if os.path.exists(src):
                shutil.move(src, os.path.join(logs_dir, log_file))

        # Create dummy METS and README
        mets_filename = f"METS.{sip_uuid}.xml"
        with open(os.path.join(data_dir, mets_filename), 'w') as f:
            f.write(f"<mets>Dummy METS for {sip_uuid}</mets>")
            
        with open(os.path.join(data_dir, "README.html"), 'w') as f:
            f.write("<html><body><h1>Archivematica SIP</h1><p>This is a dummy README.</p></body></html>")

        # Create dummy thumbnail (optional but good for structure verification)
        with open(os.path.join(thumbnails_dir, "thumb_placeholder.txt"), 'w') as f:
            f.write("Placeholder for thumbnails")

        # Create bagit.txt
        with open(os.path.join(sip_root, "bagit.txt"), 'w') as f:
            f.write("BagIt-Version: 0.97\nTag-File-Character-Encoding: UTF-8\n")

        # Create bag-info.txt
        with open(os.path.join(sip_root, "bag-info.txt"), 'w') as f:
            f.write(f"Source-Organization: Archivematica Standalone\nPayload-Oxum: {self._calculate_oxum(data_dir)}\nBagging-Date: {datetime.date.today().isoformat()}\nExternal-Identifier: {sip_uuid}\n")

        # Create manifest-sha512.txt
        self._create_manifest(data_dir, os.path.join(sip_root, "manifest-sha512.txt"), "sha512")

        # Create tagmanifest-md5.txt (hashes of top-level files except tagmanifest itself)
        self._create_tagmanifest(sip_root, os.path.join(sip_root, "tagmanifest-md5.txt"), "md5")
        
        logger.info("BagIt SIP structure created.")

    def _calculate_oxum(self, data_dir):
        total_bytes = 0
        file_count = 0
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                total_bytes += os.path.getsize(os.path.join(root, file))
                file_count += 1
        return f"{total_bytes}.{file_count}"

    def _create_manifest(self, data_dir, manifest_path, algo):
        with open(manifest_path, 'w') as f:
            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Rel path from bag root (which is parent of data_dir)
                    # data_dir is <bag>/data
                    # file_path is <bag>/data/...
                    # rel_path should be data/...
                    
                    # We need path relative to sip_root. sip_root is parent of data_dir.
                    sip_root = os.path.dirname(data_dir)
                    rel_path = os.path.relpath(file_path, sip_root).replace('\\', '/')
                    
                    hash_val = self._hash_file(file_path, algo)
                    f.write(f"{hash_val}  {rel_path}\n")

    def _create_tagmanifest(self, sip_root, tagmanifest_path, algo):
        with open(tagmanifest_path, 'w') as f:
            for item in os.listdir(sip_root):
                if item == "tagmanifest-md5.txt" or item == "data":
                    continue
                file_path = os.path.join(sip_root, item)
                if os.path.isfile(file_path):
                    hash_val = self._hash_file(file_path, algo)
                    f.write(f"{hash_val}  {item}\n")

    def _hash_file(self, filepath, algo):
        h = hashlib.new(algo)
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

class ProcessContentStep(Step):
    def execute(self):
        logger.info("Examining content...")
        # Placeholder for bulk_extractor or similar
        # For now, just log that we are examining
        logger.info("Content examination complete (simulated).")
