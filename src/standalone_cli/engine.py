import logging
import os
from .steps.ingest import (
    ScanVirusStep,
    AssignUUIDStep,
    StructureReportStep,
    IdentifyFormatStep,
    ExtractPackageStep
)
from .steps.process import (
    NormalizeStep,
    CreateSIPStep,
    ProcessContentStep
)
from .steps.store import (
    StoreAIPStep,
    StoreDIPStep
)

logger = logging.getLogger(__name__)

class WorkflowEngine:
    def __init__(self, transfer_path, aip_path, dip_path, config):
        self.context = {
            'sip_path': transfer_path,
            'aip_path': aip_path,
            'dip_path': dip_path,
            'config': config
        }
        self.config = config
        self.steps = []
        
        # Initialize steps based on configuration
        if self.config.SCAN_FOR_VIRUSES:
            self.steps.append(ScanVirusStep(self.context))
            
        if self.config.ASSIGN_UUIDS:
            self.steps.append(AssignUUIDStep(self.context))
            
        if self.config.GENERATE_STRUCTURE_REPORT:
            self.steps.append(StructureReportStep(self.context))
            
        if self.config.IDENTIFY_FORMAT_TRANSFER:
            self.steps.append(IdentifyFormatStep(self.context))
            
        if self.config.EXTRACT_PACKAGES:
            self.steps.append(ExtractPackageStep(self.context))
            
        if self.config.CREATE_SIP:
            self.steps.append(CreateSIPStep(self.context))
            
        if self.config.NORMALIZE:
            self.steps.append(NormalizeStep(self.context))
            
        if self.config.EXAMINE_CONTENTS:
            self.steps.append(ProcessContentStep(self.context))
            
        if self.config.STORE_AIP:
            self.steps.append(StoreAIPStep(self.context))
            
        if self.config.STORE_DIP:
            self.steps.append(StoreDIPStep(self.context))

    def run(self):
        logger.info("Starting Automated Workflow...")
        
        # Create a temporary processing directory
        # We'll use a 'processing' folder in the project root for visibility, or tempdir
        # Let's use a 'processing' folder in the current working directory as per plan
        import shutil
        import uuid
        
        processing_root = os.path.abspath("processing")
        os.makedirs(processing_root, exist_ok=True)
        
        # Create a unique subfolder for this run
        run_id = str(uuid.uuid4())
        processing_path = os.path.join(processing_root, run_id)
        
        logger.info(f"Creating processing environment at {processing_path}...")
        
        try:
            # Copy transfer content to processing path
            # We copy the *contents* of transfer_path into processing_path
            # If transfer_path is "C:/transfers/MyTransfer", we want "C:/processing/<uuid>/MyTransfer" 
            # or just the contents? 
            # Usually Archivematica preserves the top folder name if it's significant.
            # Let's copy the folder itself to be safe and preserve structure.
            
            transfer_dirname = os.path.basename(self.context['sip_path'].rstrip(os.sep))
            if not transfer_dirname:
                transfer_dirname = "transfer"
                
            working_sip_path = os.path.join(processing_path, transfer_dirname)
            
            shutil.copytree(self.context['sip_path'], working_sip_path)
            logger.info(f"Copied transfer to {working_sip_path}")
            
            # Update context to point to the working copy
            original_sip_path = self.context['sip_path']
            self.context['sip_path'] = working_sip_path
            
            # Execute steps
            for step in self.steps:
                try:
                    step.execute()
                except Exception as e:
                    logger.error(f"Step {step.__class__.__name__} failed: {e}")
                    raise
            
            logger.info("Workflow completed successfully.")
            
        finally:
            # Cleanup
            if os.path.exists(processing_path):
                logger.info(f"Cleaning up processing directory {processing_path}...")
                try:
                    shutil.rmtree(processing_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup processing directory: {e}")
