import os
import datetime
import hashlib
from lxml import etree

class METSGenerator:
    NS_METS = "http://www.loc.gov/METS/"
    NS_XLINK = "http://www.w3.org/1999/xlink"
    NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
    NS_PREMIS = "info:lc/xmlns/premis-v2"
    NS_DC = "http://purl.org/dc/elements/1.1/"
    
    NSMAP = {
        "mets": NS_METS,
        "xlink": NS_XLINK,
        "xsi": NS_XSI,
        "premis": NS_PREMIS,
        "dc": NS_DC
    }

    def __init__(self, sip_uuid, sip_path):
        self.sip_uuid = sip_uuid
        self.sip_path = sip_path
        self.root = etree.Element(f"{{{self.NS_METS}}}mets", nsmap=self.NSMAP)
        self.root.set("OBJID", f"uuid:{sip_uuid}")
        self.root.set("LABEL", f"AIP {sip_uuid}")
        self.root.set("PROFILE", "http://www.loc.gov/standards/mets/profiles/00000042.xml")
        
        self._create_header()
        self._create_dmd_sec()
        self._create_amd_sec()
        self.file_sec = etree.SubElement(self.root, f"{{{self.NS_METS}}}fileSec")
        self.struct_map = etree.SubElement(self.root, f"{{{self.NS_METS}}}structMap", TYPE="physical", LABEL="Archivematica Default")
        self.div_root = etree.SubElement(self.struct_map, f"{{{self.NS_METS}}}div", TYPE="Directory", LABEL=os.path.basename(sip_path))

    def _create_header(self):
        hdr = etree.SubElement(self.root, f"{{{self.NS_METS}}}metsHdr", CREATEDATE=datetime.datetime.now().isoformat())
        agent = etree.SubElement(hdr, f"{{{self.NS_METS}}}agent", ROLE="CREATOR", TYPE="ORGANIZATION")
        name = etree.SubElement(agent, f"{{{self.NS_METS}}}name")
        name.text = "Archivematica Standalone CLI"

    def _create_dmd_sec(self):
        # Descriptive Metadata Section (Placeholder for DC)
        dmd = etree.SubElement(self.root, f"{{{self.NS_METS}}}dmdSec", ID="dmdSec_1")
        md_wrap = etree.SubElement(dmd, f"{{{self.NS_METS}}}mdWrap", MDTYPE="DC")
        xml_data = etree.SubElement(md_wrap, f"{{{self.NS_METS}}}xmlData")
        title = etree.SubElement(xml_data, f"{{{self.NS_DC}}}title")
        title.text = f"AIP {self.sip_uuid}"
        identifier = etree.SubElement(xml_data, f"{{{self.NS_DC}}}identifier")
        identifier.text = self.sip_uuid

    def _create_amd_sec(self):
        # Administrative Metadata Section (Placeholder)
        amd = etree.SubElement(self.root, f"{{{self.NS_METS}}}amdSec", ID="amdSec_1")
        tech_md = etree.SubElement(amd, f"{{{self.NS_METS}}}techMD", ID="techMD_1")
        md_wrap = etree.SubElement(tech_md, f"{{{self.NS_METS}}}mdWrap", MDTYPE="PREMIS:OBJECT")
        xml_data = etree.SubElement(md_wrap, f"{{{self.NS_METS}}}xmlData")
        # Here we would normally put PREMIS object details
        # For now, just a placeholder to be valid XML
        obj = etree.SubElement(xml_data, f"{{{self.NS_PREMIS}}}object", type="file")
        
    def add_file_group(self, use, group_id, files):
        """
        files: list of (file_path, file_uuid) tuples. 
        file_path is absolute path on disk.
        """
        file_grp = etree.SubElement(self.file_sec, f"{{{self.NS_METS}}}fileGrp", USE=use)
        
        for file_path, file_uuid in files:
            if not os.path.exists(file_path):
                continue
                
            rel_path = os.path.relpath(file_path, self.sip_path).replace("\\", "/")
            file_size = os.path.getsize(file_path)
            
            # Calculate checksum (SHA-256 for METS usually, or whatever)
            # Let's use SHA-256
            checksum = self._calculate_checksum(file_path)
            
            file_el = etree.SubElement(file_grp, f"{{{self.NS_METS}}}file", 
                                       ID=f"file-{file_uuid}", 
                                       GROUPID=f"group-{file_uuid}",
                                       MIMETYPE="application/octet-stream", # Placeholder
                                       SIZE=str(file_size),
                                       CHECKSUM=checksum,
                                       CHECKSUMTYPE="SHA-256")
                                       
            flocat = etree.SubElement(file_el, f"{{{self.NS_METS}}}FLocat", 
                                      LOCTYPE="URL", 
                                      href=f"objects/{os.path.basename(rel_path)}") # Simplified href
            # Correct href should be relative to METS file. 
            # If METS is in data/, and file is in data/objects/, href is objects/file
            
            # Update StructMap
            # We need to find or create the directory div in structMap
            # For simplicity, we'll just add all files to the root div for now
            # In a real implementation, we'd mirror the directory structure
            
            fptr = etree.SubElement(self.div_root, f"{{{self.NS_METS}}}fptr", FILEID=f"file-{file_uuid}")

    def _calculate_checksum(self, filepath):
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def write(self, output_path):
        tree = etree.ElementTree(self.root)
        tree.write(output_path, pretty_print=True, xml_declaration=True, encoding="UTF-8")
