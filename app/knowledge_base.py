from flask import Blueprint, render_template
from flask_login import login_required

knowledge_base_bp = Blueprint("knowledge_base", __name__, url_prefix="/knowledge-base")


@knowledge_base_bp.route("/")
@login_required
def index():
    # Define subspecialties and their resources - ONLY real, verified resources
    subspecialties = {
        "Neuroradiology": {
            "description": "Imaging of the brain, spine, head, and neck",
            "resources": [
                {"name": "Radiopaedia - Neuroradiology", "url": "https://radiopaedia.org/articles/neuroradiology", "description": "Comprehensive neuroradiology cases and articles"},
                {"name": "American Society of Neuroradiology", "url": "https://www.asnr.org/", "description": "Professional society with educational resources"},
                {"name": "HeadNeckBrainSpine", "url": "https://headneckbrainspine.com/", "description": "High-quality neuroradiology cases and teaching files"},
                {"name": "Radiology Assistant - Brain", "url": "https://radiologyassistant.nl/neuroradiology", "description": "Systematic approach to brain imaging"}
            ]
        },
        "Musculoskeletal Radiology": {
            "description": "Imaging of bones, joints, muscles, and soft tissues",
            "resources": [
                {"name": "Radiopaedia - MSK", "url": "https://radiopaedia.org/articles/musculoskeletal", "description": "MSK radiology cases and educational content"},
                {"name": "American College of Radiology MSK", "url": "https://www.acr.org/Clinical-Resources/ACR-Appropriateness-Criteria", "description": "ACR appropriateness criteria for MSK imaging"},
                {"name": "Radiology Assistant - MSK", "url": "https://radiologyassistant.nl/musculoskeletal", "description": "Systematic approach to musculoskeletal imaging"},
                {"name": "OrthoBullets", "url": "https://www.orthobullets.com/", "description": "Orthopedic knowledge base with imaging correlation"}
            ]
        },
        "Nuclear Medicine": {
            "description": "Molecular imaging and nuclear medicine procedures",
            "resources": [
                {"name": "Radiopaedia - Nuclear Medicine", "url": "https://radiopaedia.org/articles/nuclear-medicine", "description": "Nuclear medicine cases and articles"},
                {"name": "Society of Nuclear Medicine", "url": "https://www.snmmi.org/", "description": "Professional society with educational resources"},
                {"name": "Radiology Assistant - Nuclear Medicine", "url": "https://radiologyassistant.nl/nuclear-medicine", "description": "Educational content and cases"}
            ]
        },
        "Interventional Radiology": {
            "description": "Image-guided minimally invasive procedures",
            "resources": [
                {"name": "Radiopaedia - Interventional", "url": "https://radiopaedia.org/articles/interventional-radiology", "description": "IR cases and procedures"},
                {"name": "Society of Interventional Radiology", "url": "https://www.sirweb.org/", "description": "Professional society with educational resources"},
                {"name": "Cardiovascular and Interventional Radiological Society", "url": "https://www.cirse.org/", "description": "European IR society with resources"}
            ]
        },
        "Body Radiology": {
            "description": "Abdominal and pelvic imaging",
            "resources": [
                {"name": "Radiopaedia - Abdominal", "url": "https://radiopaedia.org/articles/abdominal", "description": "Abdominal radiology cases and articles"},
                {"name": "Radiology Assistant - Abdomen", "url": "https://radiologyassistant.nl/abdomen", "description": "Comprehensive abdominal imaging resources"},
                {"name": "American College of Radiology Abdomen", "url": "https://www.acr.org/Clinical-Resources/ACR-Appropriateness-Criteria", "description": "ACR appropriateness criteria for abdominal imaging"}
            ]
        },
        "General Radiology": {
            "description": "General radiology principles and common conditions",
            "resources": [
                {"name": "Radiopaedia", "url": "https://radiopaedia.org/", "description": "Comprehensive radiology encyclopedia and cases"},
                {"name": "Radiology Assistant", "url": "https://radiologyassistant.nl/", "description": "Educational content and systematic approach to imaging"},
                {"name": "American College of Radiology", "url": "https://www.acr.org/", "description": "Professional society with educational resources and appropriateness criteria"},
                {"name": "Radiographics", "url": "https://pubs.rsna.org/journal/radiographics", "description": "Educational journal with high-quality articles"}
            ]
        },
        "Chest Radiology": {
            "description": "Thoracic imaging including lungs, heart, and mediastinum",
            "resources": [
                {"name": "Radiopaedia - Chest", "url": "https://radiopaedia.org/articles/chest", "description": "Chest radiology cases and articles"},
                {"name": "Radiology Assistant - Chest", "url": "https://radiologyassistant.nl/chest", "description": "Systematic approach to chest imaging"},
                {"name": "Fleischner Society", "url": "https://fleischner.org/", "description": "Professional society with guidelines and educational content"}
            ]
        },
        "Breast Radiology": {
            "description": "Breast imaging and mammography",
            "resources": [
                {"name": "Radiopaedia - Breast", "url": "https://radiopaedia.org/articles/breast", "description": "Breast imaging cases and articles"},
                {"name": "American College of Radiology Breast", "url": "https://www.acr.org/Clinical-Resources/ACR-Appropriateness-Criteria", "description": "ACR appropriateness criteria for breast imaging"},
                {"name": "Society of Breast Imaging", "url": "https://www.sbi-online.org/", "description": "Professional society with educational resources"}
            ]
        },
        "Pediatric Radiology": {
            "description": "Imaging of children and adolescents",
            "resources": [
                {"name": "Radiopaedia - Pediatric", "url": "https://radiopaedia.org/articles/paediatric", "description": "Pediatric radiology cases and articles"},
                {"name": "Society for Pediatric Radiology", "url": "https://www.pedrad.org/", "description": "Professional society with educational resources"},
                {"name": "Radiology Assistant - Pediatric", "url": "https://radiologyassistant.nl/pediatrics", "description": "Pediatric imaging resources and cases"}
            ]
        },
        "Ultrasound": {
            "description": "Ultrasonography and sonographic imaging",
            "resources": [
                {"name": "Radiopaedia - Ultrasound", "url": "https://radiopaedia.org/articles/ultrasound", "description": "Ultrasound cases and educational content"},
                {"name": "American Institute of Ultrasound in Medicine", "url": "https://www.aium.org/", "description": "Professional society with guidelines and educational resources"},
                {"name": "Radiology Assistant - Ultrasound", "url": "https://radiologyassistant.nl/ultrasound", "description": "Systematic approach to ultrasound imaging"},
                {"name": "Ultrasound Cases", "url": "https://www.ultrasoundcases.info/", "description": "Comprehensive ultrasound case collection"}
            ]
        }
    }
    
    return render_template("knowledge_base/index.html", subspecialties=subspecialties)
