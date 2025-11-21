import os
import uuid
import subprocess
import logging
from . import Step
from ..config import Paths

logger = logging.getLogger(__name__)

class ScanVirusStep(Step):
    def execute(self):
        logger.info("Scanning for viruses...")
        try:
            # Recursive scan, suppress summary, only print infected files
            cmd = [Paths.CLAMSCAN_CMD, "-r", self.context['sip_path']]
            logger.info(f"Running: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info("Virus scan passed.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Virus scan failed or found viruses: {e.stderr}")
            # Clamscan returns 1 if viruses are found
            if e.returncode == 1:
                logger.warning("Viruses found! (Continuing for now, but should quarantine)")
            else:
                raise
        except FileNotFoundError:
            logger.warning("ClamAV not found. Skipping virus scan.")

class AssignUUIDStep(Step):
    def execute(self):
        logger.info("Assigning UUIDs to directories...")
        # In a real scenario, we might rename the top-level transfer directory
        # For now, we'll just generate a UUID for the SIP and store it in context
        sip_uuid = str(uuid.uuid4())
        self.context['sip_uuid'] = sip_uuid
        logger.info(f"Assigned SIP UUID: {sip_uuid}")
        
        # We could rename the directory here if required, but often we just tag it
        # new_path = os.path.join(os.path.dirname(self.context['sip_path']), sip_uuid)
        # os.rename(self.context['sip_path'], new_path)
        # self.context['sip_path'] = new_path

class StructureReportStep(Step):
    def execute(self):
        logger.info("Generating structure report...")
        report_path = os.path.join(self.context['sip_path'], 'structure_report.txt')
        try:
            cmd = [Paths.TREE_CMD, self.context['sip_path']]
            # Windows tree command is different (tree /F /A), but 'tree' usually works if GnuWin32 or similar
            # If using Windows built-in tree:
            if os.name == 'nt' and Paths.TREE_CMD == 'tree':
                 cmd = ['cmd', '/c', 'tree', '/F', '/A', self.context['sip_path']]
            
            with open(report_path, 'w') as f:
                subprocess.run(cmd, stdout=f, check=True)
            logger.info(f"Structure report generated at {report_path}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(f"Failed to generate structure report: {e}")

class IdentifyFormatStep(Step):
    def execute(self):
        logger.info("Identifying file formats...")
        try:
            # FIDO usage: fido -r <dir>
            cmd = [Paths.FIDO_CMD, "-r", self.context['sip_path']]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Save FIDO output to a file
            fido_log = os.path.join(self.context['sip_path'], 'fido.xml') # FIDO default is CSV-like, but let's just save stdout
            with open(fido_log, 'w') as f:
                f.write(result.stdout)
            logger.info("File formats identified.")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(f"Failed to identify formats (FIDO missing?): {e}")

class ExtractPackageStep(Step):
    def execute(self):
        logger.info("Extracting packages...")
        # Look for archives and extract them
        for root, dirs, files in os.walk(self.context['sip_path']):
            for file in files:
                if file.lower().endswith(('.zip', '.tar', '.gz', '.7z', '.rar')):
                    archive_path = os.path.join(root, file)
                    logger.info(f"Extracting {archive_path}...")
                    try:
                        # 7z x <archive> -o<outdir>
                        out_dir = os.path.join(root, os.path.splitext(file)[0])
                        cmd = [Paths.SEVEN_ZIP_CMD, "x", archive_path, f"-o{out_dir}", "-y"]
                        subprocess.run(cmd, check=True, capture_output=True)
                        
                        if self.context['config'].DELETE_PACKAGE_AFTER_EXTRACTION:
                            os.remove(archive_path)
                            logger.info(f"Deleted original archive: {file}")
                    except (subprocess.CalledProcessError, FileNotFoundError) as e:
                        logger.warning(f"Failed to extract {file}: {e}")
