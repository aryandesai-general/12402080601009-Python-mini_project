"""
Generate a professional 8-slide PowerPoint presentation (.pptx)
Design requirements:
- Plain white background (#FFFFFF)
- CVM logo at top-left corner
- ADIT logo at top-right corner
- Short, easy-to-explain content for faculty presentation
- Slide 1: Team members (Aryan, Laksh, Meet with enrollment numbers)
- Slide 2: Project Index (Overview of all 6 sections)
- Slide 3: Section 1 & 2 (Infrastructure & Students)
- Slide 4: Section 3 & 4 (Curriculum & Faculty Profiling featuring Dr. Priyang Bhatt's photo)
- Slide 5: Section 5 (Workload Balancing & HoD Quotas featuring Dr. Priyang Bhatt's photo)
- Slide 6: Section 6 (AI Timetable Engine & Detailed Layout)
- Slide 7: Verification Test Suite (6/6 Passed) & Exports
- Slide 8: Conclusion, Future Scope & Thank You
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_presentation(output_path):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Paths to logos and images
    cvm_logo_path = "/Users/aryandesai/Desktop/project AI/assets/cvm_logo.jpg"
    adit_logo_path = "/Users/aryandesai/Desktop/project AI/assets/adit_logo.png"
    priyang_img_path = "/Users/aryandesai/Desktop/project AI/assets/faculty_images/priyang_bhatt.jpg"

    # Color Palette for Plain White Theme
    COLOR_WHITE = RGBColor(255, 255, 255)
    COLOR_PRIMARY = RGBColor(30, 27, 75)       # Navy #1E1B4B
    COLOR_SECONDARY = RGBColor(15, 118, 110)   # Teal #0F766E
    COLOR_ACCENT = RGBColor(217, 119, 6)       # Amber/Gold #D97706
    COLOR_CARD_BG = RGBColor(248, 250, 252)    # Clean Slate 50
    COLOR_CARD_BORDER = RGBColor(226, 232, 240)# Slate 200
    COLOR_TEXT_MAIN = RGBColor(15, 23, 42)     # Slate 900
    COLOR_TEXT_MUTED = RGBColor(100, 116, 139) # Slate 500

    def add_slide_base(title_text=None, category_text=None, is_title_page=False):
        slide = prs.slides.add_slide(blank_layout)

        # 1. Plain White Background
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = COLOR_WHITE
        bg.line.fill.background()

        # 2. Add Logos at top both corners
        if os.path.exists(cvm_logo_path):
            slide.shapes.add_picture(cvm_logo_path, Inches(0.8), Inches(0.4), height=Inches(0.85))

        if os.path.exists(adit_logo_path):
            slide.shapes.add_picture(adit_logo_path, Inches(11.3), Inches(0.4), height=Inches(0.85))

        # 3. Header Bar / Titles
        if not is_title_page:
            h_box = slide.shapes.add_textbox(Inches(2.5), Inches(0.35), Inches(8.3), Inches(0.95))
            h_tf = h_box.text_frame
            h_tf.word_wrap = True

            if category_text:
                p_cat = h_tf.paragraphs[0]
                p_cat.text = category_text.upper()
                p_cat.font.size = Pt(10)
                p_cat.font.bold = True
                p_cat.font.color.rgb = COLOR_SECONDARY
                p_cat.alignment = PP_ALIGN.CENTER

            p_t = h_tf.add_paragraph() if category_text else h_tf.paragraphs[0]
            p_t.text = title_text
            p_t.font.size = Pt(20)
            p_t.font.bold = True
            p_t.font.color.rgb = COLOR_PRIMARY
            p_t.alignment = PP_ALIGN.CENTER

            line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.35), Inches(11.733), Inches(0.02))
            line.fill.solid()
            line.fill.fore_color.rgb = COLOR_CARD_BORDER
            line.line.fill.background()

        # Footer
        f_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.1), Inches(11.733), Inches(0.3))
        f_tf = f_box.text_frame
        p_f = f_tf.paragraphs[0]
        p_f.text = "A. D. Patel Institute of Technology (ADIT) • CVM University • AI Academic Timetable System"
        p_f.font.size = Pt(9)
        p_f.font.color.rgb = COLOR_TEXT_MUTED
        p_f.alignment = PP_ALIGN.CENTER

        return slide

    # ========================================================
    # SLIDE 1: Title Slide & Project Team Members
    # ========================================================
    slide1 = add_slide_base(is_title_page=True)

    top_box = slide1.shapes.add_textbox(Inches(2.4), Inches(0.4), Inches(8.5), Inches(0.9))
    top_tf = top_box.text_frame
    top_tf.word_wrap = True
    p_u = top_tf.paragraphs[0]
    p_u.text = "CHARUTAR VIDYAMANDAL UNIVERSITY (CVMU)"
    p_u.font.size = Pt(12)
    p_u.font.bold = True
    p_u.font.color.rgb = COLOR_SECONDARY
    p_u.alignment = PP_ALIGN.CENTER

    p_c = top_tf.add_paragraph()
    p_c.text = "A. D. PATEL INSTITUTE OF TECHNOLOGY (ADIT)"
    p_c.font.size = Pt(15)
    p_c.font.bold = True
    p_c.font.color.rgb = COLOR_PRIMARY
    p_c.alignment = PP_ALIGN.CENTER

    t_box = slide1.shapes.add_textbox(Inches(1.2), Inches(1.5), Inches(10.9), Inches(1.6))
    t_tf = t_box.text_frame
    t_tf.word_wrap = True
    p_title = t_tf.paragraphs[0]
    p_title.text = "AI-Driven Academic Timetable Generator\n& Schedule Optimizer"
    p_title.font.size = Pt(28)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_PRIMARY
    p_title.alignment = PP_ALIGN.CENTER

    p_sub = t_tf.add_paragraph()
    p_sub.text = "An Automated Constraint Satisfaction System for Institutional Multi-Departmental Timetable Optimization"
    p_sub.font.size = Pt(12)
    p_sub.font.color.rgb = COLOR_TEXT_MUTED
    p_sub.alignment = PP_ALIGN.CENTER
    p_sub.space_before = Pt(8)

    team_title = slide1.shapes.add_textbox(Inches(1.2), Inches(3.4), Inches(10.9), Inches(0.4))
    tt_tf = team_title.text_frame
    p_tt = tt_tf.paragraphs[0]
    p_tt.text = "PROJECT TEAM MEMBERS"
    p_tt.font.size = Pt(12)
    p_tt.font.bold = True
    p_tt.font.color.rgb = COLOR_ACCENT
    p_tt.alignment = PP_ALIGN.CENTER

    members = [
        ("1st", "Desai Aryan M.", "12402080601009", "Team Lead & AI Engine Developer"),
        ("2nd", "Limbani Laksh R.", "12402080601071", "Database & Constraints Designer"),
        ("3rd", "Panchal Meet K.", "12402080601080", "UI/UX & System Verification")
    ]

    for i, (rank, name, enr, role) in enumerate(members):
        x = Inches(1.0 + i * 3.85)
        y = Inches(3.9)
        card = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(3.6), Inches(2.7))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = COLOR_CARD_BORDER
        card.line.width = Pt(1.5)

        tb = slide1.shapes.add_textbox(x + Inches(0.15), y + Inches(0.2), Inches(3.3), Inches(2.3))
        tf = tb.text_frame
        tf.word_wrap = True

        p_r = tf.paragraphs[0]
        p_r.text = f"STUDENT {rank}"
        p_r.font.size = Pt(11)
        p_r.font.bold = True
        p_r.font.color.rgb = COLOR_SECONDARY
        p_r.alignment = PP_ALIGN.CENTER

        p_n = tf.add_paragraph()
        p_n.text = name
        p_n.font.size = Pt(16)
        p_n.font.bold = True
        p_n.font.color.rgb = COLOR_PRIMARY
        p_n.alignment = PP_ALIGN.CENTER
        p_n.space_before = Pt(6)

        p_enr = tf.add_paragraph()
        p_enr.text = f"Enrollment No:\n{enr}"
        p_enr.font.size = Pt(12)
        p_enr.font.bold = True
        p_enr.font.color.rgb = COLOR_TEXT_MAIN
        p_enr.alignment = PP_ALIGN.CENTER
        p_enr.space_before = Pt(10)

        p_role = tf.add_paragraph()
        p_role.text = role
        p_role.font.size = Pt(10)
        p_role.font.color.rgb = COLOR_TEXT_MUTED
        p_role.alignment = PP_ALIGN.CENTER
        p_role.space_before = Pt(8)

    # ========================================================
    # SLIDE 2: Project Index (Overview of all 6 Sections)
    # ========================================================
    slide2 = add_slide_base("Project Index: The 6 Core Modules", "SYSTEM BLUEPRINT")

    sections = [
        ("Section 1", "Classroom & Lab Infrastructure Manager", "36 rooms & labs (capacity, location, projector, lab equipment)."),
        ("Section 2", "Student Entry & Division Calculator", "Auto-calculates division counts (ceil(Intake/90)) and batches (A, B, C, D)."),
        ("Section 3", "Subject & Curriculum Manager", "Defines L-T-P-C credits, syllabus codes, and core vs. elective baskets."),
        ("Section 4", "Faculty Profiling & Skills Allotment", "55 specialized faculty profiles, skill keywords, and top-3 priorities."),
        ("Section 5", "Workload Balance & HoD Quota Dashboard", "Equal 14h teaching load for faculty and protected 3-6h HoD admin quota."),
        ("Section 6", "AI Timetable Engine & Export Suite", "Collision-free period generation, parallel electives, and A4 print export.")
    ]

    for i, (sec, title, desc) in enumerate(sections):
        x = Inches(0.8 + (i % 2) * 5.95)
        y = Inches(1.6 + (i // 2) * 1.7)
        card = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(5.7), Inches(1.5))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = COLOR_CARD_BORDER
        card.line.width = Pt(1)

        tb = slide2.shapes.add_textbox(x + Inches(0.2), y + Inches(0.15), Inches(5.3), Inches(1.2))
        tf = tb.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        p0.text = f"{sec}: {title}"
        p0.font.size = Pt(14)
        p0.font.bold = True
        p0.font.color.rgb = COLOR_PRIMARY

        p1 = tf.add_paragraph()
        p1.text = desc
        p1.font.size = Pt(11)
        p1.font.color.rgb = COLOR_TEXT_MAIN
        p1.space_before = Pt(4)

    # ========================================================
    # SLIDE 3: Section 1 & Section 2 Details
    # ========================================================
    slide3 = add_slide_base("Section 1 & 2: Infrastructure & Student Intake", "MODULES 1 & 2")

    card1 = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.2))
    card1.fill.solid()
    card1.fill.fore_color.rgb = COLOR_CARD_BG
    card1.line.color.rgb = COLOR_PRIMARY
    card1.line.width = Pt(1.5)

    tb1 = slide3.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.3), Inches(4.8))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p_s1 = tf1.paragraphs[0]
    p_s1.text = "🏛 Section 1: Classroom & Lab Manager"
    p_s1.font.size = Pt(16)
    p_s1.font.bold = True
    p_s1.font.color.rgb = COLOR_PRIMARY

    s1_points = [
        "Tracks all 36 institutional rooms and laboratories.",
        "Classrooms (Cap: 80-90) are common shared resources across all branches.",
        "Specialized Core Labs (Cap: 40) belong to specific departments (CAD-CAM, Thermo, AI, Reaction Labs).",
        "Tracks projector, smart display, AC, and high-speed LAN capabilities.",
        "Real-time facility conflict detection avoids double-booking."
    ]
    for pt in s1_points:
        p = tf1.add_paragraph()
        p.text = f"• {pt}"
        p.font.size = Pt(11.5)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_before = Pt(8)

    card2 = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2))
    card2.fill.solid()
    card2.fill.fore_color.rgb = COLOR_CARD_BG
    card2.line.color.rgb = COLOR_SECONDARY
    card2.line.width = Pt(1.5)

    tb2 = slide3.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
    tf2 = tb2.text_frame
    tf2.word_wrap = True

    p_s2 = tf2.paragraphs[0]
    p_s2.text = "👥 Section 2: Student Entry & Divisions"
    p_s2.font.size = Pt(16)
    p_s2.font.bold = True
    p_s2.font.color.rgb = COLOR_SECONDARY

    s2_points = [
        "Department-wise approved intake tracker (CE: 240, IT: 160, ME: 80, etc.).",
        "Auto-Division Formula: Divisions = ceil(Student Intake / 90).",
        "Batch Splitting: Every division is automatically split into 4 batches (A, B, C, D) for lab work.",
        "Lab Capacity Matching: Batches (20-22 students) are grouped 2 per lab room (Batches A+B in Lab 1, C+D in Lab 2).",
        "Prevents classroom overcrowding and guarantees university teacher-student ratio."
    ]
    for pt in s2_points:
        p = tf2.add_paragraph()
        p.text = f"• {pt}"
        p.font.size = Pt(11.5)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_before = Pt(8)

    # ========================================================
    # SLIDE 4: Section 3 & Section 4 Details (FEATURING DR. PRIYANG BHATT)
    # ========================================================
    slide4 = add_slide_base("Section 3 & 4: Curriculum & Faculty Allotment", "MODULES 3 & 4")

    # Left: Section 3
    card3 = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.5), Inches(5.2))
    card3.fill.solid()
    card3.fill.fore_color.rgb = COLOR_CARD_BG
    card3.line.color.rgb = COLOR_PRIMARY
    card3.line.width = Pt(1.5)

    tb3 = slide4.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.1), Inches(4.8))
    tf3 = tb3.text_frame
    tf3.word_wrap = True

    p_s3 = tf3.paragraphs[0]
    p_s3.text = "📚 Section 3: Subject & Curriculum Manager"
    p_s3.font.size = Pt(15)
    p_s3.font.bold = True
    p_s3.font.color.rgb = COLOR_PRIMARY

    s3_points = [
        "Curriculums for all 8 departments across all semesters (1 to 8).",
        "Complete L-T-P-C scheme (Lectures, Tutorials, Practicals, Credits).",
        "AICTE Categories: PCC (Core), PEC (Electives), OEC (Open Electives).",
        "High-Credit Priority: 4 & 5 credit subjects placed in prime morning hours.",
        "Parallel Electives: Configures PE baskets held simultaneously in separate rooms."
    ]
    for pt in s3_points:
        p = tf3.add_paragraph()
        p.text = f"• {pt}"
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_before = Pt(8)

    # Right: Section 4 WITH DR. PRIYANG BHATT IMAGE
    card4 = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.6), Inches(1.6), Inches(5.9), Inches(5.2))
    card4.fill.solid()
    card4.fill.fore_color.rgb = COLOR_CARD_BG
    card4.line.color.rgb = COLOR_SECONDARY
    card4.line.width = Pt(1.5)

    # Add Dr. Priyang Bhatt's Photo in Section 4 Card
    if os.path.exists(priyang_img_path):
        slide4.shapes.add_picture(priyang_img_path, Inches(11.0), Inches(1.8), width=Inches(1.2), height=Inches(1.2))

    tb4 = slide4.shapes.add_textbox(Inches(6.8), Inches(1.8), Inches(4.1), Inches(1.3))
    tf4 = tb4.text_frame
    tf4.word_wrap = True

    p_s4 = tf4.paragraphs[0]
    p_s4.text = "👨‍🏫 Section 4: Faculty Profiling"
    p_s4.font.size = Pt(15)
    p_s4.font.bold = True
    p_s4.font.color.rgb = COLOR_SECONDARY

    p_prb = tf4.add_paragraph()
    p_prb.text = "Featured: Dr. Priyang Bhatt\nAssociate Professor & Head (IT Dept)\nSpecialization: Cloud Computing, DevOps"
    p_prb.font.size = Pt(10)
    p_prb.font.color.rgb = COLOR_TEXT_MUTED
    p_prb.space_before = Pt(2)

    # Bullet points below photo
    tb4_b = slide4.shapes.add_textbox(Inches(6.8), Inches(3.2), Inches(5.5), Inches(3.4))
    tf4_b = tb4_b.text_frame
    tf4_b.word_wrap = True

    s4_points = [
        "Profiles all 55 authentic faculty across 8 branches + ASH.",
        "Zero duplicates: Every faculty member is unique with verified credentials.",
        "Verified skill keywords and top-3 subject teaching priorities.",
        "Inter-Departmental Faculty Pooling: IT shared with AI&DS, CE shared with CSD, and ASH for Open Electives.",
        "Priority bonus scoring (+200 pts) assigns subjects matching professor expertise."
    ]
    for i, pt in enumerate(s4_points):
        p = tf4_b.paragraphs[0] if i == 0 else tf4_b.add_paragraph()
        p.text = f"• {pt}"
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_TEXT_MAIN
        if i > 0:
            p.space_before = Pt(6)

    # ========================================================
    # SLIDE 5: Section 5: Workload Balancing & HoD Quota (FEATURING DR. PRIYANG BHATT)
    # ========================================================
    slide5 = add_slide_base("Section 5: Equal Workload & HoD Admin Quotas", "MODULE 5")

    metrics = [
        ("55 / 55", "Faculty Allotted", COLOR_PRIMARY),
        ("0 Faculty", "With 0 Subjects", COLOR_SECONDARY),
        ("0 Faculty", "With 0 Hours", COLOR_SECONDARY),
        ("100% Balanced", "HoD (4-5h) / Reg (14h)", COLOR_ACCENT)
    ]
    for i, (m_val, m_lbl, m_col) in enumerate(metrics):
        x = Inches(0.8 + i * 2.98)
        c_m = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.6), Inches(2.8), Inches(1.15))
        c_m.fill.solid()
        c_m.fill.fore_color.rgb = COLOR_CARD_BG
        c_m.line.color.rgb = m_col
        c_m.line.width = Pt(1.5)

        tb_m = slide5.shapes.add_textbox(x, Inches(1.68), Inches(2.8), Inches(1.0))
        tf_m = tb_m.text_frame
        p0 = tf_m.paragraphs[0]
        p0.text = m_val
        p0.font.size = Pt(18)
        p0.font.bold = True
        p0.font.color.rgb = m_col
        p0.alignment = PP_ALIGN.CENTER

        p1 = tf_m.add_paragraph()
        p1.text = m_lbl
        p1.font.size = Pt(10)
        p1.font.color.rgb = COLOR_TEXT_MUTED
        p1.alignment = PP_ALIGN.CENTER

    # Left: HoD Quota WITH DR. PRIYANG BHATT PHOTO
    card_wl_l = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(3.0), Inches(5.7), Inches(3.8))
    card_wl_l.fill.solid()
    card_wl_l.fill.fore_color.rgb = COLOR_CARD_BG
    card_wl_l.line.color.rgb = COLOR_PRIMARY
    card_wl_l.line.width = Pt(1.5)

    # Insert Dr. Priyang Bhatt's Photo in the HoD Card
    if os.path.exists(priyang_img_path):
        slide5.shapes.add_picture(priyang_img_path, Inches(5.1), Inches(3.15), width=Inches(1.2), height=Inches(1.2))

    tb_wl_l = slide5.shapes.add_textbox(Inches(1.0), Inches(3.15), Inches(4.0), Inches(1.3))
    tf_wl_l = tb_wl_l.text_frame
    tf_wl_l.word_wrap = True
    p_l = tf_wl_l.paragraphs[0]
    p_l.text = "🎖️ HoD Administrative Quota"
    p_l.font.size = Pt(14)
    p_l.font.bold = True
    p_l.font.color.rgb = COLOR_PRIMARY

    p_l_sub = tf_wl_l.add_paragraph()
    p_l_sub.text = "Case Study: Dr. Priyang Bhatt (HoD IT)\nWeekly Load: 4h Theory • Status: Optimal HoD Quota"
    p_l_sub.font.size = Pt(9.5)
    p_l_sub.font.bold = True
    p_l_sub.font.color.rgb = COLOR_SECONDARY
    p_l_sub.space_before = Pt(2)

    tb_wl_lb = slide5.shapes.add_textbox(Inches(1.0), Inches(4.5), Inches(5.3), Inches(2.2))
    tf_wl_lb = tb_wl_lb.text_frame
    tf_wl_lb.word_wrap = True

    hod_points = [
        "AICTE Guideline: HoDs require time for departmental leadership, NBA/NAAC accreditation, and governance.",
        "Teaching Load Cap: Strictly 3 to 6 hours/week.",
        "Penalty Formulation: +85 score on 1st choice subject, -3500 penalty if load exceeds 6 hours.",
        "Result: HoDs teach their primary core course without heavy lab overload."
    ]
    for i, pt in enumerate(hod_points):
        p = tf_wl_lb.paragraphs[0] if i == 0 else tf_wl_lb.add_paragraph()
        p.text = f"• {pt}"
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_TEXT_MAIN
        if i > 0:
            p.space_before = Pt(4)

    # Right: Regular Faculty
    card_wl_r = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(3.0), Inches(5.7), Inches(3.8))
    card_wl_r.fill.solid()
    card_wl_r.fill.fore_color.rgb = COLOR_CARD_BG
    card_wl_r.line.color.rgb = COLOR_SECONDARY
    card_wl_r.line.width = Pt(1.5)

    tb_wl_r = slide5.shapes.add_textbox(Inches(7.0), Inches(3.15), Inches(5.3), Inches(3.5))
    tf_wl_r = tb_wl_r.text_frame
    tf_wl_r.word_wrap = True
    p_r = tf_wl_r.paragraphs[0]
    p_r.text = "⚖️ Regular Faculty Equalization (12-16h)"
    p_r.font.size = Pt(14)
    p_r.font.bold = True
    p_r.font.color.rgb = COLOR_SECONDARY

    reg_points = [
        "Equal Workload Norm: Every regular assistant/associate professor receives balanced 12–16 hrs/week (14h target).",
        "Balanced Composition: 6–8 hrs theory lectures + 6–8 hrs practical lab sessions.",
        "Dynamic Lab Sorting: Practical lab sessions are round-robin allocated to least-loaded faculty first.",
        "Zero Idle Faculty: All 55 faculty members have assigned subjects clearly displayed in the dashboard.",
        "Prevents faculty burnout and ensures fair departmental distribution."
    ]
    for pt in reg_points:
        p = tf_wl_r.add_paragraph()
        p.text = f"• {pt}"
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_before = Pt(6)

    # ========================================================
    # SLIDE 6: Section 6: AI Timetable Engine
    # ========================================================
    slide6 = add_slide_base("Section 6: AI Timetable Engine & Academic Rules", "MODULE 6")

    card_ai_1 = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.2))
    card_ai_1.fill.solid()
    card_ai_1.fill.fore_color.rgb = COLOR_CARD_BG
    card_ai_1.line.color.rgb = COLOR_PRIMARY
    card_ai_1.line.width = Pt(1.5)

    tb_ai_1 = slide6.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.3), Inches(4.8))
    tf_ai_1 = tb_ai_1.text_frame
    tf_ai_1.word_wrap = True
    p_a1 = tf_ai_1.paragraphs[0]
    p_a1.text = "⚡ Automated Constraint Satisfaction Core"
    p_a1.font.size = Pt(15)
    p_a1.font.bold = True
    p_a1.font.color.rgb = COLOR_PRIMARY

    ai_points_1 = [
        "Backtracking CSP Solver: Places theory and lab periods across Mon-Fri grid in < 150 milliseconds.",
        "Zero Collision Guarantee: Hard mathematical sets ensure bookedFaculty and bookedRooms never clash.",
        "Saturday Holiday Invariant: Mon-Fri teaching schedule with exactly 0 slots booked on Saturdays.",
        "Synchronized Lunch Break: 12:40 PM - 1:25 PM preserved uniformly across all divisions.",
        "Parallel Electives (PE1/PE2): Options are scheduled simultaneously in different rooms so students can choose."
    ]
    for pt in ai_points_1:
        p = tf_ai_1.add_paragraph()
        p.text = f"• {pt}"
        p.font.size = Pt(11.5)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_before = Pt(8)

    card_ai_2 = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2))
    card_ai_2.fill.solid()
    card_ai_2.fill.fore_color.rgb = COLOR_CARD_BG
    card_ai_2.line.color.rgb = COLOR_SECONDARY
    card_ai_2.line.width = Pt(1.5)

    tb_ai_2 = slide6.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
    tf_ai_2 = tb_ai_2.text_frame
    tf_ai_2.word_wrap = True
    p_a2 = tf_ai_2.paragraphs[0]
    p_a2.text = "📋 Clean Timetable UI & Detailed Views"
    p_a2.font.size = Pt(15)
    p_a2.font.bold = True
    p_a2.font.color.rgb = COLOR_SECONDARY

    ai_points_2 = [
        "Clean Text-Based Grid: Readable subject codes, professor names, and classroom numbers (no cluttered cell images).",
        "Academic Metadata Strip: Program Code, Faculty Code, Room No, Counselor, and Effective Date.",
        "Full Course Legend Table: Details Course Code, Name, Category, L-T-P-C Credits, and Faculty.",
        "Faculty Allotment Cards: Displays authentic faculty photos, designations, and workload hours.",
        "Institutional Signatures: Pre-configured signature blocks for Coordinator, HoD, and Principal."
    ]
    for pt in ai_points_2:
        p = tf_ai_2.add_paragraph()
        p.text = f"• {pt}"
        p.font.size = Pt(11.5)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_before = Pt(8)

    # ========================================================
    # SLIDE 7: System Verification & Export Suite
    # ========================================================
    slide7 = add_slide_base("Verification Test Suite & Export Capabilities", "VERIFICATION & RESULTS")

    card_v1 = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.2))
    card_v1.fill.solid()
    card_v1.fill.fore_color.rgb = COLOR_CARD_BG
    card_v1.line.color.rgb = COLOR_SECONDARY
    card_v1.line.width = Pt(1.5)

    tb_v1 = slide7.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.3), Inches(4.8))
    tf_v1 = tb_v1.text_frame
    tf_v1.word_wrap = True
    p_v1 = tf_v1.paragraphs[0]
    p_v1.text = "🧪 Automated Test Suite (6/6 Passed)"
    p_v1.font.size = Pt(15)
    p_v1.font.bold = True
    p_v1.font.color.rgb = COLOR_SECONDARY

    test_items = [
        ("Test 1", "All 8 Engineering Departments generated (Div 1 & 2)."),
        ("Test 2", "Zero faculty double-booking collisions across all branches."),
        ("Test 3", "Inter-departmental faculty pooling active (IT ⇄ AIDS, CE ⇄ CSD)."),
        ("Test 4", "Saturday Holiday invariant verified (0 slots booked)."),
        ("Test 5", "Parallel Elective invariant verified (different rooms, same time)."),
        ("Test 6", "Lab Timing invariant verified (non-overlapping practicals).")
    ]
    for code, desc in test_items:
        p = tf_v1.add_paragraph()
        p.text = f"✅ {code}: {desc}"
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_before = Pt(6)

    card_v2 = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2))
    card_v2.fill.solid()
    card_v2.fill.fore_color.rgb = COLOR_CARD_BG
    card_v2.line.color.rgb = COLOR_PRIMARY
    card_v2.line.width = Pt(1.5)

    tb_v2 = slide7.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
    tf_v2 = tb_v2.text_frame
    tf_v2.word_wrap = True
    p_v2 = tf_v2.paragraphs[0]
    p_v2.text = "📤 Multi-Format Export & Usability"
    p_v2.font.size = Pt(15)
    p_v2.font.bold = True
    p_v2.font.color.rgb = COLOR_PRIMARY

    export_items = [
        "A4 Landscape Print View: CSS print stylesheet formatted precisely for single-page notice board printing.",
        "High-Resolution PNG Canvas Export: Generates publication-ready timetable graphics with single click.",
        "Excel/CSV Timetable Export: Direct tabular download for departmental documentation.",
        "Interactive Click-to-Edit: Coordinators can manually adjust any slot with live conflict re-checks.",
        "Instant Generation: Full 8-department schedule solves in < 150 ms."
    ]
    for desc in export_items:
        p = tf_v2.add_paragraph()
        p.text = f"• {desc}"
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_before = Pt(6)

    # ========================================================
    # SLIDE 8: Conclusion, Future Scope & Thank You
    # ========================================================
    slide8 = add_slide_base("Conclusion, Future Roadmap & Acknowledgments", "SUMMARY & OUTLOOK")

    card_c1 = slide8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.733), Inches(1.9))
    card_c1.fill.solid()
    card_c1.fill.fore_color.rgb = COLOR_CARD_BG
    card_c1.line.color.rgb = COLOR_SECONDARY
    card_c1.line.width = Pt(1.5)

    tb_c1 = slide8.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(11.333), Inches(1.6))
    tf_c1 = tb_c1.text_frame
    tf_c1.word_wrap = True
    p_c1 = tf_c1.paragraphs[0]
    p_c1.text = "🌟 Project Summary & Key Takeaways"
    p_c1.font.size = Pt(14)
    p_c1.font.bold = True
    p_c1.font.color.rgb = COLOR_SECONDARY

    c_points = [
        "Transformed a manual, error-prone 2-week scheduling process into an instant 150ms automated AI execution.",
        "Achieved 100% collision-free scheduling and mathematically balanced workloads across all 55 faculty members.",
        "Full university compliance: Saturday holidays, parallel elective streaming, and HoD admin quotas."
    ]
    for pt in c_points:
        p = tf_c1.add_paragraph()
        p.text = f"• {pt}"
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_before = Pt(3)

    card_c2 = slide8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(3.7), Inches(11.733), Inches(1.9))
    card_c2.fill.solid()
    card_c2.fill.fore_color.rgb = COLOR_CARD_BG
    card_c2.line.color.rgb = COLOR_PRIMARY
    card_c2.line.width = Pt(1.5)

    tb_c2 = slide8.shapes.add_textbox(Inches(1.0), Inches(3.85), Inches(11.333), Inches(1.6))
    tf_c2 = tb_c2.text_frame
    tf_c2.word_wrap = True
    p_c2 = tf_c2.paragraphs[0]
    p_c2.text = "🚀 Future Scope & Enhancements"
    p_c2.font.size = Pt(14)
    p_c2.font.bold = True
    p_c2.font.color.rgb = COLOR_PRIMARY

    f_points = [
        "Student Elective Polling: Real-time student portal to register elective choices with dynamic division scaling.",
        "Mobile & Calendar Sync: 1-click export to Google Calendar and Apple iCal for students and faculty.",
        "Smart Classroom IoT Sensors: Dynamic room re-allotment based on real-time attendance tracking."
    ]
    for pt in f_points:
        p = tf_c2.add_paragraph()
        p.text = f"• {pt}"
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_before = Pt(3)

    ty_card = slide8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.8), Inches(11.733), Inches(1.05))
    ty_card.fill.solid()
    ty_card.fill.fore_color.rgb = COLOR_PRIMARY
    ty_card.line.fill.background()

    tb_ty = slide8.shapes.add_textbox(Inches(1.0), Inches(5.9), Inches(11.333), Inches(0.85))
    tf_ty = tb_ty.text_frame
    p_ty = tf_ty.paragraphs[0]
    p_ty.text = "🎉 Thank You! Questions & Discussion Welcome."
    p_ty.font.size = Pt(16)
    p_ty.font.bold = True
    p_ty.font.color.rgb = COLOR_WHITE
    p_ty.alignment = PP_ALIGN.CENTER

    p_cred = tf_ty.add_paragraph()
    p_cred.text = "Desai Aryan M. (12402080601009) • Limbani Laksh R. (12402080601071) • Panchal Meet K. (12402080601080)"
    p_cred.font.size = Pt(10.5)
    p_cred.font.color.rgb = RGBColor(226, 232, 240)
    p_cred.alignment = PP_ALIGN.CENTER
    p_cred.space_before = Pt(4)

    prs.save(output_path)
    print(f"Saved plain white 8-slide presentation to: {output_path}")

if __name__ == "__main__":
    out_dir = "/Users/aryandesai/Desktop/project AI"
    out_file = os.path.join(out_dir, "ADIT_AI_Timetable_Presentation.pptx")
    create_presentation(out_file)
