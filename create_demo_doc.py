"""
Generate a demo automotive service manual PDF for testing the upload functionality.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.colors import HexColor
import os

def create_demo_pdf(output_path: str):
    """Create a demo automotive service manual PDF"""
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=HexColor('#1a365d'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#2c5282'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    subsection_style = ParagraphStyle(
        'SubsectionHeader',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=HexColor('#2b6cb0'),
        spaceAfter=8,
        spaceBefore=8
    )
    
    body_style = styles['BodyText']
    body_style.fontSize = 11
    body_style.spaceAfter = 10
    
    warning_style = ParagraphStyle(
        'Warning',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#c53030'),
        spaceAfter=8,
        bold=True
    )
    
    caution_style = ParagraphStyle(
        'Caution',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#c05621'),
        spaceAfter=8,
        bold=True
    )
    
    note_style = ParagraphStyle(
        'Note',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#2d3748'),
        spaceAfter=8,
        italics=True
    )
    
    procedure_style = ParagraphStyle(
        'Procedure',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        leftIndent=20
    )
    
    story = []
    
    story.append(Paragraph("AUTOMOTIVE SERVICE MANUAL", title_style))
    story.append(Paragraph("Brake System - Front Disc Brakes", title_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Document ID: FSM-2024-BRAKE-001", body_style))
    story.append(Paragraph("Vehicle Type: Standard Passenger Vehicles", body_style))
    story.append(Spacer(1, 30))
    
    story.append(Paragraph("SECTION 1: INTRODUCTION", section_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "This section covers the inspection, removal, and installation of front disc "
        "brake pads and related components. Follow all procedures carefully to ensure "
        "proper brake operation and vehicle safety.",
        body_style
    ))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("WARNING:", warning_style))
    story.append(Paragraph(
        "Always wear safety glasses and gloves when working on brake systems. "
        "Brake dust may contain asbestos fibers - use proper respiratory protection.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("CAUTION:", caution_style))
    story.append(Paragraph(
        "Do not use compressed air to clean brake components as it may spread "
        "hazardous dust particles.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("NOTE:", note_style))
    story.append(Paragraph(
        "It is recommended to replace brake pads in pairs (both sides) to ensure "
        "even wear and consistent braking performance.",
        body_style
    ))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("SECTION 2: INSPECTION PROCEDURES", section_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("2.1 Visual Inspection", subsection_style))
    story.append(Paragraph(
        "Park the vehicle on a level surface and engage the parking brake. "
        "Loosen the front wheel lug nuts while the vehicle is on the ground.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Step 1: Lift the Vehicle", procedure_style))
    story.append(Paragraph(
        "Use a hydraulic jack to lift the front of the vehicle. Place jack stands "
        "under the designated lift points as indicated in Figure 1.",
        body_style
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Step 2: Remove the Wheel", procedure_style))
    story.append(Paragraph(
        "Remove the lug nuts and take off the front wheel. Set aside in a safe location.",
        body_style
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Step 3: Inspect Brake Pads", procedure_style))
    story.append(Paragraph(
        "Locate the brake caliper and inspect the brake pad lining thickness. "
        "Minimum acceptable thickness is 3mm. See Table 1 for specifications.",
        body_style
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Step 4: Check Rotor Condition", procedure_style))
    story.append(Paragraph(
        "Examine the brake rotor surface for scoring, grooves, or visible wear marks. "
        "Measure rotor thickness using a micrometer. Replace if below minimum specification.",
        body_style
    ))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Table 1: Brake Pad Specifications", subsection_style))
    story.append(Spacer(1, 5))
    story.append(Paragraph("• Original Pad Thickness: 12mm", body_style))
    story.append(Paragraph("• Minimum Service Thickness: 3mm", body_style))
    story.append(Paragraph("• Recommended Replacement Interval: 30,000-50,000 miles", body_style))
    story.append(Paragraph("• Pad Material: Ceramic (standard) or Semi-Metallic (performance)", body_style))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("SECTION 3: REMOVAL PROCEDURE", section_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("3.1 Caliper Removal", subsection_style))
    story.append(Paragraph(
        "To access the brake pads, the caliper must be removed. Support the caliper "
        "with wire - do not let it hang from the brake hose.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Step 1: Loosen Caliper Bolts", procedure_style))
    story.append(Paragraph(
        "Using a socket wrench, loosen the caliper guide bolts. Apply penetrating "
        "oil if bolts are corroded.",
        body_style
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Step 2: Remove Caliper", procedure_style))
    story.append(Paragraph(
        "Remove the bolts and carefully slide the caliper off the rotor. Hang it "
        "securely using wire or a suitable hanger.",
        body_style
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Step 3: Remove Old Brake Pads", procedure_style))
    story.append(Paragraph(
        "Slide the brake pads out of the caliper bracket. Note the orientation "
        "of the wear indicators for proper installation.",
        body_style
    ))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("SECTION 4: INSTALLATION PROCEDURE", section_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("4.1 Installing New Pads", subsection_style))
    story.append(Paragraph(
        "Apply brake grease to the back of the new pads in the areas indicated "
        "in Figure 2. Do not apply grease to the friction surface.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Step 1: Compress Piston", procedure_style))
    story.append(Paragraph(
        "Use a C-clamp or piston compression tool to push the caliper piston back "
        "into its bore. This makes room for the new, thicker brake pads.",
        body_style
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Step 2: Install New Pads", procedure_style))
    story.append(Paragraph(
        "Place the new brake pads into the caliper bracket, ensuring the wear "
        "indicator is positioned correctly.",
        body_style
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Step 3: Reinstall Caliper", procedure_style))
    story.append(Paragraph(
        "Slide the caliper back over the rotor and pads. Install the guide bolts "
        "and tighten to the manufacturer's specified torque (typically 25-35 ft-lbs).",
        body_style
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Step 4: Reinstall Wheel", procedure_style))
    story.append(Paragraph(
        "Place the wheel back on the hub and hand-tighten the lug nuts. Lower "
        "the vehicle and tighten lug nuts in a star pattern to 100 ft-lbs.",
        body_style
    ))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("SECTION 5: POST-INSTALLATION CHECKS", section_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("WARNING:", warning_style))
    story.append(Paragraph(
        "After installation, you MUST test drive the vehicle in a safe area to "
        "verify brake function before returning to normal driving.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Test Procedure:", subsection_style))
    story.append(Paragraph("1. Start the engine and let it idle for 1 minute.", body_style))
    story.append(Paragraph("2. Apply light brake pressure to seat the pads - repeat 5-10 times.", body_style))
    story.append(Paragraph("3. Drive at low speed (20 mph) and test brake responsiveness.", body_style))
    story.append(Paragraph("4. Gradually increase speed and test braking at various speeds.", body_style))
    story.append(Paragraph("5. Listen for unusual noises such as squealing or grinding.", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("NOTE:", note_style))
    story.append(Paragraph(
        "New brake pads may require 200-300 miles to fully break in. Expect slightly "
        "longer stopping distances during this period.",
        body_style
    ))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("SECTION 6: TROUBLESHOOTING", section_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Common Issues:", subsection_style))
    story.append(Paragraph(
        "• Squealing brakes: Check pad installation, may need brake grease on back of pads",
        body_style
    ))
    story.append(Paragraph(
        "• Brake pedal pulsation: Rotor may be warped - check runout with dial indicator",
        body_style
    ))
    story.append(Paragraph(
        "• Reduced braking power: Check for air in brake lines or worn pads",
        body_style
    ))
    story.append(Paragraph(
        "• Brake drag: Check caliper slides are moving freely, apply appropriate grease",
        body_style
    ))
    story.append(Spacer(1, 20))
    
    story.append(PageBreak())
    
    story.append(Paragraph("APPENDIX A: TORQUE SPECIFICATIONS", section_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("• Wheel Lug Nuts: 100 ft-lbs (135 Nm)", body_style))
    story.append(Paragraph("• Caliper Guide Bolts: 25-35 ft-lbs (34-47 Nm)", body_style))
    story.append(Paragraph("• Caliper Bleeder Valve: 10-15 ft-lbs (14-20 Nm)", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("APPENDIX B: REQUIRED TOOLS", section_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("• Hydraulic jack and jack stands", body_style))
    story.append(Paragraph("• Socket set (metric and SAE)", body_style))
    story.append(Paragraph("• Torque wrench", body_style))
    story.append(Paragraph("• Brake bleeder kit", body_style))
    story.append(Paragraph("• C-clamp or piston compression tool", body_style))
    story.append(Paragraph("• Brake grease", body_style))
    story.append(Paragraph("• Wire for hanging caliper", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("APPENDIX C: FIGURE REFERENCES", section_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Figure 1: Jack stand lift points - See vehicle owner's manual", body_style))
    story.append(Paragraph("Figure 2: Brake pad grease application points", body_style))
    story.append(Paragraph("Figure 3: Brake system hydraulic layout", body_style))
    story.append(Spacer(1, 30))
    
    story.append(Paragraph("END OF DOCUMENT", title_style))
    
    doc.build(story)
    print(f"Demo PDF created successfully: {output_path}")

if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(__file__), "demo_automotive_service_manual.pdf")
    create_demo_pdf(output_path)