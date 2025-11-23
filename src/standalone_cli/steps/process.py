import logging
import os
import subprocess
import shutil
import hashlib
import csv
import datetime
from . import Step
from ..config import Paths

logger = logging.getLogger(__name__)



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
        content_dir = os.path.join(data_dir, 'content')
        objects_dir = os.path.join(content_dir, 'objects')
        metadata_dir = os.path.join(content_dir, 'metadata')
        logs_dir = os.path.join(content_dir, 'logs')
        thumbnails_dir = os.path.join(data_dir, 'thumbnails')
        manifests_dir = os.path.join(data_dir, 'manifests')
        
        os.makedirs(objects_dir, exist_ok=True)
        os.makedirs(metadata_dir, exist_ok=True)
        os.makedirs(logs_dir, exist_ok=True)
        os.makedirs(thumbnails_dir, exist_ok=True)
        os.makedirs(manifests_dir, exist_ok=True)
        
        # Subdirectories in metadata
        os.makedirs(os.path.join(metadata_dir, 'submissionDocumentation'), exist_ok=True)

        # Move existing content to data/content/objects
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

        # Move specific logs to data/content/logs
        for log_file in ['structure_report.txt', 'fido.xml', 'virus_scan.log']:
            src = os.path.join(objects_dir, log_file)
            if os.path.exists(src):
                shutil.move(src, os.path.join(logs_dir, log_file))

        # --- Generate Metadata Files ---
        
        # 1. metadata.csv
        metadata_csv_path = os.path.join(metadata_dir, 'metadata.csv')
        with open(metadata_csv_path, 'w', newline='') as csvfile:
            fieldnames = ['filename', 'dc.title', 'dc.creator', 'dc.description', 'dc.date', 'dc.format', 'dc.identifier']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Add entries for objects
            for root, dirs, files in os.walk(objects_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, content_dir).replace('\\', '/')
                    # content_dir is data/content, objects are in data/content/objects
                    # so rel_path starts with objects/
                    
                    writer.writerow({
                        'filename': rel_path,
                        'dc.title': file,
                        'dc.creator': 'Unknown',
                        'dc.description': f'Imported file {file}',
                        'dc.date': datetime.date.today().isoformat(),
                        'dc.format': os.path.splitext(file)[1][1:].upper(),
                        'dc.identifier': hashlib.md5(file_path.encode()).hexdigest()
                    })

        # 2. dublin_core.xml
        dc_path = os.path.join(metadata_dir, 'dublin_core.xml')
        with open(dc_path, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<dublin_core xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://purl.org/dc/terms/ https://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd">\n')
            f.write(f'  <dc:title>AIP {sip_uuid}</dc:title>\n')
            f.write(f'  <dc:identifier>{sip_uuid}</dc:identifier>\n')
            f.write(f'  <dc:date>{datetime.date.today().isoformat()}</dc:date>\n')
            f.write('</dublin_core>')
            
        # 3. premis.xml (Detailed)
        premis_path = os.path.join(metadata_dir, 'premis.xml')
        with open(premis_path, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<premis:premis xmlns:premis="http://www.loc.gov/standards/premis/v3/premis.xsd" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/standards/premis/v3/premis.xsd http://www.loc.gov/standards/premis/v3/premis.xsd" version="3.0">\n')
            
            # Object: The AIP itself (Intellectual Entity)
            f.write('  <premis:object xsi:type="premis:intellectualEntity">\n')
            f.write('    <premis:objectIdentifier>\n')
            f.write('      <premis:objectIdentifierType>UUID</premis:objectIdentifierType>\n')
            f.write(f'      <premis:objectIdentifierValue>{sip_uuid}</premis:objectIdentifierValue>\n')
            f.write('    </premis:objectIdentifier>\n')
            f.write('    <premis:originalName>AIP</premis:originalName>\n')
            f.write('  </premis:object>\n')
            
            # Event: Ingest
            f.write('  <premis:event>\n')
            f.write('    <premis:eventIdentifier>\n')
            f.write('      <premis:eventIdentifierType>UUID</premis:eventIdentifierType>\n')
            f.write(f'      <premis:eventIdentifierValue>{hashlib.md5(b"ingest").hexdigest()}</premis:eventIdentifierValue>\n')
            f.write('    </premis:eventIdentifier>\n')
            f.write('    <premis:eventType>ingestion</premis:eventType>\n')
            f.write(f'    <premis:eventDateTime>{datetime.datetime.now().isoformat()}</premis:eventDateTime>\n')
            f.write('    <premis:eventDetailInformation>\n')
            f.write('      <premis:eventDetail>Ingested by Archivematica Standalone CLI</premis:eventDetail>\n')
            f.write('    </premis:eventDetailInformation>\n')
            f.write('    <premis:linkingObjectIdentifier>\n')
            f.write('      <premis:linkingObjectIdentifierType>UUID</premis:linkingObjectIdentifierType>\n')
            f.write(f'      <premis:linkingObjectIdentifierValue>{sip_uuid}</premis:linkingObjectIdentifierValue>\n')
            f.write('    </premis:linkingObjectIdentifier>\n')
            f.write('  </premis:event>\n')
            
            # Agent: The CLI
            f.write('  <premis:agent>\n')
            f.write('    <premis:agentIdentifier>\n')
            f.write('      <premis:agentIdentifierType>preservation system</premis:agentIdentifierType>\n')
            f.write('      <premis:agentIdentifierValue>Archivematica Standalone CLI</premis:agentIdentifierValue>\n')
            f.write('    </premis:agentIdentifier>\n')
            f.write('    <premis:agentName>Archivematica Standalone CLI</premis:agentName>\n')
            f.write('    <premis:agentType>software</premis:agentType>\n')
            f.write('  </premis:agent>\n')
            
            f.write('</premis:premis>')

        # 4. mods.xml (User requested "mode", likely MODS)
        mods_path = os.path.join(metadata_dir, 'mods.xml')
        with open(mods_path, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<mods:mods xmlns:mods="http://www.loc.gov/mods/v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/mods/v3 http://www.loc.gov/standards/mods/v3/mods.xsd">\n')
            f.write('  <mods:titleInfo>\n')
            f.write(f'    <mods:title>AIP {sip_uuid}</mods:title>\n')
            f.write('  </mods:titleInfo>\n')
            f.write('  <mods:typeOfResource>collection</mods:typeOfResource>\n')
            f.write('  <mods:originInfo>\n')
            f.write(f'    <mods:dateCreated>{datetime.date.today().isoformat()}</mods:dateCreated>\n')
            f.write('  </mods:originInfo>\n')
            f.write('</mods:mods>')
            
        # 5. submissionDocumentation
        # Create dummy processingMCP.xml and rights.csv as per workflow.txt
        sub_doc_dir = os.path.join(metadata_dir, 'submissionDocumentation')
        with open(os.path.join(sub_doc_dir, 'processingMCP.xml'), 'w') as f:
             f.write('<processingMCP>\n  <preconfigs />\n</processingMCP>')
        with open(os.path.join(sub_doc_dir, 'rights.csv'), 'w') as f:
             f.write('file,basis,status,country,jurisdiction,start_date,end_date,note\n')

        # --- Generate README.html ---
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'README.html')
        readme_path = os.path.join(data_dir, "README.html")
        
        try:
            if os.path.exists(template_path):
                shutil.copy2(template_path, readme_path)
                logger.info(f"Generated README.html: {readme_path}")
            else:
                logger.warning(f"README.html template not found at {template_path}")
                with open(readme_path, 'w') as f:
                    f.write(f"<html><body><h1>AIP {sip_uuid}</h1></body></html>")
        except Exception as e:
            logger.error(f"Failed to generate README.html: {e}")

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

        # manifest-sha256.txt
        self._create_manifest(data_dir, os.path.join(sip_root, "manifest-sha256.txt"), "sha256")

        # tagmanifest-sha256.txt
        self._create_tagmanifest(sip_root, os.path.join(sip_root, "tagmanifest-sha256.txt"), "sha256")
        
        # manifests/manifest.json
        self._create_manifest_json(data_dir, os.path.join(manifests_dir, "manifests.json"))
        
        # manifests/checksums.sha256 (Copy of manifest-sha256.txt)
        shutil.copy2(os.path.join(sip_root, "manifest-sha256.txt"), os.path.join(manifests_dir, "checksums.sha256"))
        
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
                if item == "tagmanifest-sha256.txt" or item == "data":
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

    def _create_manifest_json(self, data_dir, manifest_path):
        import json
        manifest_data = []
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                 file_path = os.path.join(root, file)
                 sip_root = os.path.dirname(data_dir)
                 rel_path = os.path.relpath(file_path, sip_root).replace('\\', '/')
                 
                 manifest_data.append({
                     "file": rel_path,
                     "size": os.path.getsize(file_path),
                     "sha256": self._hash_file(file_path, "sha256")
                 })
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=4)

class NormalizeStep(Step):
    def execute(self):
        logger.info("Normalizing content for preservation and access...")
        
        sip_root = self.context['sip_path']
        objects_dir = os.path.join(sip_root, 'data', 'content', 'objects')
        thumbnails_dir = os.path.join(sip_root, 'data', 'thumbnails')
        
        if not os.path.exists(objects_dir):
            objects_dir = sip_root
            
        for root, dirs, files in os.walk(objects_dir):
            for file in files:
                file_path = os.path.join(root, file)
                filename, ext = os.path.splitext(file)
                ext = ext.lower()
                
                # Images
                if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tif', '.tiff']:
                    # Preservation: TIFF (if not already)
                    if ext not in ['.tif', '.tiff']:
                        preservation_path = os.path.join(root, f"{filename}_preservation.tif")
                        try:
                            cmd = [Paths.CONVERT_CMD, file_path, "-compress", "lzw", preservation_path]
                            subprocess.run(cmd, check=True, capture_output=True)
                            logger.info(f"Normalized {file} to TIFF")
                        except Exception as e:
                            logger.warning(f"Failed to normalize image {file}: {e}")

                    # Thumbnails
                    thumb_path = os.path.join(thumbnails_dir, f"{filename}.png")
                    try:
                        # convert input -resize 200x200 thumb.png
                        cmd = [Paths.CONVERT_CMD, file_path, "-resize", "200x200", thumb_path]
                        subprocess.run(cmd, check=True, capture_output=True)
                        logger.info(f"Generated thumbnail for {file}")
                    except Exception as e:
                        logger.warning(f"Failed to generate thumbnail for {file}: {e}")

                # Video
                elif ext in ['.avi', '.mov', '.mp4', '.flv']:
                    # Preservation: MKV (FFV1)
                    preservation_path = os.path.join(root, f"{filename}_preservation.mkv")
                    try:
                        cmd = [Paths.FFMPEG_CMD, "-i", file_path, "-c:v", "ffv1", "-level", "3", "-c:a", "pcm_s24le", preservation_path, "-y"]
                        subprocess.run(cmd, check=True, capture_output=True)
                        logger.info(f"Normalized {file} to MKV")
                    except Exception as e:
                         logger.warning(f"Failed to normalize video {file}: {e}")

class ProcessContentStep(Step):
    def execute(self):
        logger.info("Examining content...")
        # Placeholder for bulk_extractor or similar
        # For now, just log that we are examining
        logger.info("Content examination complete (simulated).")
