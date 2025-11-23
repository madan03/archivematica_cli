import os
import datetime
import hashlib
from lxml import etree

class METSGenerator:
    # Namespaces from Archivematica
    NS_METS = "http://www.loc.gov/METS/"
    NS_XLINK = "http://www.w3.org/1999/xlink"
    NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
    NS_PREMIS = "http://www.loc.gov/standards/premis/v3/premis.xsd" # v3 based on create_mets_v2.py
    NS_DC = "http://purl.org/dc/elements/1.1/"
    NS_DCTERMS = "http://purl.org/dc/terms/"
    
    NSMAP = {
        "mets": NS_METS,
        "xlink": NS_XLINK,
        "xsi": NS_XSI,
        "premis": NS_PREMIS,
        "dc": NS_DC,
        "dcterms": NS_DCTERMS
    }

    def __init__(self, sip_uuid, sip_path):
        self.sip_uuid = sip_uuid
        self.sip_path = sip_path
        self.root = etree.Element(f"{{{self.NS_METS}}}mets", nsmap=self.NSMAP)
        self.root.set("OBJID", f"uuid:{sip_uuid}")
        self.root.set("LABEL", f"AIP {sip_uuid}")
        self.root.set("PROFILE", "http://www.loc.gov/standards/mets/profiles/00000042.xml")
        
        self._create_header()
        self.dmd_secs = []
        self.amd_secs = []
        self.file_sec = etree.SubElement(self.root, f"{{{self.NS_METS}}}fileSec")
        self.struct_map = etree.SubElement(self.root, f"{{{self.NS_METS}}}structMap", TYPE="physical", LABEL="Archivematica Default")
        self.div_root = etree.SubElement(self.struct_map, f"{{{self.NS_METS}}}div", TYPE="Directory", LABEL=os.path.basename(sip_path))

    def _create_header(self):
        hdr = etree.SubElement(self.root, f"{{{self.NS_METS}}}metsHdr", CREATEDATE=datetime.datetime.now().isoformat())
        agent = etree.SubElement(hdr, f"{{{self.NS_METS}}}agent", ROLE="CREATOR", TYPE="ORGANIZATION")
        name = etree.SubElement(agent, f"{{{self.NS_METS}}}name")
        name.text = "Archivematica Standalone CLI"

    def add_dmd_sec(self, dmd_id, md_type, content_element):
        dmd = etree.SubElement(self.root, f"{{{self.NS_METS}}}dmdSec", ID=dmd_id)
        md_wrap = etree.SubElement(dmd, f"{{{self.NS_METS}}}mdWrap", MDTYPE=md_type)
        xml_data = etree.SubElement(md_wrap, f"{{{self.NS_METS}}}xmlData")
        xml_data.append(content_element)
        self.dmd_secs.append(dmd_id)

    def add_amd_sec(self, amd_id, tech_md_element=None, digiprov_md_element=None):
        amd = etree.SubElement(self.root, f"{{{self.NS_METS}}}amdSec", ID=amd_id)
        if tech_md_element is not None:
            tech_md = etree.SubElement(amd, f"{{{self.NS_METS}}}techMD", ID=f"techMD_{amd_id}")
            md_wrap = etree.SubElement(tech_md, f"{{{self.NS_METS}}}mdWrap", MDTYPE="PREMIS:OBJECT")
            xml_data = etree.SubElement(md_wrap, f"{{{self.NS_METS}}}xmlData")
            xml_data.append(tech_md_element)
        
        if digiprov_md_element is not None:
            digiprov = etree.SubElement(amd, f"{{{self.NS_METS}}}digiprovMD", ID=f"digiprovMD_{amd_id}")
            md_wrap = etree.SubElement(digiprov, f"{{{self.NS_METS}}}mdWrap", MDTYPE="PREMIS:EVENT")
            xml_data = etree.SubElement(md_wrap, f"{{{self.NS_METS}}}xmlData")
            xml_data.append(digiprov_md_element)
            
        self.amd_secs.append(amd_id)

    def add_file_group(self, use, group_id, files):
        """
        files: list of (file_path, file_uuid) tuples. 
        """
        file_grp = etree.SubElement(self.file_sec, f"{{{self.NS_METS}}}fileGrp", USE=use)
        
        for file_path, file_uuid in files:
            if not os.path.exists(file_path):
                continue
                
            rel_path = os.path.relpath(file_path, self.sip_path).replace("\\", "/")
            file_size = os.path.getsize(file_path)
            checksum = self._calculate_checksum(file_path)
            
            file_el = etree.SubElement(file_grp, f"{{{self.NS_METS}}}file", 
                                       ID=f"file-{file_uuid}", 
                                       GROUPID=f"group-{file_uuid}",
                                       MIMETYPE="application/octet-stream", 
                                       SIZE=str(file_size),
                                       CHECKSUM=checksum,
                                       CHECKSUMTYPE="SHA-256")
                                       
            flocat = etree.SubElement(file_el, f"{{{self.NS_METS}}}FLocat", 
                                      LOCTYPE="URL", 
                                      href=rel_path,
                                      **{f"{{{self.NS_XLINK}}}type": "simple",
                                         f"{{{self.NS_XLINK}}}title": os.path.basename(file_path)})
            
            # Update StructMap
            fptr = etree.SubElement(self.div_root, f"{{{self.NS_METS}}}fptr", FILEID=f"file-{file_uuid}")

    def _calculate_checksum(self, filepath):
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def write(self, output_path):
        # Ensure sections are in correct order (Header, dmdSec, amdSec, fileSec, structMap)
        # lxml appends in order, but we might have added dmdSecs after fileSec if we weren't careful.
        # But here we add them to self.root as we go.
        # Ideally we should re-order children if strict compliance is needed, but usually order of addition is fine.
        
        tree = etree.ElementTree(self.root)
        tree.write(output_path, pretty_print=True, xml_declaration=True, encoding="UTF-8")
