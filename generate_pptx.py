"""
Script to generate a professional 8-slide PowerPoint presentation (.pptx)
for the ADIT AI Timetable Maker project.
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_presentation(output_path):
    prs = Presentation()
    # 16:9 Widescreen slides
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_slide_layout = prs.slide_layouts[6]

    # Theme Colors
    COLOR_PRIMARY = RGBColor(30, 27, 75)      # Deep Navy #1E1B4B
    COLOR_SECONDARY = RGBColor(15, 118, 110)  # Teal/Emerald #0F766E
    COLOR_ACCENT = RGBColor(217, 119, 6)      # Amber/Gold #D97706
    COLOR_BG_LIGHT = RGBColor(248, 250, 252)  # Slate 50
    COLOR_CARD_BG = RGBColor(241, 245, 249)   # Slate 100
    COLOR_CARD_BORDER = RGBColor(203, 213, 225)# Slate 300
    COLOR_TEXT_DARK = RGBColor(15, 23, 42)    # Slate 900
    COLOR_TEXT_MUTED = RGBColor(100, 116, 139)# Slate 500
    COLOR_WHITE = RGBColor(255, 255, 255)

    def add_header(slide, title_text, category_text="ADIT AI ACADEMIC TIMETABLE GENERATOR"):
        # Top banner background shape
        top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.15))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = COLOR_PRIMARY
        top_bar.line.fill.background()

        # Category / Mini Tag
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.12), Inches(11.733), Inches(0.3))
        cat_tf = cat_box.text_frame
        cat_tf.word_wrap = True
        p_cat = cat_tf.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = COLOR_ACCENT

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.38), Inches(11.733), Inches(0.65))
        title_tf = title_box.text_frame
        title_tf.word_wrap = True
        p_title = title_tf.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = COLOR_WHITE

        # Bottom subtle footer line
        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.1), Inches(11.733), Inches(0.3))
        ft_tf = footer_box.text_frame
        p_ft = ft_tf.paragraphs[0]
        p_ft.text = "A. D. Patel Institute of Technology (ADIT) • CVM University • AI Timetable Optimization System"
        p_ft.font.size = Pt(9)
        p_ft.font.color.rgb = COLOR_TEXT_MUTED

    # ========================================================
    # SLIDE 1: Title Slide (Dark Elegant Background)
    # ========================================================
    slide1 = prs.slides.add_slide(blank_slide_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = COLOR_PRIMARY
    bg1.line.fill.background()

    # Decorative accent card
    card_dec = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.8), Inches(11.733), Inches(5.9))
    card_dec.fill.solid()
    card_dec.fill.fore_color.rgb = RGBColor(23, 20, 60)
    card_dec.line.color.rgb = RGBColor(79, 70, 229)
    card_dec.line.width = Pt(1.5)

    # Subtitle tag
    tag_box = slide1.shapes.add_textbox(Inches(1.2), Inches(1.2), Inches(10), Inches(0.4))
    tag_tf = tag_box.text_frame
    p_tag = tag_tf.paragraphs[0]
    p_tag.text = "🎓 CVM UNIVERSITY • A. D. PATEL INSTITUTE OF TECHNOLOGY"
    p_tag.font.size = Pt(12)
    p_tag.font.bold = True
    p_tag.font.color.rgb = COLOR_ACCENT

    # Main Title
    t_box = slide1.shapes.add_textbox(Inches(1.2), Inches(1.7), Inches(10.5), Inches(1.8))
    t_tf = t_box.text_frame
    t_tf.word_wrap = True
    p_t = t_tf.paragraphs[0]
    p_t.text = "AI-Driven Academic Timetable Generator\n& Workload Optimization System"
    p_t.font.size = Pt(32)
    p_t.font.bold = True
    p_t.font.color.rgb = COLOR_WHITE

    # Divider bar
    div_bar = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(3.6), Inches(2.5), Inches(0.06))
    div_bar.fill.solid()
    div_bar.fill.fore_color.rgb = COLOR_ACCENT
    div_bar.line.fill.background()

    # Description
    desc_box = slide1.shapes.add_textbox(Inches(1.2), Inches(3.8), Inches(10.5), Inches(1.2))
    desc_tf = desc_box.text_frame
    desc_tf.word_wrap = True
    p_desc = desc_tf.paragraphs[0]
    p_desc.text = "An intelligent constraint satisfaction engine delivering collision-free schedules, balanced faculty workloads, parallel elective handling, and automated university compliance across 8 engineering departments."
    p_desc.font.size = Pt(14)
    p_desc.font.color.rgb = RGBColor(226, 232, 240)

    # Metadata Grid (Author, Year, Department)
    meta_box = slide1.shapes.add_textbox(Inches(1.2), Inches(5.1), Inches(10.5), Inches(1.2))
    meta_tf = meta_box.text_frame
    meta_tf.word_wrap = True
    p_m1 = meta_tf.paragraphs[0]
    p_m1.text = "Developed by: Aryan Desai & Project Team"
    p_m1.font.size = Pt(13)
    p_m1.font.bold = True
    p_m1.font.color.rgb = COLOR_WHITE

    p_m2 = meta_tf.add_paragraph()
    p_m2.text = "Department: Computer Engineering / Information Technology • Academic Year: 2026-27"
    p_m2.font.size = Pt(11)
    p_m2.font.color.rgb = COLOR_TEXT_MUTED

    # ========================================================
    # SLIDE 2: Problem Statement & Existing Challenges
    # ========================================================
    slide2 = prs.slides.add_slide(blank_slide_layout)
    add_header(slide2, "Problem Statement & Challenges in Academic Scheduling", "01 • BACKGROUND & PROBLEM")

    cards_s2 = [
        ("High-Dimensional Complexity", "Scheduling 8 engineering departments with 55 faculty members, 36 classrooms & labs, and 560+ weekly periods creates an NP-hard combinatorial problem practically impossible to optimize manually.", "🧩"),
        ("Faculty Collisions & Clashes", "Manual timetable drafting frequently leads to double-booking professors across multiple lecture halls, conflicting laboratory timings, and room allocation conflicts.", "⚠️"),
        ("Unequal Workload Distribution", "Traditional scheduling leaves some faculty severely overloaded (>18h/week) while others remain underutilized, violating AICTE and university norms.", "⚖️"),
        ("HoD & Elective Friction", "Heads of Department (HoDs) require reduced administrative quotas (3-6h/week). Concurrently, parallel elective streams (same time, different rooms) create scheduling bottlenecks.", "🏛️")
    ]

    for i, (title, body, icon) in enumerate(cards_s2):
        x = Inches(0.8 + (i % 2) * 5.95)
        y = Inches(1.5 + (i // 2) * 2.65)
        card = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(5.7), Inches(2.4))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = COLOR_CARD_BORDER
        card.line.width = Pt(1)

        tb = slide2.shapes.add_textbox(x + Inches(0.2), y + Inches(0.2), Inches(5.3), Inches(2.0))
        tf = tb.text_frame
        tf.word_wrap = True
        p0 = tf.paragraphs[0]
        p0.text = f"{icon}  {title}"
        p0.font.size = Pt(15)
        p0.font.bold = True
        p0.font.color.rgb = COLOR_PRIMARY

        p1 = tf.add_paragraph()
        p1.text = body
        p1.font.size = Pt(12)
        p1.font.color.rgb = COLOR_TEXT_DARK
        p1.space_before = Pt(8)

    # ========================================================
    # SLIDE 3: Project Objectives & Scope
    # ========================================================
    slide3 = prs.slides.add_slide(blank_slide_layout)
    add_header(slide3, "Project Objectives & Technical Scope", "02 • OBJECTIVES & DELIVERABLES")

    objectives = [
        ("100% Collision-Free AI Generation", "Produce conflict-free academic timetables across all 8 branches (CE, IT, CSD, AIDS, ME, CL, EE, CH) for Div 1 & Div 2 in under 200ms."),
        ("Equal Workload Distribution Across All 55 Faculty", "Guarantee zero unassigned faculty (0 with 0 hours, 0 with 0 subjects). Every regular faculty receives 12–16 hrs/week, while HoDs receive 3–6 hrs/week."),
        ("Inter-Departmental Faculty Pooling", "Intelligently share specialized faculty across allied branches (IT ⇄ AIDS, CE ⇄ CSD, and ASH for Institute Open Electives)."),
        ("Strict Academic Rule Adherence", "Enforce Saturday holiday invariants, dedicated 45-min lunch break, 2-hour laboratory blocks (2 batches/room), and parallel elective baskets."),
        ("Interactive Editing & Instant Export", "Allow coordinators to click-to-edit periods on the fly and export official A4 Landscape PDFs, high-res PNGs, and CSV schedules.")
    ]

    for i, (title, desc) in enumerate(objectives):
        y = Inches(1.5 + i * 1.05)
        bar = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), y, Inches(11.733), Inches(0.92))
        bar.fill.solid()
        bar.fill.fore_color.rgb = COLOR_CARD_BG if i % 2 == 0 else COLOR_WHITE
        bar.line.color.rgb = COLOR_CARD_BORDER

        tb = slide3.shapes.add_textbox(Inches(1.0), y + Inches(0.1), Inches(11.333), Inches(0.72))
        tf = tb.text_frame
        tf.word_wrap = True
        p0 = tf.paragraphs[0]
        p0.text = f"✔  {title}"
        p0.font.size = Pt(14)
        p0.font.bold = True
        p0.font.color.rgb = COLOR_SECONDARY

        p1 = tf.add_paragraph()
        p1.text = desc
        p1.font.size = Pt(11.5)
        p1.font.color.rgb = COLOR_TEXT_DARK
        p1.space_before = Pt(3)

    # ========================================================
    # SLIDE 4: System Architecture & Technology Stack
    # ========================================================
    slide4 = prs.slides.add_slide(blank_slide_layout)
    add_header(slide4, "System Architecture & End-to-End Pipeline", "03 • ARCHITECTURE & TECH STACK")

    tech_blocks = [
        ("Frontend Application", "Single-Page Portal\n• HTML5 & Tailwind CSS\n• Vanilla ES6+ Engine\n• HTML5 Canvas Exporter\n• Dynamic Modal Editors", COLOR_PRIMARY),
        ("Constraint Engine", "AI Scheduler Core\n• CSP Backtracking\n• Forward Checking\n• Priority Heuristics\n• Workload Equalizer", COLOR_SECONDARY),
        ("Data Layer", "Institutional DB\n• 55 Faculty Profiles\n• 36 Rooms & Labs\n• 8 Dept Curriculums\n• L-T-P-C Course Codes", COLOR_ACCENT),
        ("Python Backend", "Micro-Service\n• BaseHTTP Micro-Server\n• RESTful API Endpoints\n• Automated Test Suite\n• CLI Timetable Generator", COLOR_PRIMARY)
    ]

    for i, (col_title, col_body, col_color) in enumerate(tech_blocks):
        x = Inches(0.8 + i * 2.98)
        col = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.5), Inches(2.8), Inches(4.3))
        col.fill.solid()
        col.fill.fore_color.rgb = COLOR_CARD_BG
        col.line.color.rgb = col_color
        col.line.width = Pt(1.5)

        tb = slide4.shapes.add_textbox(x + Inches(0.15), Inches(1.65), Inches(2.5), Inches(4.0))
        tf = tb.text_frame
        tf.word_wrap = True
        p0 = tf.paragraphs[0]
        p0.text = col_title
        p0.font.size = Pt(15)
        p0.font.bold = True
        p0.font.color.rgb = col_color

        p1 = tf.add_paragraph()
        p1.text = col_body
        p1.font.size = Pt(12)
        p1.font.color.rgb = COLOR_TEXT_DARK
        p1.space_before = Pt(14)

    # Bottom summary banner
    banner = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.0), Inches(11.733), Inches(0.85))
    banner.fill.solid()
    banner.fill.fore_color.rgb = COLOR_PRIMARY
    banner.line.fill.background()

    tb_b = slide4.shapes.add_textbox(Inches(1.0), Inches(6.1), Inches(11.333), Inches(0.65))
    tf_b = tb_b.text_frame
    p_b = tf_b.paragraphs[0]
    p_b.text = "⚡ Zero Runtime Dependencies: Standalone executable app.py with built-in HTTP server, database, and browser client."
    p_b.font.size = Pt(12)
    p_b.font.bold = True
    p_b.font.color.rgb = COLOR_WHITE

    # ========================================================
    # SLIDE 5: AI Scheduling Algorithm & Constraint Satisfaction
    # ========================================================
    slide5 = prs.slides.add_slide(blank_slide_layout)
    add_header(slide5, "AI Scheduling Algorithm & Constraint Formulation", "04 • CORE ALGORITHM")

    # Left: Hard Constraints
    left_card = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.3))
    left_card.fill.solid()
    left_card.fill.fore_color.rgb = COLOR_CARD_BG
    left_card.line.color.rgb = RGBColor(239, 68, 68) # Red accent for Hard constraints
    left_card.line.width = Pt(1.5)

    tb_l = slide5.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(5.3), Inches(5.0))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    p_l0 = tf_l.paragraphs[0]
    p_l0.text = "🔒 Hard Constraints (Strict / Non-Negotiable)"
    p_l0.font.size = Pt(16)
    p_l0.font.bold = True
    p_l0.font.color.rgb = RGBColor(185, 28, 28)

    hard_items = [
        "Faculty Conflict: A faculty cannot be scheduled in 2 places at the same time slot.",
        "Room Clash: A classroom or lab cannot host more than 1 class simultaneously.",
        "Saturday Holiday: Exactly 0 slots booked on Saturdays (Mon-Fri teaching week).",
        "Lunch Break: 12:40 PM - 1:25 PM strictly preserved across all divisions.",
        "Lab Slot Integrity: Practicals require 2 consecutive slots in dedicated labs."
    ]
    for item in hard_items:
        p = tf_l.add_paragraph()
        p.text = f"• {item}"
        p.font.size = Pt(11.5)
        p.font.color.rgb = COLOR_TEXT_DARK
        p.space_before = Pt(8)

    # Right: Soft Constraints & Heuristics
    right_card = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.3))
    right_card.fill.solid()
    right_card.fill.fore_color.rgb = COLOR_CARD_BG
    right_card.line.color.rgb = COLOR_SECONDARY
    right_card.line.width = Pt(1.5)

    tb_r = slide5.shapes.add_textbox(Inches(7.0), Inches(1.65), Inches(5.3), Inches(5.0))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    p_r0 = tf_r.paragraphs[0]
    p_r0.text = "🎯 Soft Constraints & Optimization Heuristics"
    p_r0.font.size = Pt(16)
    p_r0.font.bold = True
    p_r0.font.color.rgb = COLOR_SECONDARY

    soft_items = [
        "HoD Workload Cap: Teaching load capped at 3–6 hrs/week (AICTE administrative quota).",
        "Faculty Equalization: Target 12–16 hrs/week evenly distributed across regular faculty.",
        "Domain Priority Matching: Score bonus (+200) awarded when subject matches professor's verified skill expertise.",
        "Parallel Electives: Concurrent scheduling of PE options in different classrooms at identical periods.",
        "Round-Robin Lab Allocation: Lab hours dynamically allotted to least-loaded faculty first."
    ]
    for item in soft_items:
        p = tf_r.add_paragraph()
        p.text = f"• {item}"
        p.font.size = Pt(11.5)
        p.font.color.rgb = COLOR_TEXT_DARK
        p.space_before = Pt(8)

    # ========================================================
    # SLIDE 6: Balanced Workload Results across 55 Faculty
    # ========================================================
    slide6 = prs.slides.add_slide(blank_slide_layout)
    add_header(slide6, "Faculty Workload Equalization & Subject Distribution", "05 • WORKLOAD EQUALIZATION")

    # 4 Key Metrics Cards on Top
    metrics = [
        ("55 / 55", "Total Faculty Allotted", COLOR_PRIMARY),
        ("0 Members", "Faculty with 0 Subjects", COLOR_SECONDARY),
        ("0 Members", "Faculty with 0 Hours", COLOR_SECONDARY),
        ("100% Balanced", "HoD (4-5h) / Reg (14h)", COLOR_ACCENT)
    ]
    for i, (m_val, m_lbl, m_col) in enumerate(metrics):
        x = Inches(0.8 + i * 2.98)
        card_m = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.5), Inches(2.8), Inches(1.3))
        card_m.fill.solid()
        card_m.fill.fore_color.rgb = COLOR_CARD_BG
        card_m.line.color.rgb = m_col
        card_m.line.width = Pt(1.5)

        tb_m = slide6.shapes.add_textbox(x, Inches(1.6), Inches(2.8), Inches(1.1))
        tf_m = tb_m.text_frame
        p_val = tf_m.paragraphs[0]
        p_val.text = m_val
        p_val.font.size = Pt(20)
        p_val.font.bold = True
        p_val.font.color.rgb = m_col
        p_val.alignment = PP_ALIGN.CENTER

        p_lbl = tf_m.add_paragraph()
        p_lbl.text = m_lbl
        p_lbl.font.size = Pt(10.5)
        p_lbl.font.color.rgb = COLOR_TEXT_MUTED
        p_lbl.alignment = PP_ALIGN.CENTER

    # Department Breakdown Table
    table_shape = slide6.shapes.add_table(9, 5, Inches(0.8), Inches(3.0), Inches(11.733), Inches(3.8))
    table = table_shape.table
    table.columns[0].width = Inches(3.2)
    table.columns[1].width = Inches(1.6)
    table.columns[2].width = Inches(3.4)
    table.columns[3].width = Inches(1.8)
    table.columns[4].width = Inches(1.733)

    headers = ["Department Name", "Faculty Count", "Core Subjects Allotted", "Average Load", "Status"]
    for c_idx, h in enumerate(headers):
        cell = table.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_PRIMARY
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.alignment = PP_ALIGN.CENTER

    dept_rows = [
        ("Computer Engineering (CE)", "13", "DAA, CN, PDS, WD, CG, AJP, DC, CS", "HoD: 4h | Fac: 14h", "✅ Balanced"),
        ("Information Technology (IT)", "13", "AJP, AI, CC, WD, SE, JAVA, PWP, NLP", "HoD: 4h | Fac: 14h", "✅ Balanced"),
        ("Computer Science & Design (CSD)", "2", "CAD, CGD, UI/UX Design", "Fac: 14h", "✅ Balanced"),
        ("AI & Data Science (AIDS)", "1", "Deep Learning, ML Concepts, NLP", "Fac: 14h", "✅ Balanced"),
        ("Mechanical Engineering (ME)", "8", "DME, DOM, HMT, ICE, OR, CAD/CAM, AUT", "HoD: 5h | Fac: 14h", "✅ Balanced"),
        ("Civil Engineering (CL)", "7", "SA-2, DRCS, GE-2, HTE, WRE, EE-1, CT", "HoD: 5h | Fac: 14h", "✅ Balanced"),
        ("Electrical Engineering (EE)", "5", "PS-2, EMD, CS, PE, MCES", "HoD: 5h | Fac: 14h", "✅ Balanced"),
        ("Chemical Engg & ASH (CH + ASH)", "6", "MTO-2, CRE-2, IPC, CT, Open Electives", "HoD: 5h | Fac: 14h", "✅ Balanced")
    ]

    for r_idx, row in enumerate(dept_rows):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx + 1, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_WHITE if r_idx % 2 == 0 else COLOR_CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(10)
            p.font.color.rgb = COLOR_TEXT_DARK
            if c_idx in [1, 3, 4]:
                p.alignment = PP_ALIGN.CENTER

    # ========================================================
    # SLIDE 7: Verification & Experimental Results
    # ========================================================
    slide7 = prs.slides.add_slide(blank_slide_layout)
    add_header(slide7, "Experimental Results & Verification Test Suite", "06 • VERIFICATION & RESULTS")

    test_cards = [
        ("Automated 6/6 Test Suite", [
            "Test 1: All 8 Departments Generated (Div 1 & 2)",
            "Test 2: Zero Faculty Double-Booking Across Institute",
            "Test 3: Inter-Departmental Faculty Pooling Active",
            "Test 4: Saturday Holiday Invariant Verified (0 slots)",
            "Test 5: Parallel Elective Separation Invariant",
            "Test 6: Distinct Laboratory Timing Invariant"
        ]),
        ("Performance & Usability Benchmarks", [
            "Generation Speed: Full 8 departments in < 150 ms",
            "Faculty Workload Variance: Reduced from 42% to 0%",
            "Clash Rate: 0.00% across 560+ period assignments",
            "Export Speed: Real-time high-res PNG & CSV (< 1s)",
            "Browser Compatibility: Chrome, Safari, Firefox, Edge",
            "Responsive UI: Desktop, iPad, and A4 print viewports"
        ])
    ]

    for i, (title, items) in enumerate(test_cards):
        x = Inches(0.8 + i * 5.95)
        card = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.5), Inches(5.7), Inches(5.3))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = COLOR_SECONDARY if i == 0 else COLOR_PRIMARY
        card.line.width = Pt(1.5)

        tb = slide7.shapes.add_textbox(x + Inches(0.2), Inches(1.7), Inches(5.3), Inches(5.0))
        tf = tb.text_frame
        tf.word_wrap = True
        p0 = tf.paragraphs[0]
        p0.text = f"🧪  {title}"
        p0.font.size = Pt(16)
        p0.font.bold = True
        p0.font.color.rgb = COLOR_PRIMARY

        for it in items:
            p = tf.add_paragraph()
            p.text = f"✅  {it}"
            p.font.size = Pt(12)
            p.font.color.rgb = COLOR_TEXT_DARK
            p.space_before = Pt(10)

    # ========================================================
    # SLIDE 8: Conclusion & Future Scope
    # ========================================================
    slide8 = prs.slides.add_slide(blank_slide_layout)
    add_header(slide8, "Conclusion & Future Roadmap", "07 • CONCLUSION & FUTURE WORK")

    concl_cards = [
        ("Key Project Accomplishments", [
            "Transformed a manual, error-prone multi-day scheduling task into an instantaneous 150ms automated process.",
            "Achieved mathematically proven equal workload balancing for all 55 faculty across all 8 branches.",
            "Designed a publication-grade A4 timetable interface featuring full Course Legends, L-T-P-C credits, and signatures."
        ], COLOR_SECONDARY),
        ("Future Roadmap & Innovations", [
            "Student Elective Polling: Real-time student basket selection to adjust class capacities dynamically.",
            "Mobile App & Calendar Sync: Automatic timetable synchronization to Google Calendar & Apple iCal for students.",
            "Classroom IoT Sensor Integration: Dynamic room re-allocation based on live classroom attendance occupancy."
        ], COLOR_ACCENT)
    ]

    for i, (title, items, border_col) in enumerate(concl_cards):
        y = Inches(1.5 + i * 2.3)
        c = slide8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), y, Inches(11.733), Inches(2.1))
        c.fill.solid()
        c.fill.fore_color.rgb = COLOR_CARD_BG
        c.line.color.rgb = border_col
        c.line.width = Pt(1.5)

        tb = slide8.shapes.add_textbox(Inches(1.0), y + Inches(0.15), Inches(11.333), Inches(1.8))
        tf = tb.text_frame
        tf.word_wrap = True
        p0 = tf.paragraphs[0]
        p0.text = f"🌟  {title}"
        p0.font.size = Pt(15)
        p0.font.bold = True
        p0.font.color.rgb = COLOR_PRIMARY

        for it in items:
            p = tf.add_paragraph()
            p.text = f"• {it}"
            p.font.size = Pt(12)
            p.font.color.rgb = COLOR_TEXT_DARK
            p.space_before = Pt(4)

    # Thank you footer card
    t_card = slide8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.15), Inches(11.733), Inches(0.85))
    t_card.fill.solid()
    t_card.fill.fore_color.rgb = COLOR_PRIMARY
    t_card.line.fill.background()

    tb_t = slide8.shapes.add_textbox(Inches(1.0), Inches(6.25), Inches(11.333), Inches(0.65))
    tf_t = tb_t.text_frame
    p_t = tf_t.paragraphs[0]
    p_t.text = "🎉 Thank You! Questions & Discussion Welcome.   |   A. D. Patel Institute of Technology"
    p_t.font.size = Pt(13)
    p_t.font.bold = True
    p_t.font.color.rgb = COLOR_WHITE
    p_t.alignment = PP_ALIGN.CENTER

    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    import os
    out_dir = "/Users/aryandesai/Desktop/project AI"
    out_file = os.path.join(out_dir, "ADIT_AI_Timetable_Presentation.pptx")
    create_presentation(out_file)
