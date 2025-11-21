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

        # Move specific logs to data/logs
        for log_file in ['structure_report.txt', 'fido.xml']:
            src = os.path.join(objects_dir, log_file)
            if os.path.exists(src):
                shutil.move(src, os.path.join(logs_dir, log_file))

        # --- Generate METS ---
        from ..utils.mets import METSGenerator
        mets_gen = METSGenerator(sip_uuid, data_dir)
        
        # Add objects to METS
        object_files = []
        for root, dirs, files in os.walk(objects_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Generate a file UUID or ID
                file_id = hashlib.md5(file_path.encode()).hexdigest() # Simple ID
                object_files.append((file_path, file_id))
        
        mets_gen.add_file_group("original", "group-original", object_files)
        
        mets_filename = f"METS.{sip_uuid}.xml"
        mets_path = os.path.join(data_dir, mets_filename)
        mets_gen.write(mets_path)
        logger.info(f"Generated METS file: {mets_path}")

        # --- Generate README.html ---
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'README.html')
        readme_path = os.path.join(data_dir, "README.html")
        
        try:
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            # Simple string replacement instead of jinja2 to avoid extra dependency if not needed, 
            # but user added lxml so maybe they are okay with deps. 
            # Let's stick to simple replacement for now as requirements.txt didn't strictly have jinja2
            content = template_content.replace('{{ sip_uuid }}', sip_uuid)
            content = content.replace('{{ date_generated }}', datetime.datetime.now().isoformat())
            
            with open(readme_path, 'w') as f:
                f.write(content)
            logger.info(f"Generated README.html: {readme_path}")
        except Exception as e:
            logger.error(f"Failed to generate README.html: {e}")
            # Fallback
            with open(readme_path, 'w') as f:
                f.write(f"<html><body><h1>AIP {sip_uuid}</h1></body></html>")

        # Create dummy thumbnail
        with open(os.path.join(thumbnails_dir, "thumb_placeholder.txt"), 'w') as f:
            f.write("Placeholder for thumbnails")

        # --- BagIt Files ---
        
        # bagit.txt
        with open(os.path.join(sip_root, "bagit.txt"), 'w') as f:
            f.write("BagIt-Version: 0.97\nTag-File-Character-Encoding: UTF-8\n")

        # bag-info.txt - Standard Archivematica Fields
        oxum = self._calculate_oxum(data_dir)
        bag_size = self._calculate_bag_size(data_dir)
        with open(os.path.join(sip_root, "bag-info.txt"), 'w') as f:
            f.write(f"Source-Organization: Archivematica Standalone\n")
            f.write(f"Organization-Address: 123 Archive Way\n")
            f.write(f"Contact-Name: Admin\n")
            f.write(f"External-Description: AIP generated by Standalone CLI\n")
            f.write(f"Bagging-Date: {datetime.date.today().isoformat()}\n")
            f.write(f"External-Identifier: {sip_uuid}\n")
            f.write(f"Payload-Oxum: {oxum}\n")
            f.write(f"Bag-Size: {bag_size}\n")
            f.write(f"Bag-Group-Identifier: {sip_uuid}\n") # Often same as UUID or Transfer name

        # manifest-sha512.txt
        self._create_manifest(data_dir, os.path.join(sip_root, "manifest-sha512.txt"), "sha512")

        # tagmanifest-md5.txt
        self._create_tagmanifest(sip_root, os.path.join(sip_root, "tagmanifest-md5.txt"), "md5")
        
        logger.info("BagIt SIP structure created.")

    def _calculate_bag_size(self, data_dir):
        total_bytes = 0
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                total_bytes += os.path.getsize(os.path.join(root, file))
        
        # Convert to human readable
        for unit in ['B', 'KB', 'MB', 'GB']:
            if total_bytes < 1024:
                return f"{total_bytes:.2f} {unit}"
            total_bytes /= 1024
        return f"{total_bytes:.2f} TB"

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
