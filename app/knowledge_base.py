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
                {"name": "Radiopaedia - Neuroradiology Sections", "url": "https://radiopaedia.org/sections/neuroradiology", "description": "Organized neuroradiology sections and subspecialties"},
                {"name": "Learn Neuroradiology", "url": "https://learnneuroradiology.com/", "description": "Comprehensive neuroradiology learning platform"},
                {"name": "Radiology Assistant - Neuroradiology", "url": "https://www.radiologyassistant.nl/neuroradiology", "description": "Systematic approach to neuroradiology imaging"},
                {"name": "American Society of Neuroradiology", "url": "https://www.asnr.org/", "description": "Professional society with educational resources"},
                {"name": "ASNR Core Education", "url": "https://www.asnr.org/education/neuroradiology-core-education/", "description": "ASNR's core neuroradiology education curriculum"},
                {"name": "Radiographics Journal", "url": "https://pubs.rsna.org/journal/radiographics", "description": "RSNA's educational journal with neuroradiology content"},
                {"name": "CTisus Learning", "url": "https://www.ctisus.com/learning", "description": "CT imaging education and cases"},
                {"name": "Medality Noon Conference", "url": "https://www.medality.com/noon-conference", "description": "Educational conference series and cases"},
                {"name": "HeadNeckBrainSpine", "url": "https://headneckbrainspine.com/", "description": "High-quality neuroradiology cases and teaching files"}
            ]
        },
        "Musculoskeletal Radiology": {
            "description": "Imaging of bones, joints, muscles, and soft tissues",
            "resources": [
                {"name": "Radiopaedia - MSK", "url": "https://radiopaedia.org/articles/musculoskeletal", "description": "MSK radiology cases and educational content"},
                {"name": "Radiopaedia - MSK Sections", "url": "https://radiopaedia.org/sections/musculoskeletal", "description": "Organized musculoskeletal radiology sections and subspecialties"},
                {"name": "UW MSK Radiology Book", "url": "https://rad.washington.edu/about-us/academic-sections/musculoskeletal-radiology/teaching-materials/online-musculoskeletal-radiology-book/", "description": "University of Washington's comprehensive online MSK radiology textbook"},
                {"name": "Radiology Assistant - MSK", "url": "https://radiologyassistant.nl/musculoskeletal", "description": "Systematic approach to musculoskeletal imaging"},
                {"name": "Skeletal Radiology Society", "url": "https://skeletalrad.org/web-resources", "description": "Skeletal Radiology Society web resources and educational materials"},
                {"name": "Radiographics Journal", "url": "https://pubs.rsna.org/journal/radiographics", "description": "RSNA's educational journal with musculoskeletal radiology content"},
                {"name": "CTisus MSK Learning", "url": "https://www.ctisus.com/learning?subspecialty_id=7", "description": "CT imaging education focused on musculoskeletal radiology"},
                {"name": "Medality MSK Library", "url": "https://www.medality.com/library/musculoskeletal/", "description": "Comprehensive musculoskeletal radiology case library"},
                {"name": "Radiology Core Lectures MSK", "url": "https://radiologycorelectures.org/msk/", "description": "Core lecture series for musculoskeletal radiology"},
                {"name": "Image Interpretation MSK", "url": "https://www.imageinterpretation.co.uk/musculoskeletal-index.php", "description": "UK-based musculoskeletal radiology educational resources"},
                {"name": "MSK Radiology", "url": "https://www.msk-radiology.com/", "description": "Dedicated musculoskeletal radiology educational platform"},
                {"name": "UW Radiology Education", "url": "https://radiology.wisc.edu/education/online-", "description": "University of Wisconsin online radiology education resources"},
                {"name": "American College of Radiology MSK", "url": "https://www.acr.org/Clinical-Resources/ACR-Appropriateness-Criteria", "description": "ACR appropriateness criteria for MSK imaging"},
                {"name": "OrthoBullets", "url": "https://www.orthobullets.com/", "description": "Orthopedic knowledge base with imaging correlation"}
            ]
        },
        "Nuclear Medicine": {
            "description": "Molecular imaging and nuclear medicine procedures",
            "resources": [
                {"name": "Radiopaedia - Nuclear Medicine", "url": "https://radiopaedia.org/articles/nuclear-medicine", "description": "Nuclear medicine cases and articles"},
                {"name": "Radiopaedia - Nuclear Medicine Sections", "url": "https://radiopaedia.org/sections/nuclear-medicine", "description": "Organized nuclear medicine sections and subspecialties"},
                {"name": "IAEA Nuclear Medicine E-Learning", "url": "https://www.iaea.org/resources/hhc/nuclear-medicine/e-learning-courses/datol", "description": "International Atomic Energy Agency nuclear medicine e-learning courses"},
                {"name": "Society of Nuclear Medicine", "url": "https://www.snmmi.org/", "description": "Professional society with educational resources"},
                {"name": "SNMMI Clinical Practice", "url": "https://www.snmmi.org/ClinicalPractice/content.aspx?ItemNumber=6414", "description": "SNMMI clinical practice guidelines and resources"},
                {"name": "Radiology Core Lectures Nuclear Medicine", "url": "https://radiologyresidentcorelectures.com/nuclear-medicine-courses/", "description": "Core lecture series for nuclear medicine radiology residents"},
                {"name": "EANM Guidelines", "url": "https://www.eanm.org/publications/guidelines/", "description": "European Association of Nuclear Medicine clinical guidelines"},
                {"name": "Curium Pharma Resources", "url": "https://www.curiumpharma.com/resources/", "description": "Educational resources and materials from Curium Pharma"},
                {"name": "Radiology Education Nuclear Medicine", "url": "https://www.radiologyeducation.com/nuclear-", "description": "Nuclear medicine educational resources and courses"},
                {"name": "Radiology Assistant - Nuclear Medicine", "url": "https://radiologyassistant.nl/nuclear-medicine", "description": "Educational content and cases"}
            ]
        },
        "Interventional Radiology": {
            "description": "Image-guided minimally invasive procedures",
            "resources": [
                {"name": "Radiopaedia - Interventional", "url": "https://radiopaedia.org/articles/interventional-radiology", "description": "IR cases and procedures"},
                {"name": "Radiopaedia - Interventional Sections", "url": "https://radiopaedia.org/sections/interventional", "description": "Organized interventional radiology sections and subspecialties"},
                {"name": "Society of Interventional Radiology", "url": "https://www.sirweb.org/", "description": "Professional society with educational resources"},
                {"name": "SIR Learning Center", "url": "https://www.sirweb.org/learning-center/rfs-landing-page/free-content/", "description": "SIR's free educational content and learning resources"},
                {"name": "Radiology Assistant - Interventional", "url": "https://www.radiologyassistant.nl/interventional", "description": "Systematic approach to interventional radiology procedures"},
                {"name": "CTisus IR Learning", "url": "https://www.ctisus.com/learning?subspecialty_id=8", "description": "CT imaging education focused on interventional radiology"},
                {"name": "Medality IR Library", "url": "https://www.medality.com/library/interventional/", "description": "Comprehensive interventional radiology case library"},
                {"name": "Radiology Core Lectures IR", "url": "https://radiologycorelectures.org/ir/", "description": "Core lecture series for interventional radiology"},
                {"name": "VIR Radiology Education", "url": "https://www.vir-radiology.com/education/free-educational-resources/", "description": "Free educational resources for vascular and interventional radiology"},
                {"name": "Cardiovascular and Interventional Radiological Society", "url": "https://www.cirse.org/", "description": "European IR society with resources"}
            ]
        },
        "Body Radiology": {
            "description": "Abdominal and pelvic imaging",
            "resources": [
                {"name": "Radiopaedia - Abdominal", "url": "https://radiopaedia.org/articles/abdominal", "description": "Abdominal radiology cases and articles"},
                {"name": "Radiopaedia - Abdomen and Pelvis Sections", "url": "https://radiopaedia.org/sections/abdomen-and-pelvis", "description": "Organized abdomen and pelvis radiology sections and subspecialties"},
                {"name": "Radiology Assistant - Abdomen", "url": "https://radiologyassistant.nl/abdomen", "description": "Comprehensive abdominal imaging resources"},
                {"name": "Radiographics Journal", "url": "https://pubs.rsna.org/journal/radiographics", "description": "RSNA's educational journal with body radiology content"},
                {"name": "CTisus Body Learning", "url": "https://www.ctisus.com/learning?subspecialty_id=2", "description": "CT imaging education focused on body radiology"},
                {"name": "Medality Abdomen Library", "url": "https://www.medality.com/library/abdomen", "description": "Comprehensive abdomen radiology case library"},
                {"name": "Radiology Core Lectures Body", "url": "https://radiologycorelectures.org/body/", "description": "Core lecture series for body radiology"},
                {"name": "UW Body Imaging Book", "url": "https://rad.washington.edu/about-us/academic-sections/body-imaging/teaching-materials/online-body-imaging-book/", "description": "University of Washington's comprehensive online body imaging textbook"},
                {"name": "Image Interpretation Abdomen", "url": "https://www.imageinterpretation.co.uk/abdomen-index.php", "description": "UK-based abdomen radiology educational resources"},
                {"name": "American College of Radiology Abdomen", "url": "https://www.acr.org/Clinical-Resources/ACR-Appropriateness-Criteria", "description": "ACR appropriateness criteria for abdominal imaging"}
            ]
        },
        "General Radiology": {
            "description": "General radiology principles and common conditions",
            "resources": [
                {"name": "Radiopaedia", "url": "https://radiopaedia.org/", "description": "Comprehensive radiology encyclopedia and cases"},
                {"name": "Radiopaedia - Radiology Sections", "url": "https://radiopaedia.org/sections/radiology", "description": "Organized radiology sections and subspecialties"},
                {"name": "Radiology Assistant", "url": "https://radiologyassistant.nl/", "description": "Educational content and systematic approach to imaging"},
                {"name": "Radiographics", "url": "https://pubs.rsna.org/journal/radiographics", "description": "Educational journal with high-quality articles"},
                {"name": "CTisus Learning", "url": "https://www.ctisus.com/learning", "description": "CT imaging education and cases"},
                {"name": "Medality Library", "url": "https://www.medality.com/library/", "description": "Comprehensive radiology case library and educational resources"},
                {"name": "Radiology Core Lectures", "url": "https://radiologycorelectures.org/", "description": "Core lecture series for radiology residents"},
                {"name": "Image Interpretation", "url": "https://www.imageinterpretation.co.uk/", "description": "UK-based radiology educational resources and cases"},
                {"name": "AuntMinnie Education Center", "url": "https://www.auntminnie.com/education-center", "description": "Educational resources and cases from AuntMinnie"},
                {"name": "Learning Radiology", "url": "https://learningradiology.com/", "description": "Comprehensive radiology learning platform"},
                {"name": "American College of Radiology", "url": "https://www.acr.org/", "description": "Professional society with educational resources and appropriateness criteria"}
            ]
        },
        "Chest Radiology": {
            "description": "Thoracic imaging including lungs, heart, and mediastinum",
            "resources": [
                {"name": "Radiopaedia - Chest", "url": "https://radiopaedia.org/articles/chest", "description": "Chest radiology cases and articles"},
                {"name": "Radiopaedia - Chest Sections", "url": "https://radiopaedia.org/sections/chest", "description": "Organized chest radiology sections and subspecialties"},
                {"name": "Radiology Assistant - Chest", "url": "https://radiologyassistant.nl/chest", "description": "Systematic approach to chest imaging"},
                {"name": "Radiographics Journal", "url": "https://pubs.rsna.org/journal/radiographics", "description": "RSNA's educational journal with chest radiology content"},
                {"name": "CTisus Chest Learning", "url": "https://www.ctisus.com/learning?subspecialty_id=3", "description": "CT imaging education focused on chest radiology"},
                {"name": "Medality Chest Library", "url": "https://www.medality.com/library/chest/", "description": "Comprehensive chest radiology case library"},
                {"name": "Radiology Core Lectures Chest", "url": "https://radiologycorelectures.org/chest/", "description": "Core lecture series for chest radiology"},
                {"name": "Thoracic Radiology Society", "url": "https://www.thoracicrad.org/?page_id=171", "description": "Thoracic Radiology Society educational resources and guidelines"},
                {"name": "Image Interpretation Chest", "url": "https://www.imageinterpretation.co.uk/chest-index.php", "description": "UK-based chest radiology educational resources"},
                {"name": "Fleischner Society", "url": "https://fleischner.org/", "description": "Professional society with guidelines and educational content"}
            ]
        },
        "Breast Radiology": {
            "description": "Breast imaging and mammography",
            "resources": [
                {"name": "Radiopaedia - Breast", "url": "https://radiopaedia.org/articles/breast", "description": "Breast imaging cases and articles"},
                {"name": "Radiopaedia - Breast Sections", "url": "https://radiopaedia.org/sections/breast", "description": "Organized breast radiology sections and subspecialties"},
                {"name": "Radiology Assistant - Breast", "url": "https://www.radiologyassistant.nl/breast", "description": "Systematic approach to breast imaging"},
                {"name": "Radiographics Journal", "url": "https://pubs.rsna.org/journal/radiographics", "description": "RSNA's educational journal with breast radiology content"},
                {"name": "CTisus Breast Learning", "url": "https://www.ctisus.com/learning?subspecialty_id=4", "description": "CT imaging education focused on breast radiology"},
                {"name": "Medality Breast Library", "url": "https://www.medality.com/library/breast/", "description": "Comprehensive breast radiology case library"},
                {"name": "Radiology Core Lectures Breast", "url": "https://radiologycorelectures.org/breast/", "description": "Core lecture series for breast radiology"},
                {"name": "SBI Free Educational Resources", "url": "https://www.sbi-online.org/education/free-educational-resources", "description": "Society of Breast Imaging free educational resources and materials"},
                {"name": "American College of Radiology Breast", "url": "https://www.acr.org/Clinical-Resources/ACR-Appropriateness-Criteria", "description": "ACR appropriateness criteria for breast imaging"},
                {"name": "Society of Breast Imaging", "url": "https://www.sbi-online.org/", "description": "Professional society with educational resources"}
            ]
        },
        "Pediatric Radiology": {
            "description": "Imaging of children and adolescents",
            "resources": [
                {"name": "Radiopaedia - Pediatric", "url": "https://radiopaedia.org/articles/paediatric", "description": "Pediatric radiology cases and articles"},
                {"name": "Radiopaedia - Pediatric Sections", "url": "https://radiopaedia.org/sections/paediatric", "description": "Organized pediatric radiology sections and subspecialties"},
                {"name": "Radiology Assistant - Pediatric", "url": "https://radiologyassistant.nl/pediatrics", "description": "Pediatric imaging resources and cases"},
                {"name": "Radiographics Journal", "url": "https://pubs.rsna.org/journal/radiographics", "description": "RSNA's educational journal with pediatric radiology content"},
                {"name": "CTisus Pediatric Learning", "url": "https://www.ctisus.com/learning?subspecialty_id=5", "description": "CT imaging education focused on pediatric radiology"},
                {"name": "Medality Pediatric Library", "url": "https://www.medality.com/library/pediatric/", "description": "Comprehensive pediatric radiology case library"},
                {"name": "Radiology Core Lectures Pediatric", "url": "https://radiologycorelectures.org/pediatric/", "description": "Core lecture series for pediatric radiology"},
                {"name": "Society for Pediatric Radiology", "url": "https://www.pedrad.org/", "description": "Professional society with educational resources"},
                {"name": "SPR Online Education", "url": "https://www.pedrad.org/Resources/SPR-Online-Education", "description": "Society for Pediatric Radiology online education resources"},
                {"name": "Image Gently Resources", "url": "https://www.imagegently.org/Resources", "description": "Image Gently Alliance resources for safe pediatric imaging"}
            ]
        },
    "Ultrasound": {
        "description": "Ultrasonography and sonographic imaging",
        "resources": [
            {"name": "Radiopaedia - Ultrasound", "url": "https://radiopaedia.org/articles/ultrasound", "description": "Ultrasound cases and educational content"},
            {"name": "Radiopaedia - Ultrasound Sections", "url": "https://radiopaedia.org/sections/ultrasound", "description": "Organized ultrasound sections and subspecialties"},
            {"name": "Radiology Assistant - Ultrasound", "url": "https://radiologyassistant.nl/ultrasound", "description": "Systematic approach to ultrasound imaging"},
            {"name": "Radiographics Journal", "url": "https://pubs.rsna.org/journal/radiographics", "description": "RSNA's educational journal with ultrasound content"},
            {"name": "CTisus Ultrasound Learning", "url": "https://www.ctisus.com/learning?subspecialty_id=6", "description": "CT imaging education focused on ultrasound"},
            {"name": "Medality Ultrasound Library", "url": "https://www.medality.com/library/ultrasound/", "description": "Comprehensive ultrasound case library"},
            {"name": "Radiology Core Lectures Ultrasound", "url": "https://radiologycorelectures.org/ultrasound/", "description": "Core lecture series for ultrasound"},
            {"name": "AIUM Resources", "url": "https://www.aium.org/resources/", "description": "American Institute of Ultrasound in Medicine resources"},
            {"name": "American Institute of Ultrasound in Medicine", "url": "https://www.aium.org/", "description": "Professional society with guidelines and educational resources"},
            {"name": "Ultrasound Cases", "url": "https://www.ultrasoundcases.info/", "description": "Comprehensive ultrasound case collection"}
        ]
    }
    }
    
    return render_template("knowledge_base/index.html", subspecialties=subspecialties)
