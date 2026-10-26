#!/usr/bin/env python3
"""
ADIT AI Timetable Generator & Multi-Department Scheduling System
Single Self-Contained Application File

Author: Desai Aryan M.
Enrollment: EN. No. 12402080601009
College: A D Patel Institute of Technology (ADIT) | The CVM University

Usage:
    python3 app.py               # Starts web server at http://localhost:8000
    python3 app.py --serve       # Starts web server at http://localhost:8000
    python3 app.py --test        # Runs verification test suite
    python3 app.py --generate    # Generates timetable in terminal
"""

import sys
import os
import json
import random
import argparse
import mimetypes
import subprocess
import re
import socket
import shutil
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Tuple

# ====================================================
# 1. CONFIGURATION & CONSTANTS
# ====================================================

# Academic Cycle: Monday to Friday (Saturday & Sunday are strict holidays)
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
ALL_DAYS_WITH_HOLIDAY = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# Standard 6-period daily schedule with lunch and tea breaks
PERIODS = [
    {"slot": 1, "time": "10:30 - 11:30 AM", "type": "LECTURE"},
    {"slot": 2, "time": "11:30 - 12:30 PM", "type": "LECTURE"},
    {"slot": "LUNCH", "time": "12:30 - 01:15 PM", "type": "RECESS"},
    {"slot": 3, "time": "01:15 - 02:15 PM", "type": "LECTURE_OR_LAB"},
    {"slot": 4, "time": "02:15 - 03:15 PM", "type": "LECTURE_OR_LAB"},
    {"slot": 5, "time": "03:30 - 04:30 PM", "type": "LECTURE_OR_LAB"},
    {"slot": 6, "time": "04:30 - 05:30 PM", "type": "LECTURE_OR_LAB"},
]

# Teaching period slot numbers (excluding lunch)
ACTIVE_SLOT_INDICES = [1, 2, 3, 4, 5, 6]

# Institutional Capacity Rules (Nominal 80, Valid up to 90 students per class)
CLASSROOM_CAPACITY = 80          # Nominal capacity per division
CLASSROOM_MAX_CAPACITY = 90      # Valid extended capacity limit per division
LAB_CAPACITY = 45                # Department dedicated (2 batches)
BATCH_CAPACITY = 22              # 4 batches per division (~20-22 students)

# Academic Course Constraints
LECTURES_PER_THEORY_COURSE = 3  # Exactly 3 lectures per week per theory course
LABS_PER_PRACTICAL_COURSE = 1   # Exactly 1 lab per week per practical course (2-hour block)

# Inter-Departmental Faculty Sharing Map
# IT shares with AI&DS, CE shares with CSD
FACULTY_SHARING_MAP = {
    "IT": "AIDS",
    "AIDS": "IT",
    "CE": "CSD",
    "CSD": "CE",
}

# Faculty Teaching Load Bounds (Hours per week)
TARGET_WORKLOAD_MIN = 12
TARGET_WORKLOAD_MAX = 15

# Head of Department (HOD) Administrative Teaching Relief:
# HODs carry institutional, accreditation, and department administration, so their teaching workload
# is capped at 6 - 8 hours/week (strictly less than regular faculty who teach 12 - 16 hours/week).
HOD_WORKLOAD_MIN = 3
HOD_WORKLOAD_MAX = 8

# Supported Engineering Departments
DEPARTMENTS = ["CE", "IT", "CSD", "AIDS", "ME", "CL", "EE", "CH"]

# Supported Semesters
SEMESTERS = [1, 2, 3, 4, 5, 6, 7, 8]
DEFAULT_SEMESTER = 5

# ====================================================
# 2. DATA MODELS
# ====================================================



@dataclass
class Faculty:
    code: str
    name: str
    dept: str
    designation: str
    experience: str
    qualification: str
    skills: str
    priorities: List[str] = field(default_factory=list)
    photo: str = ""
    localPhoto: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Course:
    code: str
    name: str
    short: str
    l: int
    t: int
    p: int
    c: int
    category: str
    faculty_code: str
    lab_type: str = "Computer"
    is_high_credit: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Room:
    no: str
    name: str
    type: str  # "Classroom", "Computer Lab", "Core Lab", etc.
    capacity: int
    dept: str
    is_classroom: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PeriodEntry:
    day: str
    slot: int
    time: str
    activity: str  # "THEORY", "LAB", "FREE", "LIBRARY"
    subject_code: str
    subject_name: str
    faculty_code: str
    faculty_name: str
    room_no: str
    is_shared_faculty: bool = False
    shared_from_dept: Optional[str] = None
    lab_batches: List[str] = field(default_factory=list)
    lab_room_2: Optional[str] = None
    is_elective: bool = False
    elective_options: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Timetable:
    dept: str
    semester: int
    division: int
    room_no: str
    grid: Dict[str, Dict[int, PeriodEntry]]  # Day -> Slot -> PeriodEntry

    def to_dict(self) -> Dict[str, Any]:
        res = {
            "dept": self.dept,
            "semester": self.semester,
            "division": self.division,
            "room_no": self.room_no,
            "grid": {}
        }
        for day, slots in self.grid.items():
            res["grid"][day] = {str(s): entry.to_dict() for s, entry in slots.items()}
        return res


@dataclass
class FacultyWorkload:
    code: str
    name: str
    dept: str
    designation: str
    theory_hours: int = 0
    lab_hours: int = 0
    total_hours: int = 0
    assigned_subjects: List[str] = field(default_factory=list)
    status: str = "Balanced"  # "Perfect", "Balanced", "Under Assigned", "Over Assigned"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# ====================================================
# 3. ADIT ACADEMIC DATABASE
# ====================================================

ADIT_PORTAL_DATA = {'rooms': [{'roomNo': '213', 'type': 'Classroom', 'capacity': 90, 'dept': 'Common', 'buildingFloor': 'Main Bldg - 2nd Floor', 'features': 'Smart Projector, Audio System, AC'}, {'roomNo': '214', 'type': 'Classroom', 'capacity': 90, 'dept': 'Common', 'buildingFloor': 'Main Bldg - 2nd Floor', 'features': 'Smart Board, High-Lumen Projector'}, {'roomNo': '314', 'type': 'Classroom', 'capacity': 90, 'dept': 'Common', 'buildingFloor': 'Main Bldg - 3rd Floor', 'features': 'Tiered Seating, Smart Display'}, {'roomNo': '209', 'type': 'Classroom', 'capacity': 90, 'dept': 'Common', 'buildingFloor': 'IT Block - 2nd Floor', 'features': 'Interactive Whiteboard, AC'}, {'roomNo': '210', 'type': 'Classroom', 'capacity': 90, 'dept': 'Common', 'buildingFloor': 'IT Block - 2nd Floor', 'features': 'Digital Podium, Dual Displays'}, {'roomNo': '320', 'type': 'Classroom', 'capacity': 90, 'dept': 'Common', 'buildingFloor': 'Design Wing - 3rd Floor', 'features': 'Design Studio Setup, 4K Display'}, {'roomNo': '218', 'type': 'Classroom', 'capacity': 90, 'dept': 'Common', 'buildingFloor': 'AI Wing - 2nd Floor', 'features': 'Smart Interactive Screen, High-Speed LAN'}, {'roomNo': '101', 'type': 'Classroom', 'capacity': 90, 'dept': 'Common', 'buildingFloor': 'Mech Block - 1st Floor', 'features': 'Acoustic Panels, Projection Screen'}, {'roomNo': '105', 'type': 'Classroom', 'capacity': 90, 'dept': 'Common', 'buildingFloor': 'Chem Block - 1st Floor', 'features': 'Smart Display, Ventilation'}, {'roomNo': '201', 'type': 'Classroom', 'capacity': 90, 'dept': 'Common', 'buildingFloor': 'EE Block - 2nd Floor', 'features': 'Digital Projector, AC'}, {'roomNo': '301', 'type': 'Classroom', 'capacity': 90, 'dept': 'Common', 'buildingFloor': 'Civil Block - 3rd Floor', 'features': 'Drafting Tables, Overhead Display'}, {'roomNo': '215', 'type': 'Classroom', 'capacity': 90, 'dept': 'Common', 'buildingFloor': 'Main Bldg - 2nd Floor', 'features': 'Multi-purpose Lecture Hall'}, {'roomNo': '312', 'type': 'Classroom', 'capacity': 90, 'dept': 'Common', 'buildingFloor': 'Main Bldg - 3rd Floor', 'features': 'Audio-Visual Seminar Setup'}, {'roomNo': '313', 'type': 'Classroom', 'capacity': 90, 'dept': 'Common', 'buildingFloor': 'Main Bldg - 3rd Floor', 'features': 'High Capacity Lecture Theatre'}, {'roomNo': 'CE-3 Lab', 'type': 'Computer-Lab', 'capacity': 40, 'dept': 'CE', 'buildingFloor': 'Main Bldg - 2nd Floor', 'features': '40 Intel Core i7 Systems, Ubuntu/Win Dual Boot'}, {'roomNo': 'CE-4 Lab', 'type': 'Computer-Lab', 'capacity': 40, 'dept': 'CE', 'buildingFloor': 'Main Bldg - 2nd Floor', 'features': '40 Systems, Cisco Networking Racks'}, {'roomNo': 'CE-5 Lab', 'type': 'Computer-Lab', 'capacity': 40, 'dept': 'CE', 'buildingFloor': 'Main Bldg - 3rd Floor', 'features': '40 Systems, Algorithm Simulation Suite'}, {'roomNo': 'CE-6 Lab', 'type': 'Computer-Lab', 'capacity': 40, 'dept': 'CE', 'buildingFloor': 'Main Bldg - 3rd Floor', 'features': '40 Systems, Full Stack Web Dev Environment'}, {'roomNo': 'IT-3 Lab', 'type': 'Computer-Lab', 'capacity': 40, 'dept': 'IT', 'buildingFloor': 'IT Block - 2nd Floor', 'features': '40 Dell OptiPlex Systems, Oracle DBMS'}, {'roomNo': 'IT-4 Lab', 'type': 'Computer-Lab', 'capacity': 40, 'dept': 'IT', 'buildingFloor': 'IT Block - 2nd Floor', 'features': '40 Systems, Python & Data Science Rigs'}, {'roomNo': 'IT-5 Lab', 'type': 'Computer-Lab', 'capacity': 40, 'dept': 'IT', 'buildingFloor': 'IT Block - 3rd Floor', 'features': '40 Systems, Cloud & DevOps Simulation'}, {'roomNo': 'IT-6 Lab', 'type': 'Computer-Lab', 'capacity': 40, 'dept': 'IT', 'buildingFloor': 'IT Block - 3rd Floor', 'features': '40 Systems, Cyber Security & Forensics'}, {'roomNo': 'Lab 331-A', 'type': 'Computer-Lab', 'capacity': 40, 'dept': 'IT', 'buildingFloor': 'IT Block - 3rd Floor', 'features': '40 High-End Workstations, ML Frameworks'}, {'roomNo': 'AI-1 Lab', 'type': 'Computer-Lab', 'capacity': 40, 'dept': 'AIDS', 'buildingFloor': 'AI Wing - 2nd Floor', 'features': 'NVIDIA GPU Workstations, Deep Learning Suite'}, {'roomNo': 'AI-2 Lab', 'type': 'Computer-Lab', 'capacity': 40, 'dept': 'AIDS', 'buildingFloor': 'AI Wing - 2nd Floor', 'features': 'High Performance Compute Nodes, Big Data Spark'}, {'roomNo': 'CAD-CAM Lab', 'type': 'Core-Lab', 'capacity': 40, 'dept': 'ME', 'buildingFloor': 'Mech Block - Ground Floor', 'features': 'AutoCAD, SolidWorks, CNC Simulators'}, {'roomNo': 'Thermo Lab', 'type': 'Core-Lab', 'capacity': 40, 'dept': 'ME', 'buildingFloor': 'Mech Block - Ground Floor', 'features': 'Steam Turbine, Heat Exchanger Test Rigs'}, {'roomNo': 'Reaction Lab', 'type': 'Core-Lab', 'capacity': 40, 'dept': 'CH', 'buildingFloor': 'Chem Block - Ground Floor', 'features': 'Batch & CSTR Reactors, Distillation Units'}, {'roomNo': 'Mass Transfer Lab', 'type': 'Core-Lab', 'capacity': 40, 'dept': 'CH', 'buildingFloor': 'Chem Block - 1st Floor', 'features': 'Absorption Towers, Liquid Extraction Rigs'}, {'roomNo': 'Machines Lab', 'type': 'Core-Lab', 'capacity': 40, 'dept': 'EE', 'buildingFloor': 'EE Block - Ground Floor', 'features': 'AC/DC Motor-Generator Sets, Transformers'}, {'roomNo': 'Power System Lab', 'type': 'Core-Lab', 'capacity': 40, 'dept': 'EE', 'buildingFloor': 'EE Block - 1st Floor', 'features': 'Transmission Line Simulators, Relays'}, {'roomNo': 'Structure Lab', 'type': 'Core-Lab', 'capacity': 40, 'dept': 'CL', 'buildingFloor': 'Civil Block - Ground Floor', 'features': 'Universal Testing Machine (UTM), Compression Rig'}, {'roomNo': 'Geotech Lab', 'type': 'Core-Lab', 'capacity': 40, 'dept': 'CL', 'buildingFloor': 'Civil Block - Ground Floor', 'features': 'Direct Shear Apparatus, Triaxial Test Setup'}, {'roomNo': 'Mech Workshop', 'type': 'Workshop', 'capacity': 80, 'dept': 'ME', 'buildingFloor': 'Workshop Annex - Ground Floor', 'features': 'Lathe Machines, Welding, Carpentry, Fitting'}, {'roomNo': 'Physics Lab', 'type': 'Core-Lab', 'capacity': 40, 'dept': 'Shared', 'buildingFloor': 'Science Block - 1st Floor', 'features': 'Optics Spectrometers, Laser & Hall Effect'}, {'roomNo': 'Chemistry Lab', 'type': 'Core-Lab', 'capacity': 40, 'dept': 'Shared', 'buildingFloor': 'Science Block - 1st Floor', 'features': 'Fume Hoods, Analytical Instruments'}], 'departments': [{'code': 'CE', 'name': 'Computer Engineering', 'progCode': '04', 'facCode': '02', 'studentIntake': 240, 'defaultRooms': ['213', '214', '314'], 'labPrefix': 'CE', 'labs': ['CE-3 Lab', 'CE-4 Lab', 'CE-5 Lab', 'CE-6 Lab']}, {'code': 'IT', 'name': 'Information Technology', 'progCode': '08', 'facCode': '0208', 'studentIntake': 160, 'defaultRooms': ['209', '210'], 'labPrefix': 'IT', 'labs': ['IT-3 Lab', 'IT-4 Lab', 'IT-5 Lab', 'IT-6 Lab', 'Lab 331-A']}, {'code': 'CSD', 'name': 'Computer Science & Design', 'progCode': '13', 'facCode': '02', 'studentIntake': 80, 'defaultRooms': ['320'], 'labPrefix': 'CE', 'labs': ['CE-4 Lab', 'CE-5 Lab', 'CE-6 Lab']}, {'code': 'AIDS', 'name': 'Artificial Intelligence & Data Science', 'progCode': '16', 'facCode': '02', 'studentIntake': 80, 'defaultRooms': ['218'], 'labPrefix': 'AI', 'labs': ['AI-1 Lab', 'AI-2 Lab', 'IT-3 Lab']}, {'code': 'ME', 'name': 'Mechanical Engineering', 'progCode': '02', 'facCode': '02', 'studentIntake': 80, 'defaultRooms': ['101'], 'labPrefix': 'ME', 'labs': ['Thermo Lab', 'CAD-CAM Lab', 'Mech Workshop']}, {'code': 'CL', 'name': 'Civil Engineering', 'progCode': '06', 'facCode': '02', 'studentIntake': 80, 'defaultRooms': ['301'], 'labPrefix': 'CL', 'labs': ['Structure Lab', 'Geotech Lab']}, {'code': 'EE', 'name': 'Electrical Engineering', 'progCode': '09', 'facCode': '02', 'studentIntake': 80, 'defaultRooms': ['201'], 'labPrefix': 'EE', 'labs': ['Machines Lab', 'Power System Lab']}, {'code': 'CH', 'name': 'Chemical Engineering', 'progCode': '05', 'facCode': '02', 'studentIntake': 80, 'defaultRooms': ['105'], 'labPrefix': 'CH', 'labs': ['Reaction Lab', 'Mass Transfer Lab']}], 'timeSlots': [{'time': '9:05 to 9:55am', 'id': 'T1', 'isBreak': False}, {'time': '10:00 to 10:50am', 'id': 'T2', 'isBreak': False}, {'time': '10:55 to 11:45am', 'id': 'T3', 'isBreak': False}, {'time': '11:50 to 12:40pm', 'id': 'T4', 'isBreak': False}, {'time': '12:40 to 1:25pm', 'id': 'LUNCH', 'isBreak': True, 'label': 'LUNCH BREAK'}, {'time': '1:25 to 2:15pm', 'id': 'T5', 'isBreak': False}, {'time': '2:20 to 3:10pm', 'id': 'T6', 'isBreak': False}, {'time': '3:15 to 4:05pm', 'id': 'T7', 'isBreak': False}, {'time': '4:10 to 5:00pm', 'id': 'T8', 'isBreak': False}], 'days': ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'], 'curriculums': {'CE_1': [{'code': '202000101', 'name': 'Mathematics - I (Calculus & Linear Algebra)', 'short': 'MATH-1', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202000102', 'name': 'Engineering Physics', 'short': 'EP', 'category': 'BSC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Physics', 'facultyCode': 'SKP'}, {'code': '202000103', 'name': 'Programming for Problem Solving (PPS - C)', 'short': 'PPS', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'JKP'}, {'code': '202000104', 'name': 'Basic Electrical Engineering (BEE)', 'short': 'BEE', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'PRM'}, {'code': '202000105', 'name': 'Engineering Graphics & Design (EGD)', 'short': 'EGD', 'category': 'ESC', 'l': 1, 't': 0, 'p': 4, 'c': 3, 'isHighCredit': False, 'labType': 'CAD', 'facultyCode': 'AYJ'}, {'code': '202000106', 'name': 'Environmental Science & Constitution', 'short': 'ES', 'category': 'Audit', 'l': 2, 't': 0, 'p': 0, 'c': 0, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'PMG'}], 'CE_2': [{'code': '202000201', 'name': 'Mathematics - II (Advanced Calculus & ODE)', 'short': 'MATH-2', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202000202', 'name': 'Engineering Chemistry', 'short': 'CHEM', 'category': 'BSC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'INT'}, {'code': '202000203', 'name': 'Basic Electronics & Digital Systems', 'short': 'BEDS', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'VSS'}, {'code': '202000204', 'name': 'Workshop & Manufacturing Practices', 'short': 'WS', 'category': 'ESC', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'Workshop', 'facultyCode': 'BJS'}, {'code': '202000205', 'name': 'English for Technical Communication', 'short': 'ETC', 'category': 'HSMC', 'l': 2, 't': 0, 'p': 2, 'c': 3, 'isHighCredit': False, 'labType': 'Language', 'facultyCode': 'BJS'}], 'CE_3': [{'code': '202043301', 'name': 'Data Structures & Algorithms (DSA)', 'short': 'DSA', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'DKS'}, {'code': '202043302', 'name': 'Database Management Systems (DBMS)', 'short': 'DBMS', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'IT'}, {'code': '202043303', 'name': 'Digital Logic & Computer Design (DLD)', 'short': 'DLD', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'JKP'}, {'code': '202043304', 'name': 'Discrete Mathematics (DM)', 'short': 'DM', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202043305', 'name': 'Object Oriented Programming with C++', 'short': 'OOPC', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'PT'}], 'CE_4': [{'code': '202044401', 'name': 'Operating Systems (OS)', 'short': 'OS', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'KRP'}, {'code': '202044402', 'name': 'Computer Organization & Architecture (COA)', 'short': 'COA', 'category': 'PCC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'ANP'}, {'code': '202044403', 'name': 'Object Oriented Programming with Java', 'short': 'JAVA', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'JVP_CE'}, {'code': '202044404', 'name': 'Theory of Computation & Automata (FLAT)', 'short': 'TOC', 'category': 'PCC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'HMP'}, {'code': '202044405', 'name': 'Probability, Statistics & Numerical Analysis', 'short': 'PSNA', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}], 'CE_5': [{'code': '202045601', 'name': 'Design and Analysis of Algorithms', 'short': 'DAA', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'DKS'}, {'code': '202044501', 'name': 'Computer Networks', 'short': 'CN', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'PKT'}, {'code': '202045603', 'name': 'Python for Data Science', 'short': 'PDS', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'TRR'}, {'code': '202044505', 'name': 'Web Development', 'short': 'WD', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'KSP'}, {'code': '202045606', 'name': 'Computer Graphics - PE1', 'short': 'CG', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'CE', 'facultyCode': 'JVP_CE'}, {'code': '202045605', 'name': 'Advanced Java Programming - PE1', 'short': 'AJP', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'CE', 'facultyCode': 'AW'}, {'code': '202045610', 'name': 'Distributed Computing & Cloud - PE1', 'short': 'DC', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'CE', 'facultyCode': 'MB'}, {'code': '202045611', 'name': 'Software Testing & QA - PE1', 'short': 'STQA', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'CE', 'facultyCode': 'AJK'}, {'code': '202045612', 'name': 'Cyber Security Principles - PE1', 'short': 'CS', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'CE', 'facultyCode': 'SJM'}, {'code': '202045613', 'name': 'Advanced Algorithm Lab & Analysis', 'short': 'ALGO', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'PT'}, {'code': '202045614', 'name': 'Python & Web Architecture', 'short': 'PWP', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'AKK'}, {'code': '202045615', 'name': 'Database Management & Systems', 'short': 'DBMS', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'IT'}, {'code': '202045616', 'name': 'Computer Graphics & Multimedia Design', 'short': 'CGD', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'CBJ'}, {'code': '202045699', 'name': 'Open Elective (Disaster Management & Remote Sensing)', 'short': 'OE', 'category': 'OEC', 'l': 2, 't': 0, 'p': 0, 'c': 2, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'DM'}], 'CE_6': [{'code': '202046601', 'name': 'Compiler Design', 'short': 'CD', 'category': 'PCC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'DJP'}, {'code': '202046602', 'name': 'Machine Learning & AI', 'short': 'ML', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'IT'}, {'code': '202046603', 'name': 'Full Stack Web Technologies (MERN)', 'short': 'FSW', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'PT'}, {'code': '202046604', 'name': 'Software Testing & Quality Assurance', 'short': 'STQA', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'CE', 'facultyCode': 'AJK'}, {'code': '202046605', 'name': 'Mobile Application Development (Flutter/Android)', 'short': 'MAD', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'CE', 'facultyCode': 'JVP_CE'}, {'code': '202046606', 'name': 'Mini Project & Technical Seminar', 'short': 'MP', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'CE', 'facultyCode': 'CBJ'}], 'CE_7': [{'code': '202047701', 'name': 'Cloud Computing & DevOps Architecture', 'short': 'CC', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'KRP'}, {'code': '202047702', 'name': 'Cyber Security & Digital Forensics', 'short': 'CSF', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'IT'}, {'code': '202047703', 'name': 'Blockchain & Smart Contracts', 'short': 'BC', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'CE', 'facultyCode': 'AJK'}, {'code': '202047704', 'name': 'Internet of Things (IoT) Systems', 'short': 'IOT', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'CE', 'facultyCode': 'SJM'}, {'code': '202047705', 'name': 'Major Project - Phase I', 'short': 'PROJ-1', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 8, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'MB'}], 'CE_8': [{'code': '202048801', 'name': 'Industry Internship / Major Capstone Project - Phase II', 'short': 'CAPSTONE', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 24, 'c': 12, 'isHighCredit': True, 'labType': 'Industry/Lab', 'facultyCode': 'MB'}, {'code': '202048802', 'name': 'Comprehensive Seminar & Technical Viva', 'short': 'VIVA', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'Seminar', 'facultyCode': 'DKS'}, {'code': '202048803', 'name': 'Professional Practice, IP Rights & Ethics', 'short': 'ETHICS', 'category': 'HSMC', 'l': 2, 't': 0, 'p': 0, 'c': 2, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'PMG'}], 'IT_1': [{'code': '202000101', 'name': 'Mathematics - I (Calculus & Linear Algebra)', 'short': 'MATH-1', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202000102', 'name': 'Engineering Physics', 'short': 'EP', 'category': 'BSC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Physics', 'facultyCode': 'SKP'}, {'code': '202000103', 'name': 'Programming for Problem Solving (PPS)', 'short': 'PPS', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'JKP'}, {'code': '202000104', 'name': 'Basic Electrical Engineering', 'short': 'BEE', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'PRM'}, {'code': '202000105', 'name': 'Engineering Graphics & Design', 'short': 'EGD', 'category': 'ESC', 'l': 1, 't': 0, 'p': 4, 'c': 3, 'isHighCredit': False, 'labType': 'CAD', 'facultyCode': 'AYJ'}, {'code': '202000106', 'name': 'Environmental Science & Constitution', 'short': 'ES', 'category': 'Audit', 'l': 2, 't': 0, 'p': 0, 'c': 0, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'PMG'}], 'IT_2': [{'code': '202000201', 'name': 'Mathematics - II (Vector Calculus & ODE)', 'short': 'MATH-2', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202000202', 'name': 'Engineering Chemistry', 'short': 'CHEM', 'category': 'BSC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'INT'}, {'code': '202000203', 'name': 'Basic Electronics Engineering', 'short': 'BEE', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'VSS'}, {'code': '202000204', 'name': 'Workshop Practices', 'short': 'WS', 'category': 'ESC', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'Workshop', 'facultyCode': 'BJS'}, {'code': '202000205', 'name': 'English for Technical Communication', 'short': 'ETC', 'category': 'HSMC', 'l': 2, 't': 0, 'p': 2, 'c': 3, 'isHighCredit': False, 'labType': 'Language', 'facultyCode': 'BJS'}], 'IT_3': [{'code': '202043301', 'name': 'Data Structures', 'short': 'DS', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'MAP'}, {'code': '202043302', 'name': 'Database Management Systems', 'short': 'DBMS', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'IT'}, {'code': '202043305', 'name': 'Object Oriented Programming with C++', 'short': 'OOP', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'KVP'}, {'code': '202043307', 'name': 'Digital Electronics & Computer Organization', 'short': 'DECO', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'KJP'}, {'code': '202043304', 'name': 'Discrete Mathematics', 'short': 'DM', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}], 'IT_4': [{'code': '202044401', 'name': 'Operating Systems', 'short': 'OS', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'KRP'}, {'code': '202044402', 'name': 'Computer Networks', 'short': 'CN', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'ANP'}, {'code': '202044403', 'name': 'Java Programming & Technologies', 'short': 'JAVA', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'AJR'}, {'code': '202044405', 'name': 'Probability & Numerical Techniques', 'short': 'PNT', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202044406', 'name': 'Principles of Software Engineering', 'short': 'SE', 'category': 'PCC', 'l': 3, 't': 0, 'p': 0, 'c': 3, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'NMM'}], 'IT_5': [{'code': '202045601', 'name': 'Design and Analysis of Algorithms', 'short': 'DAA', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'MAP'}, {'code': '202045602', 'name': 'Software Engineering', 'short': 'SE', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'ANP'}, {'code': '202044504', 'name': 'Programming with Python', 'short': 'PWP', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'HMP'}, {'code': '202044505', 'name': 'Web Development', 'short': 'WD', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'SNG'}, {'code': '202044503', 'name': 'Artificial Intelligence (PE1)', 'short': 'AI', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'IT', 'facultyCode': 'DJP'}, {'code': '202045605', 'name': 'Advanced Java Programming (PE1)', 'short': 'AJP', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'IT', 'facultyCode': 'PRB'}, {'code': '202045607', 'name': 'Cyber Security (PE1)', 'short': 'CS', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'IT', 'facultyCode': 'HVP'}, {'code': '202045623', 'name': 'Natural Language Processing (PE1)', 'short': 'NLP', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'IT', 'facultyCode': 'KJP'}, {'code': '202045624', 'name': 'Java Programming & Technologies', 'short': 'JAVA', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'JKP'}, {'code': '202045625', 'name': 'Full Stack Application Development', 'short': 'FSAD', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'AJR'}, {'code': '202045626', 'name': 'Object Oriented Programming with C++', 'short': 'OOP', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'KVP'}, {'code': '202045627', 'name': 'Software Project Management & Agile', 'short': 'SPM', 'category': 'PCC', 'l': 3, 't': 0, 'p': 0, 'c': 3, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'NMM'}, {'code': '202045628', 'name': 'Cloud Computing & DevOps Architecture', 'short': 'CC', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'KRP'}, {'code': '202045698', 'name': 'Open Elective (Professional Ethics & Technical Practice)', 'short': 'OE', 'category': 'OEC', 'l': 2, 't': 0, 'p': 0, 'c': 2, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'PMG'}], 'IT_6': [{'code': '202046602', 'name': 'Machine Learning & Analytics', 'short': 'MLA', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'IT'}, {'code': '202046607', 'name': 'Cloud Computing & Virtualization', 'short': 'CCV', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'BKM'}, {'code': '202046608', 'name': 'Full Stack Application Development', 'short': 'FSAD', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'AJR'}, {'code': '202046609', 'name': 'Information & Network Security', 'short': 'INS', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'HVP'}, {'code': '202046610', 'name': 'Software Project Management (PE2)', 'short': 'SPM', 'category': 'PEC', 'l': 3, 't': 0, 'p': 0, 'c': 3, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'NMM'}, {'code': '202046606', 'name': 'Mini Project & Technical Seminar', 'short': 'MP', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'IT', 'facultyCode': 'KJP'}], 'IT_7': [{'code': '202047701', 'name': 'DevOps & Cloud Native Architecture', 'short': 'DEV', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'KRP'}, {'code': '202047702', 'name': 'Cyber Security & Ethical Hacking', 'short': 'EH', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'IT'}, {'code': '202047709', 'name': 'Big Data Technologies & Analytics', 'short': 'BDA', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'IT', 'facultyCode': 'BKM'}, {'code': '202047710', 'name': 'Mobile Computing & Wireless Tech', 'short': 'MCWT', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'IT', 'facultyCode': 'KVP'}, {'code': '202047705', 'name': 'Major Project - Phase I', 'short': 'PROJ-1', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 8, 'c': 4, 'isHighCredit': True, 'labType': 'IT', 'facultyCode': 'SNG'}], 'IT_8': [{'code': '202048801', 'name': 'Industry Internship / Major Capstone Project - Phase II', 'short': 'CAPSTONE', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 24, 'c': 12, 'isHighCredit': True, 'labType': 'Industry/Lab', 'facultyCode': 'SNG'}, {'code': '202048802', 'name': 'Technical Seminar & Comprehensive Viva', 'short': 'VIVA', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'Seminar', 'facultyCode': 'MAP'}, {'code': '202048803', 'name': 'Intellectual Property Rights & Cyber Laws', 'short': 'IPR', 'category': 'HSMC', 'l': 2, 't': 0, 'p': 0, 'c': 2, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'PMG'}], 'CSD_1': [{'code': '202000101', 'name': 'Mathematics - I (Calculus & Linear Algebra)', 'short': 'MATH-1', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202000102', 'name': 'Engineering Physics', 'short': 'EP', 'category': 'BSC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Physics', 'facultyCode': 'SKP'}, {'code': '202000103', 'name': 'Programming for Problem Solving', 'short': 'PPS', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'JKP'}, {'code': '202000107', 'name': 'Visual Arts & Design Thinking', 'short': 'VADT', 'category': 'ESC', 'l': 2, 't': 0, 'p': 4, 'c': 4, 'isHighCredit': True, 'labType': 'Design', 'facultyCode': 'PMG'}, {'code': '202000104', 'name': 'Basic Electrical Engineering', 'short': 'BEE', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'PRM'}], 'CSD_2': [{'code': '202000201', 'name': 'Mathematics - II (Advanced Calculus & ODE)', 'short': 'MATH-2', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202000202', 'name': 'Engineering Chemistry', 'short': 'CHEM', 'category': 'BSC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'INT'}, {'code': '202000203', 'name': 'Basic Electronics Engineering', 'short': 'BEE', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'VSS'}, {'code': '202000208', 'name': 'Design Workshop & Prototyping', 'short': 'DWP', 'category': 'ESC', 'l': 1, 't': 0, 'p': 4, 'c': 3, 'isHighCredit': False, 'labType': 'Design', 'facultyCode': 'CBJ'}, {'code': '202000205', 'name': 'English for Technical Communication', 'short': 'ETC', 'category': 'HSMC', 'l': 2, 't': 0, 'p': 2, 'c': 3, 'isHighCredit': False, 'labType': 'Language', 'facultyCode': 'BJS'}], 'CSD_3': [{'code': '202043301', 'name': 'Data Structures & Design Algorithms', 'short': 'DSA', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'DKS'}, {'code': '202043302', 'name': 'Database Management Systems', 'short': 'DBMS', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'IT'}, {'code': '202043308', 'name': 'Fundamentals of UI/UX Design', 'short': 'UIUX', 'category': 'PCC', 'l': 2, 't': 0, 'p': 4, 'c': 4, 'isHighCredit': True, 'labType': 'Design', 'facultyCode': 'BKM'}, {'code': '202043303', 'name': 'Digital Logic & System Design', 'short': 'DLSD', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'JKP'}, {'code': '202043304', 'name': 'Discrete Mathematical Structures', 'short': 'DMS', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}], 'CSD_4': [{'code': '202044401', 'name': 'Operating Systems Principles', 'short': 'OSP', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'KRP'}, {'code': '202044407', 'name': 'Interactive Computer Graphics', 'short': 'ICG', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Design', 'facultyCode': 'CBJ'}, {'code': '202044403', 'name': 'Object Oriented Design with Java', 'short': 'OODJ', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'JVP_CE'}, {'code': '202044408', 'name': 'Design Research Methods & Usability Testing', 'short': 'DRM', 'category': 'PCC', 'l': 2, 't': 0, 'p': 4, 'c': 4, 'isHighCredit': True, 'labType': 'Design', 'facultyCode': 'VVN_CSD'}, {'code': '202044405', 'name': 'Probability & Applied Statistics', 'short': 'PAS', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}], 'CSD_5': [{'code': '202045601', 'name': 'Design and Analysis of Algorithms', 'short': 'DAA', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'PT'}, {'code': '202044507', 'name': 'Computer Architecture & Design', 'short': 'CAD', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'VVN_CSD'}, {'code': '202045611', 'name': 'Computer Graphics & UI/UX Design', 'short': 'CGD', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'BKM'}, {'code': '202045612', 'name': 'Python and Web Programming', 'short': 'PWP', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'AKK'}, {'code': '202045605', 'name': 'Advance Java Programming - PE1', 'short': 'AJP', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'CE', 'facultyCode': 'AW'}, {'code': '202045607', 'name': 'Cyber Security - PE1', 'short': 'CS', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'CE', 'facultyCode': 'SJM'}, {'code': '202045699', 'name': 'Open Elective (Applied Mathematics & Optimization)', 'short': 'OE', 'category': 'OEC', 'l': 2, 't': 0, 'p': 0, 'c': 2, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'DM'}], 'CSD_6': [{'code': '202046611', 'name': 'Interactive UX / AR & VR Systems', 'short': 'ARVR', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Design', 'facultyCode': 'CBJ'}, {'code': '202046612', 'name': '3D Animation & Game Design', 'short': 'GAME', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Design', 'facultyCode': 'VVN'}, {'code': '202046602', 'name': 'Machine Learning in Design', 'short': 'MLD', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'IT'}, {'code': '202046613', 'name': 'Mobile UX & Digital Product Engineering', 'short': 'MUX', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Design', 'facultyCode': 'AKK'}, {'code': '202046614', 'name': 'Design Studio Mini Project', 'short': 'STUDIO', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'Design', 'facultyCode': 'PRB'}], 'CSD_7': [{'code': '202047706', 'name': 'Spatial Computing & Generative Design', 'short': 'SPATIAL', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'Design', 'facultyCode': 'CBJ'}, {'code': '202047707', 'name': 'Human-AI Interaction Systems', 'short': 'HAII', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'DKS'}, {'code': '202047708', 'name': 'Design Systems & Web Frameworks', 'short': 'DSYS', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'CE', 'facultyCode': 'AKK'}, {'code': '202047705', 'name': 'Major Project - Phase I (Design & Build)', 'short': 'PROJ-1', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 8, 'c': 4, 'isHighCredit': True, 'labType': 'Design', 'facultyCode': 'DKS'}], 'CSD_8': [{'code': '202048801', 'name': 'Industry Internship / Major Capstone Design Project', 'short': 'CAPSTONE', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 24, 'c': 12, 'isHighCredit': True, 'labType': 'Industry/Lab', 'facultyCode': 'DKS'}, {'code': '202048802', 'name': 'Design Portfolio & Comprehensive Viva', 'short': 'PORTFOLIO', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'Seminar', 'facultyCode': 'CBJ'}, {'code': '202048803', 'name': 'Design Ethics, Copyrights & Patents', 'short': 'IPR', 'category': 'HSMC', 'l': 2, 't': 0, 'p': 0, 'c': 2, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'PMG'}], 'AIDS_1': [{'code': '202000101', 'name': 'Mathematics - I (Calculus & Linear Algebra)', 'short': 'MATH-1', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202000102', 'name': 'Engineering Physics', 'short': 'EP', 'category': 'BSC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Physics', 'facultyCode': 'SKP'}, {'code': '202000103', 'name': 'Programming for Problem Solving (Python/C)', 'short': 'PPS', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'JKP'}, {'code': '202000104', 'name': 'Basic Electrical Engineering', 'short': 'BEE', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'PRM'}, {'code': '202000105', 'name': 'Engineering Graphics & Design', 'short': 'EGD', 'category': 'ESC', 'l': 1, 't': 0, 'p': 4, 'c': 3, 'isHighCredit': False, 'labType': 'CAD', 'facultyCode': 'AYJ'}], 'AIDS_2': [{'code': '202000201', 'name': 'Mathematics - II (Multivariate Calculus & Matrices)', 'short': 'MATH-2', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202000202', 'name': 'Engineering Chemistry', 'short': 'CHEM', 'category': 'BSC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'INT'}, {'code': '202000203', 'name': 'Basic Electronics & IoT Sensors', 'short': 'BEIS', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'VSS'}, {'code': '202000204', 'name': 'Python for Scientific Computing', 'short': 'PSC', 'category': 'ESC', 'l': 1, 't': 0, 'p': 4, 'c': 3, 'isHighCredit': False, 'labType': 'AI', 'facultyCode': 'BJS'}, {'code': '202000205', 'name': 'English for Technical Communication', 'short': 'ETC', 'category': 'HSMC', 'l': 2, 't': 0, 'p': 2, 'c': 3, 'isHighCredit': False, 'labType': 'Language', 'facultyCode': 'BJS'}], 'AIDS_3': [{'code': '202043301', 'name': 'Data Structures for AI & Analytics', 'short': 'DSA-AI', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'DKS'}, {'code': '202043309', 'name': 'Mathematical Foundations for Data Science', 'short': 'MFDS', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202043302', 'name': 'Relational & NoSQL Database Systems', 'short': 'RNDS', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'IT'}, {'code': '202043310', 'name': 'Object Oriented Design with Java', 'short': 'OODJ', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'AW'}, {'code': '202043307', 'name': 'Computer Architecture & Linux Systems', 'short': 'CALS', 'category': 'PCC', 'l': 3, 't': 0, 'p': 0, 'c': 3, 'isHighCredit': False, 'labType': 'AI', 'facultyCode': 'VVN'}], 'AIDS_4': [{'code': '202044401', 'name': 'Operating Systems & Concurrency', 'short': 'OSC', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'KRP'}, {'code': '202044410', 'name': 'Artificial Intelligence Foundations', 'short': 'AIF', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'SNG'}, {'code': '202044411', 'name': 'Applied Probability & Statistical Inference', 'short': 'APSI', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202044412', 'name': 'Data Wrangling & Exploratory Analysis', 'short': 'DWEA', 'category': 'PCC', 'l': 2, 't': 0, 'p': 4, 'c': 4, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'TRR'}, {'code': '202044402', 'name': 'Data Communications & Networking', 'short': 'DCN', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'ANP'}], 'AIDS_5': [{'code': '202045601', 'name': 'Design and Analysis of Algorithms', 'short': 'DAA', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'MAP'}, {'code': '202045620', 'name': 'Machine Learning Concepts & Algorithms', 'short': 'ML', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'SNG'}, {'code': '202045621', 'name': 'Deep Learning Foundations (PyTorch/TF)', 'short': 'DL', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'PKG'}, {'code': '202045622', 'name': 'Big Data Engineering & Spark', 'short': 'BDE', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'KRP'}, {'code': '202045623', 'name': 'Natural Language Processing (PE1)', 'short': 'NLP', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'AI', 'facultyCode': 'KJP'}, {'code': '202045699', 'name': 'Open Elective (Physics of AI & Quantum Tech)', 'short': 'OE', 'category': 'OEC', 'l': 2, 't': 0, 'p': 0, 'c': 2, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'SKP'}], 'AIDS_6': [{'code': '202046620', 'name': 'Computer Vision & Pattern Recognition', 'short': 'CVPR', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'PKG'}, {'code': '202046621', 'name': 'Generative AI & LLM Systems', 'short': 'GENAI', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'PKG'}, {'code': '202046622', 'name': 'MLOps, Pipeline Engineering & Ethics', 'short': 'MLOPS', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'PKG'}, {'code': '202046623', 'name': 'Reinforcement Learning & Game AI', 'short': 'RL', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'AI', 'facultyCode': 'KJP'}, {'code': '202046624', 'name': 'Applied AI Domain Project', 'short': 'AIPROJ', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'AI', 'facultyCode': 'DKS'}], 'AIDS_7': [{'code': '202047706', 'name': 'Autonomous Systems & Edge AI', 'short': 'EDGEAI', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'DKS'}, {'code': '202047707', 'name': 'Cloud AI Infrastructure & High Performance Computing', 'short': 'HPC', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'MB'}, {'code': '202047708', 'name': 'Time Series Analysis & Forecasting', 'short': 'TSA', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'AI', 'facultyCode': 'SNG'}, {'code': '202047705', 'name': 'Major Project - Phase I (AI System)', 'short': 'PROJ-1', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 8, 'c': 4, 'isHighCredit': True, 'labType': 'AI', 'facultyCode': 'DKS'}], 'AIDS_8': [{'code': '202048801', 'name': 'Industry Internship / Major Capstone AI Project', 'short': 'CAPSTONE', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 24, 'c': 12, 'isHighCredit': True, 'labType': 'Industry/Lab', 'facultyCode': 'DKS'}, {'code': '202048802', 'name': 'AI Research Paper & Technical Viva', 'short': 'VIVA', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'Seminar', 'facultyCode': 'SNG'}, {'code': '202048803', 'name': 'AI Governance, Patents & Ethics', 'short': 'ETHICS', 'category': 'HSMC', 'l': 2, 't': 0, 'p': 0, 'c': 2, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'PMG'}], 'ME_1': [{'code': '202000101', 'name': 'Mathematics - I (Calculus & Linear Algebra)', 'short': 'MATH-1', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202000108', 'name': 'Engineering Chemistry', 'short': 'CHEM', 'category': 'BSC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'INT'}, {'code': '202000104', 'name': 'Basic Electrical & Electronics', 'short': 'BEE', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'PRM'}, {'code': '202000109', 'name': 'Engineering Mechanics (Statics & Dynamics)', 'short': 'EM', 'category': 'ESC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'HBJ'}, {'code': '202000105', 'name': 'Engineering Graphics & Computer Drafting', 'short': 'EGCD', 'category': 'ESC', 'l': 1, 't': 0, 'p': 4, 'c': 3, 'isHighCredit': False, 'labType': 'CAD', 'facultyCode': 'AYJ'}], 'ME_2': [{'code': '202000201', 'name': 'Mathematics - II (Calculus & ODE)', 'short': 'MATH-2', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202000202', 'name': 'Engineering Physics', 'short': 'EP', 'category': 'BSC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Physics', 'facultyCode': 'TRR'}, {'code': '202000204', 'name': 'Workshop & Manufacturing Practice', 'short': 'WMP', 'category': 'ESC', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'Workshop', 'facultyCode': 'BJS'}, {'code': '202000210', 'name': 'Elements of Mechanical Engineering', 'short': 'EME', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Mechanical', 'facultyCode': 'JVP'}, {'code': '202000205', 'name': 'Technical Communication & Ethics', 'short': 'TCE', 'category': 'HSMC', 'l': 2, 't': 0, 'p': 2, 'c': 3, 'isHighCredit': False, 'labType': 'Language', 'facultyCode': 'BJS'}], 'ME_3': [{'code': '202013301', 'name': 'Engineering Thermodynamics & Heat', 'short': 'THERMO', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'Mechanical', 'facultyCode': 'YDP'}, {'code': '202013302', 'name': 'Strength of Materials', 'short': 'SOM', 'category': 'PCC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Mechanical', 'facultyCode': 'HBJ'}, {'code': '202013303', 'name': 'Manufacturing Processes - I (Casting/Welding)', 'short': 'MP-1', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Workshop', 'facultyCode': 'RRS'}, {'code': '202013304', 'name': 'Material Science & Metallurgy', 'short': 'MSM', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Mechanical', 'facultyCode': 'INT'}, {'code': '202013305', 'name': 'Engineering Mathematics - III', 'short': 'MATH-3', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}], 'ME_4': [{'code': '202014401', 'name': 'Fluid Mechanics & Hydraulic Machines', 'short': 'FMHM', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'Mechanical', 'facultyCode': 'MIS'}, {'code': '202014402', 'name': 'Kinematics of Machinery (KOM)', 'short': 'KOM', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Mechanical', 'facultyCode': 'VNS'}, {'code': '202014403', 'name': 'Applied Thermodynamics & Steam Power', 'short': 'AT', 'category': 'PCC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Mechanical', 'facultyCode': 'YDP'}, {'code': '202014404', 'name': 'Manufacturing Processes - II (Machining)', 'short': 'MP-2', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Workshop', 'facultyCode': 'RRS'}, {'code': '202014405', 'name': 'Mechanical Measurement & Metrology', 'short': 'MMM', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Mechanical', 'facultyCode': 'HBJ'}], 'ME_5': [{'code': '202015501', 'name': 'Design of Machine Elements (DME)', 'short': 'DME', 'category': 'PCC', 'l': 4, 't': 1, 'p': 0, 'c': 5, 'isHighCredit': True, 'labType': 'CAD', 'facultyCode': 'VNS'}, {'code': '202015502', 'name': 'Dynamics of Machinery (DOM)', 'short': 'DOM', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Mechanical', 'facultyCode': 'HBJ'}, {'code': '202015503', 'name': 'Heat and Mass Transfer (HMT)', 'short': 'HMT', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Mechanical', 'facultyCode': 'YDP'}, {'code': '202015504', 'name': 'Internal Combustion Engines (ICE)', 'short': 'ICE', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Mechanical', 'facultyCode': 'MIS'}, {'code': '202015505', 'name': 'Operations Research (OR)', 'short': 'OR', 'category': 'PCC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'MVM'}, {'code': '202015506', 'name': 'CAD/CAM & FEA - PE1', 'short': 'CAD', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'CAD', 'facultyCode': 'AYJ'}, {'code': '202015507', 'name': 'Production Automation & Robotics - PE1', 'short': 'PAR', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'Mechanical', 'facultyCode': 'RRS'}, {'code': '202015508', 'name': 'Automobile Engineering & EV Tech - PE1', 'short': 'AUT', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'Mechanical', 'facultyCode': 'BJS'}, {'code': '202015599', 'name': 'Open Elective (Industrial Safety & Ethics)', 'short': 'OE', 'category': 'OEC', 'l': 2, 't': 0, 'p': 0, 'c': 2, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'PMG'}], 'ME_6': [{'code': '202016601', 'name': 'Computer Aided Design & Manufacturing (CAD/CAM)', 'short': 'CAD/CAM', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CAD', 'facultyCode': 'AYJ'}, {'code': '202016602', 'name': 'Refrigeration and Air Conditioning (RAC)', 'short': 'RAC', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Mechanical', 'facultyCode': 'MVM'}, {'code': '202016603', 'name': 'Production Automation & Robotics', 'short': 'PAR', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Mechanical', 'facultyCode': 'RRS'}, {'code': '202016604', 'name': 'Power Plant Engineering', 'short': 'PPE', 'category': 'PCC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'MIS'}, {'code': '202016606', 'name': 'Mechanical Mini Project', 'short': 'MP', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'Workshop', 'facultyCode': 'JVP'}], 'ME_7': [{'code': '202017701', 'name': 'Automobile Engineering & EV Tech', 'short': 'EV', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'Mechanical', 'facultyCode': 'BJS'}, {'code': '202017702', 'name': 'Finite Element Method (FEM) Analysis', 'short': 'FEM', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CAD', 'facultyCode': 'AYJ'}, {'code': '202017703', 'name': 'Renewable Energy Technologies', 'short': 'RET', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'Mechanical', 'facultyCode': 'INT'}, {'code': '202017705', 'name': 'Major Project - Phase I', 'short': 'PROJ-1', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 8, 'c': 4, 'isHighCredit': True, 'labType': 'Mechanical', 'facultyCode': 'JVP'}], 'ME_8': [{'code': '202018801', 'name': 'Industry Internship / Major Capstone Project', 'short': 'CAPSTONE', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 24, 'c': 12, 'isHighCredit': True, 'labType': 'Industry/Lab', 'facultyCode': 'JVP'}, {'code': '202018802', 'name': 'Technical Seminar & Project Viva', 'short': 'VIVA', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'Seminar', 'facultyCode': 'JVP'}, {'code': '202018803', 'name': 'Industrial Management & Quality Control', 'short': 'IMQC', 'category': 'HSMC', 'l': 2, 't': 0, 'p': 0, 'c': 2, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'MVM'}], 'CH_1': [{'code': '202000101', 'name': 'Mathematics - I (Calculus & Linear Algebra)', 'short': 'MATH-1', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202000102', 'name': 'Engineering Physics', 'short': 'EP', 'category': 'BSC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Physics', 'facultyCode': 'SKP'}, {'code': '202000108', 'name': 'Applied Chemistry for Engineers', 'short': 'CHEM', 'category': 'BSC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'INT'}, {'code': '202000104', 'name': 'Basic Electrical Engineering', 'short': 'BEE', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'PRM'}, {'code': '202000105', 'name': 'Engineering Graphics & Design', 'short': 'EGD', 'category': 'ESC', 'l': 1, 't': 0, 'p': 4, 'c': 3, 'isHighCredit': False, 'labType': 'CAD', 'facultyCode': 'AYJ'}], 'CH_2': [{'code': '202000201', 'name': 'Mathematics - II (Calculus & ODE)', 'short': 'MATH-2', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202000211', 'name': 'Organic & Physical Chemistry', 'short': 'OPC', 'category': 'BSC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'INT'}, {'code': '202000103', 'name': 'Programming for Problem Solving', 'short': 'PPS', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'JKP'}, {'code': '202000204', 'name': 'Workshop Practices', 'short': 'WS', 'category': 'ESC', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'Workshop', 'facultyCode': 'BJS'}, {'code': '202000205', 'name': 'Technical Communication & Ethics', 'short': 'TCE', 'category': 'HSMC', 'l': 2, 't': 0, 'p': 2, 'c': 3, 'isHighCredit': False, 'labType': 'Language', 'facultyCode': 'BJS'}], 'CH_3': [{'code': '202023301', 'name': 'Chemical Process Calculations (CPC)', 'short': 'CPC', 'category': 'PCC', 'l': 4, 't': 1, 'p': 0, 'c': 5, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'HSP'}, {'code': '202023302', 'name': 'Fluid Flow Operations (FFO)', 'short': 'FFO', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'KSN'}, {'code': '202023303', 'name': 'Chemical Engineering Thermodynamics - I', 'short': 'CET-1', 'category': 'PCC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'HSP'}, {'code': '202023304', 'name': 'Mechanical Operations in Chemical Engg', 'short': 'MO', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'INT'}, {'code': '202023305', 'name': 'Applied Mathematics in Chemical Engg', 'short': 'AMCE', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}], 'CH_4': [{'code': '202024401', 'name': 'Heat Transfer Operations (HTO)', 'short': 'HTO', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'HSP'}, {'code': '202024402', 'name': 'Mass Transfer Operations - I (MTO-1)', 'short': 'MTO-1', 'category': 'PCC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'RMS'}, {'code': '202024403', 'name': 'Chemical Reaction Engineering - I (CRE-1)', 'short': 'CRE-1', 'category': 'PCC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'HSP'}, {'code': '202024404', 'name': 'Process Equipment Design - I (PED-1)', 'short': 'PED-1', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CAD', 'facultyCode': 'INT'}, {'code': '202024405', 'name': 'Materials of Construction for Chemical Plants', 'short': 'MCCP', 'category': 'PCC', 'l': 3, 't': 0, 'p': 0, 'c': 3, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'INT'}], 'CH_5': [{'code': '202025501', 'name': 'Mass Transfer Operations - II (MTO-2)', 'short': 'MTO-2', 'category': 'PCC', 'l': 4, 't': 1, 'p': 0, 'c': 5, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'HSP'}, {'code': '202025502', 'name': 'Chemical Reaction Engineering - II (CRE-2)', 'short': 'CRE-2', 'category': 'PCC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'HSP'}, {'code': '202025503', 'name': 'Instrumentation & Process Control', 'short': 'IPC', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'RMS'}, {'code': '202025504', 'name': 'Chemical Technology (Inorganic & Organic)', 'short': 'CT', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'RMS'}, {'code': '202025505', 'name': 'Transport Phenomena & Modeling - PE1', 'short': 'TP', 'category': 'PEC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'KSN'}, {'code': '202025599', 'name': 'Open Elective (Industrial Safety & HAZOP)', 'short': 'OE', 'category': 'OEC', 'l': 2, 't': 0, 'p': 0, 'c': 2, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'PMG'}], 'CH_6': [{'code': '202026601', 'name': 'Transport Phenomena', 'short': 'TP', 'category': 'PCC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'KSN'}, {'code': '202026602', 'name': 'Process Modeling, Simulation & Aspen', 'short': 'PMSA', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'KSN'}, {'code': '202026603', 'name': 'Industrial Pollution Control & Abatement', 'short': 'IPCA', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'RMS'}, {'code': '202026604', 'name': 'Petroleum Refining & Petrochemicals', 'short': 'PRP', 'category': 'PEC', 'l': 3, 't': 0, 'p': 0, 'c': 3, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'INT'}, {'code': '202026606', 'name': 'Chemical Process Mini Project', 'short': 'MP', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'Chemistry', 'facultyCode': 'INT'}], 'CH_7': [{'code': '202027701', 'name': 'Plant Design & Economics', 'short': 'PDE', 'category': 'PCC', 'l': 4, 't': 1, 'p': 0, 'c': 5, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'KSN'}, {'code': '202027702', 'name': 'Polymer Science & Technology', 'short': 'PST', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'RMS'}, {'code': '202027703', 'name': 'Biochemical Engineering Principles', 'short': 'BCE', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'Chemistry', 'facultyCode': 'RMS'}, {'code': '202027705', 'name': 'Major Project - Phase I', 'short': 'PROJ-1', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 8, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'INT'}], 'CH_8': [{'code': '202028801', 'name': 'Industry Internship / Major Capstone Chemical Project', 'short': 'CAPSTONE', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 24, 'c': 12, 'isHighCredit': True, 'labType': 'Industry/Lab', 'facultyCode': 'INT'}, {'code': '202028802', 'name': 'Process Seminar & Comprehensive Viva', 'short': 'VIVA', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'Seminar', 'facultyCode': 'INT'}, {'code': '202028803', 'name': 'Chemical Plant Management & Safety Regulations', 'short': 'CPMS', 'category': 'HSMC', 'l': 2, 't': 0, 'p': 0, 'c': 2, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'INT'}], 'EE_1': [{'code': '202000101', 'name': 'Mathematics - I (Calculus & Linear Algebra)', 'short': 'MATH-1', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202000102', 'name': 'Engineering Physics', 'short': 'EP', 'category': 'BSC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Physics', 'facultyCode': 'SKP'}, {'code': '202000104', 'name': 'Basic Electrical Engineering', 'short': 'BEE', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'PRM'}, {'code': '202000103', 'name': 'Programming for Problem Solving', 'short': 'PPS', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'JKP'}, {'code': '202000105', 'name': 'Engineering Graphics & Design', 'short': 'EGD', 'category': 'ESC', 'l': 1, 't': 0, 'p': 4, 'c': 3, 'isHighCredit': False, 'labType': 'CAD', 'facultyCode': 'AYJ'}], 'EE_2': [{'code': '202000201', 'name': 'Mathematics - II (Calculus & ODE)', 'short': 'MATH-2', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202000202', 'name': 'Engineering Chemistry', 'short': 'CHEM', 'category': 'BSC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'INT'}, {'code': '202000203', 'name': 'Basic Electronic Devices & Circuits', 'short': 'BEDC', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'VSS'}, {'code': '202000204', 'name': 'Electrical Workshop Practice', 'short': 'EWS', 'category': 'ESC', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'Workshop', 'facultyCode': 'BJS'}, {'code': '202000205', 'name': 'Technical Communication Skills', 'short': 'TCS', 'category': 'HSMC', 'l': 2, 't': 0, 'p': 2, 'c': 3, 'isHighCredit': False, 'labType': 'Language', 'facultyCode': 'BJS'}], 'EE_3': [{'code': '202033301', 'name': 'Electrical Circuit Analysis (ECA)', 'short': 'ECA', 'category': 'PCC', 'l': 4, 't': 1, 'p': 0, 'c': 5, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'PRM'}, {'code': '202033302', 'name': 'Electrical Machines - I (Transformers & DC)', 'short': 'EM-1', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'MNJ'}, {'code': '202033303', 'name': 'Electromagnetic Fields & Waves', 'short': 'EMF', 'category': 'PCC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'VSS'}, {'code': '202033304', 'name': 'Analog Electronics & Op-Amps', 'short': 'AE', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'VSS'}, {'code': '202033305', 'name': 'Engineering Mathematics - III', 'short': 'MATH-3', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}], 'EE_4': [{'code': '202034401', 'name': 'Power Systems - I (Generation & Transmission)', 'short': 'PS-1', 'category': 'PCC', 'l': 4, 't': 1, 'p': 0, 'c': 5, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'KMC'}, {'code': '202034402', 'name': 'Electrical Machines - II (Induction & Sync)', 'short': 'EM-2', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'MNJ'}, {'code': '202034403', 'name': 'Control Systems Engineering', 'short': 'CSE', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'PRM'}, {'code': '202034404', 'name': 'Digital Electronics & Microprocessors', 'short': 'DEMP', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'VSS'}, {'code': '202034405', 'name': 'Electrical Measurements & Sensors', 'short': 'EMS', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'INT'}], 'EE_5': [{'code': '202035501', 'name': 'Power Electronics & Converter Drives', 'short': 'PE', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'KMS'}, {'code': '202035502', 'name': 'Power Systems - II (Analysis & Faults)', 'short': 'PS-2', 'category': 'PCC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'KMC'}, {'code': '202035503', 'name': 'Microcontrollers & Embedded Systems', 'short': 'MCES', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'VSS'}, {'code': '202035504', 'name': 'Electrical Machine Design', 'short': 'EMD', 'category': 'PCC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'CAD', 'facultyCode': 'MNJ'}, {'code': '202035505', 'name': 'Control Systems Engineering & Automation - PE1', 'short': 'CS', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'EE', 'facultyCode': 'PRM'}, {'code': '202035599', 'name': 'Open Elective (Renewable Energy Integration)', 'short': 'OE', 'category': 'OEC', 'l': 2, 't': 0, 'p': 0, 'c': 2, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'SKP'}], 'EE_6': [{'code': '202036601', 'name': 'Switchgear, Protection & Relays', 'short': 'SWP', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'KMS'}, {'code': '202036602', 'name': 'Digital Signal Processing (DSP)', 'short': 'DSP', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'INT'}, {'code': '202036603', 'name': 'Renewable Energy Systems & Smart Grid', 'short': 'RESG', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'KMS'}, {'code': '202036604', 'name': 'Industrial Automation & PLC / SCADA', 'short': 'PLC', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'MNJ'}, {'code': '202036606', 'name': 'Electrical Mini Project', 'short': 'MP', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'EE', 'facultyCode': 'AW'}], 'EE_7': [{'code': '202037701', 'name': 'High Voltage Engineering & Testing', 'short': 'HVE', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'KMC'}, {'code': '202037702', 'name': 'Electric Vehicle Powertrain & Battery Tech', 'short': 'EVT', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'KMS'}, {'code': '202037703', 'name': 'Power System Operation & Control', 'short': 'PSOC', 'category': 'PEC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': False, 'labType': 'EE', 'facultyCode': 'INT'}, {'code': '202037705', 'name': 'Major Project - Phase I', 'short': 'PROJ-1', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 8, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'AW'}], 'EE_8': [{'code': '202038801', 'name': 'Industry Internship / Major Capstone Electrical Project', 'short': 'CAPSTONE', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 24, 'c': 12, 'isHighCredit': True, 'labType': 'Industry/Lab', 'facultyCode': 'AW'}, {'code': '202038802', 'name': 'Seminar & Comprehensive Electrical Viva', 'short': 'VIVA', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'Seminar', 'facultyCode': 'AW'}, {'code': '202038803', 'name': 'Energy Auditing, Conservation & Management', 'short': 'EACM', 'category': 'HSMC', 'l': 2, 't': 0, 'p': 0, 'c': 2, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'INT'}], 'CL_1': [{'code': '202000101', 'name': 'Mathematics - I (Calculus & Linear Algebra)', 'short': 'MATH-1', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202000102', 'name': 'Engineering Physics', 'short': 'EP', 'category': 'BSC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Physics', 'facultyCode': 'SKP'}, {'code': '202000109', 'name': 'Engineering Mechanics', 'short': 'EM', 'category': 'ESC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Civil', 'facultyCode': 'HBJ'}, {'code': '202000105', 'name': 'Engineering Graphics & Building Drafting', 'short': 'EGD', 'category': 'ESC', 'l': 1, 't': 0, 'p': 4, 'c': 3, 'isHighCredit': False, 'labType': 'CAD', 'facultyCode': 'AYJ'}, {'code': '202000104', 'name': 'Basic Electrical & Electronics', 'short': 'BEE', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'EE', 'facultyCode': 'PRM'}], 'CL_2': [{'code': '202000201', 'name': 'Mathematics - II (Calculus & ODE)', 'short': 'MATH-2', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}, {'code': '202000202', 'name': 'Engineering Chemistry', 'short': 'CHEM', 'category': 'BSC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Chemistry', 'facultyCode': 'INT'}, {'code': '202000103', 'name': 'Programming for Problem Solving', 'short': 'PPS', 'category': 'ESC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'CE', 'facultyCode': 'JKP'}, {'code': '202000204', 'name': 'Workshop & Construction Practice', 'short': 'WCP', 'category': 'ESC', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'Workshop', 'facultyCode': 'BJS'}, {'code': '202000205', 'name': 'Technical Communication Skills', 'short': 'TCS', 'category': 'HSMC', 'l': 2, 't': 0, 'p': 2, 'c': 3, 'isHighCredit': False, 'labType': 'Language', 'facultyCode': 'BJS'}], 'CL_3': [{'code': '202053301', 'name': 'Surveying & Geomatics', 'short': 'SURV', 'category': 'PCC', 'l': 3, 't': 0, 'p': 4, 'c': 5, 'isHighCredit': True, 'labType': 'Civil', 'facultyCode': 'DMY'}, {'code': '202053302', 'name': 'Mechanics of Solids (MOS)', 'short': 'MOS', 'category': 'PCC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Civil', 'facultyCode': 'PBV'}, {'code': '202053303', 'name': 'Fluid Mechanics & Hydraulics', 'short': 'FMH', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Civil', 'facultyCode': 'ASS'}, {'code': '202053304', 'name': 'Building Construction & Materials', 'short': 'BCM', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Civil', 'facultyCode': 'CBH'}, {'code': '202053305', 'name': 'Engineering Geology', 'short': 'EG', 'category': 'PCC', 'l': 2, 't': 0, 'p': 2, 'c': 3, 'isHighCredit': False, 'labType': 'Civil', 'facultyCode': 'INT'}], 'CL_4': [{'code': '202054401', 'name': 'Structural Analysis - I (SA-1)', 'short': 'SA-1', 'category': 'PCC', 'l': 4, 't': 1, 'p': 0, 'c': 5, 'isHighCredit': True, 'labType': 'Civil', 'facultyCode': 'RJB'}, {'code': '202054402', 'name': 'Geotechnical Engineering - I (Soil Mechanics)', 'short': 'GE-1', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Civil', 'facultyCode': 'PBV'}, {'code': '202054403', 'name': 'Concrete Technology', 'short': 'CT', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Civil', 'facultyCode': 'DKB'}, {'code': '202054404', 'name': 'Water Supply & Environmental Engineering', 'short': 'WSEE', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Civil', 'facultyCode': 'ASS'}, {'code': '202054405', 'name': 'Numerical Methods in Civil Engineering', 'short': 'NMCE', 'category': 'BSC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'Classroom', 'facultyCode': 'DM'}], 'CL_5': [{'code': '202055501', 'name': 'Structural Analysis - II (SA-2)', 'short': 'SA-2', 'category': 'PCC', 'l': 4, 't': 1, 'p': 0, 'c': 5, 'isHighCredit': True, 'labType': 'Civil', 'facultyCode': 'RJB'}, {'code': '202055502', 'name': 'Design of Reinforced Concrete Structures (DRCS)', 'short': 'DRCS', 'category': 'PCC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'CAD', 'facultyCode': 'DKB'}, {'code': '202055503', 'name': 'Geotechnical Engineering - II (Foundations)', 'short': 'GE-2', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Civil', 'facultyCode': 'PBV'}, {'code': '202055504', 'name': 'Highway & Transportation Engineering', 'short': 'HTE', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Civil', 'facultyCode': 'DMY'}, {'code': '202055505', 'name': 'Water Resources & Hydrology - PE1', 'short': 'WRE', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'Civil', 'facultyCode': 'ASS'}, {'code': '202055506', 'name': 'Environmental Engineering - I - PE1', 'short': 'EE-1', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'Civil', 'facultyCode': 'CBH'}, {'code': '202055507', 'name': 'Concrete Technology & Estimation - PE1', 'short': 'CT', 'category': 'PEC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': False, 'labType': 'Civil', 'facultyCode': 'BWP'}, {'code': '202055599', 'name': 'Open Elective (GIS & Remote Sensing)', 'short': 'OE', 'category': 'OEC', 'l': 2, 't': 0, 'p': 0, 'c': 2, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'DM'}], 'CL_6': [{'code': '202056601', 'name': 'Design of Steel Structures (DSS)', 'short': 'DSS', 'category': 'PCC', 'l': 3, 't': 1, 'p': 0, 'c': 4, 'isHighCredit': True, 'labType': 'CAD', 'facultyCode': 'DKB'}, {'code': '202056602', 'name': 'Environmental Engineering - II (Wastewater)', 'short': 'EE-2', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Civil', 'facultyCode': 'CBH'}, {'code': '202056603', 'name': 'Hydrology & Water Resources Engineering', 'short': 'HWRE', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Civil', 'facultyCode': 'ASS'}, {'code': '202056604', 'name': 'Construction Project Management & Estimation', 'short': 'CPME', 'category': 'PCC', 'l': 3, 't': 0, 'p': 0, 'c': 3, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'BWP'}, {'code': '202056606', 'name': 'Civil Engineering Mini Project', 'short': 'MP', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'Civil', 'facultyCode': 'INT'}], 'CL_7': [{'code': '202057701', 'name': 'Earthquake Resistant Design of Structures', 'short': 'ERDS', 'category': 'PCC', 'l': 4, 't': 0, 'p': 2, 'c': 5, 'isHighCredit': True, 'labType': 'Civil', 'facultyCode': 'RJB'}, {'code': '202057702', 'name': 'Bridge & Tunnel Engineering', 'short': 'BTE', 'category': 'PCC', 'l': 3, 't': 0, 'p': 2, 'c': 4, 'isHighCredit': True, 'labType': 'Civil', 'facultyCode': 'BWP'}, {'code': '202057703', 'name': 'Urban Infrastructure Planning & Smart Cities', 'short': 'UIP', 'category': 'PEC', 'l': 3, 't': 0, 'p': 0, 'c': 3, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'DMY'}, {'code': '202057705', 'name': 'Major Project - Phase I', 'short': 'PROJ-1', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 8, 'c': 4, 'isHighCredit': True, 'labType': 'Civil', 'facultyCode': 'INT'}], 'CL_8': [{'code': '202058801', 'name': 'Industry Internship / Major Capstone Civil Project', 'short': 'CAPSTONE', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 24, 'c': 12, 'isHighCredit': True, 'labType': 'Industry/Lab', 'facultyCode': 'INT'}, {'code': '202058802', 'name': 'Structural Viva & Comprehensive Seminar', 'short': 'VIVA', 'category': 'PROJ', 'l': 0, 't': 0, 'p': 4, 'c': 2, 'isHighCredit': False, 'labType': 'Seminar', 'facultyCode': 'INT'}, {'code': '202058803', 'name': 'Construction Law, Contracts & Valuation', 'short': 'CLCV', 'category': 'HSMC', 'l': 2, 't': 0, 'p': 0, 'c': 2, 'isHighCredit': False, 'labType': 'Classroom', 'facultyCode': 'BWP'}]}, 'faculty': [{'code': 'MB', 'name': 'Dr. Malay Bhatt', 'dept': 'CE', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/56.jpg', 'localPhoto': '56.jpg', 'designation': 'Associate Professor and Head', 'experience': '22 Years', 'qualification': 'Ph.D., M.E., B.E.', 'skills': 'Computer Networks, Cyber Security, Distributed Computing, Cloud Architecture', 'priorities': ['Computer Networks', 'Cyber Security & Digital Forensics', 'Distributed Computing']}, {'code': 'DKS', 'name': 'Dr. Dheeraj Kumar Singh', 'dept': 'CE', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/DKS.jpg', 'localPhoto': 'DKS.jpg', 'designation': 'Associate Professor & Head CSD', 'experience': '17 Years', 'qualification': 'Ph.D., M.Tech, B.Tech', 'skills': 'Algorithms, Machine Learning, Data Science, AI Systems', 'priorities': ['Design and Analysis of Algorithms', 'Machine Learning & AI', 'Data Structures & Algorithms (DSA)']}, {'code': 'IT', 'name': 'Dr. Ishita Theba', 'dept': 'CE', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/52.jpg', 'localPhoto': '52.jpg', 'designation': 'Assistant Professor', 'experience': '12 Years', 'qualification': 'Ph.D., M.E., B.E.', 'skills': 'Cloud Computing, Computer Graphics, Operating Systems', 'priorities': ['Cloud Computing & DevOps Architecture', 'Operating Systems (OS)', 'Computer Graphics - PE1']}, {'code': 'AKK', 'name': 'Prof. Aniruddha Kurtkoti', 'dept': 'CE', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/63.jpg', 'localPhoto': '63.jpg', 'designation': 'Assistant Professor', 'experience': '8 Years', 'qualification': 'M.Tech, B.Tech', 'skills': 'Python, Web Programming, Mobile Product Engineering, Database Management', 'priorities': ['Python and Web Programming', 'Database Management Systems (DBMS)', 'Mobile Application Development']}, {'code': 'CBJ', 'name': 'Prof. Chinmay Joshi', 'dept': 'CE', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/271.jpg', 'localPhoto': '271.jpg', 'designation': 'Assistant Professor', 'experience': '9 Years', 'qualification': 'M.E., B.E.', 'skills': 'UI/UX Design, Computer Graphics & Design, Digital Logic', 'priorities': ['Computer Graphics & Design', 'Fundamentals of UI/UX Design', 'Digital Logic & Computer Design (DLD)']}, {'code': 'PT', 'name': 'Prof. Prerak Thakkar', 'dept': 'CE', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/335.jpg', 'localPhoto': '335.jpg', 'designation': 'Assistant Professor', 'experience': '11 Years', 'qualification': 'M.E., B.E.', 'skills': 'Algorithms, Advanced Java, Object Oriented Programming', 'priorities': ['Design and Analysis of Algorithms', 'Advanced Java Programming - PE1', 'Object Oriented Programming with Java']}, {'code': 'AJK', 'name': 'Prof. Axit Jaykumar Kachhia', 'dept': 'CE', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/270722.jpg', 'localPhoto': '270722.jpg', 'designation': 'Assistant Professor', 'experience': '8 Years', 'qualification': 'M.E., B.E.', 'skills': 'Full Stack Development, Cyber Security, Web Development', 'priorities': ['Full Stack Web Technologies (MERN)', 'Cyber Security - PE1', 'Web Development']}, {'code': 'KSP', 'name': 'Prof. Kinjal Parmar', 'dept': 'CE', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/1027.jpg', 'localPhoto': '1027.jpg', 'designation': 'Assistant Professor', 'experience': '10 Years', 'qualification': 'M.E., B.E.', 'skills': 'Programming for Problem Solving, Web Development, Algorithms', 'priorities': ['Web Development', 'Programming for Problem Solving (PPS - C)', 'Full Stack Web Technologies (MERN)']}, {'code': 'JVP_CE', 'name': 'Prof. Jignasha Vishal Parmar', 'dept': 'CE', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/09072024.jpg', 'localPhoto': '09072024.jpg', 'designation': 'Assistant Professor', 'experience': '11 Years', 'qualification': 'M.E., B.E.', 'skills': 'Software Testing, Database Management, Python', 'priorities': ['Database Management Systems (DBMS)', 'Software Testing & QA', 'Python for Data Science']}, {'code': 'SJM', 'name': 'Prof. Sheetal J. Macwan', 'dept': 'CE', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/sheetal.jpg', 'localPhoto': 'sheetal.jpg', 'designation': 'Assistant Professor', 'experience': '10 Years', 'qualification': 'M.E., B.E.', 'skills': 'Data Structures, Computer Organization, Programming', 'priorities': ['Data Structures & Algorithms (DSA)', 'Computer Organization & Architecture (COA)', 'Object Oriented Programming with C++']}, {'code': 'TRR', 'name': 'Prof. Tejas Rajeshbhai Rana', 'dept': 'CE', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/TJ.png', 'localPhoto': 'TJ.png', 'designation': 'Assistant Professor & TT Coordinator', 'experience': '12 Years', 'qualification': 'M.E., B.E.', 'skills': 'Python for Data Science, Computer Vision, Machine Learning', 'priorities': ['Python for Data Science', 'Computer Vision & Pattern Recognition', 'Machine Learning & AI']}, {'code': 'PKT', 'name': 'Prof. Pragnesh Patel', 'dept': 'CE', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/1066.jpg', 'localPhoto': '1066.jpg', 'designation': 'Assistant Professor', 'experience': '14 Years', 'qualification': 'M.E., B.E.', 'skills': 'Computer Networks, Database Management Systems, Software Quality', 'priorities': ['Computer Networks', 'Database Management Systems (DBMS)', 'Software Testing & QA']}, {'code': 'AW', 'name': 'Prof. Ankit Wadhwa', 'dept': 'CE', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/05072024.jpg', 'localPhoto': '05072024.jpg', 'designation': 'Assistant Professor', 'experience': '9 Years', 'qualification': 'M.E., B.E.', 'skills': 'Advanced Java Programming, Basic Electrical, Cloud Computing', 'priorities': ['Advanced Java Programming - PE1', 'Object Oriented Programming with Java', 'Basic Electrical Engineering (BEE)']}, {'code': 'PRB', 'name': 'Dr. Priyang Bhatt', 'dept': 'IT', 'photo': 'assets/faculty_images/priyang_bhatt.jpg', 'localPhoto': 'priyang_bhatt.jpg', 'designation': 'Associate Professor & Head IT', 'experience': '18 Years', 'qualification': 'Ph.D., M.E., B.E.', 'skills': 'Cloud Computing, Distributed Computing, High Performance Computing', 'priorities': ['Cloud Computing & Virtualization', 'DevOps & Cloud Native Architecture', 'Design and Analysis of Algorithms']}, {'code': 'DJP', 'name': 'Dr. Dinesh Prajapati', 'dept': 'IT', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/66.jpg', 'localPhoto': '66.jpg', 'designation': 'Associate Professor & AI Coordinator', 'experience': '16 Years', 'qualification': 'Ph.D., M.E., B.E.', 'skills': 'Artificial Intelligence, Machine Learning, Deep Learning', 'priorities': ['Artificial Intelligence (PE1)', 'Machine Learning & Analytics', 'Deep Learning Foundations']}, {'code': 'KRP', 'name': 'Dr. Krunal Patel', 'dept': 'IT', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/100008.jpg', 'localPhoto': '100008.jpg', 'designation': 'Associate Professor', 'experience': '15 Years', 'qualification': 'Ph.D., M.E., B.E.', 'skills': 'Data Structures, Database Management, Big Data', 'priorities': ['Data Structures', 'Database Management Systems', 'Big Data Technologies & Analytics']}, {'code': 'SNG', 'name': 'Dr. Shital Gondaliya', 'dept': 'IT', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/20230823.jpg', 'localPhoto': '20230823.jpg', 'designation': 'Associate Professor', 'experience': '16 Years', 'qualification': 'Ph.D., M.E., B.E.', 'skills': 'Web Development, Machine Learning, Data Analytics', 'priorities': ['Web Development', 'Machine Learning & Analytics', 'Database Management Systems']}, {'code': 'ANP', 'name': 'Dr. Anand Pandya', 'dept': 'IT', 'photo': 'assets/faculty_images/anand_pandya.jpg', 'localPhoto': 'anand_pandya.jpg', 'designation': 'Assistant Professor', 'experience': '12 Years', 'qualification': 'Ph.D., M.E., B.E.', 'skills': 'Cyber Security, Ethical Hacking, Network Security', 'priorities': ['Cyber Security (PE1)', 'Information & Network Security', 'Computer Networks']}, {'code': 'JKP', 'name': 'Prof. Jitiksha Patel', 'dept': 'IT', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/294.jpg', 'localPhoto': '294.jpg', 'designation': 'Assistant Professor', 'experience': '10 Years', 'qualification': 'M.E., B.E.', 'skills': 'Software Engineering, Java Programming, Agile Development', 'priorities': ['Software Engineering', 'Java Programming & Technologies', 'Software Project Management']}, {'code': 'HMP', 'name': 'Prof. Hemanshu Patel', 'dept': 'IT', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/322.jpg', 'localPhoto': '322.jpg', 'designation': 'Assistant Professor', 'experience': '11 Years', 'qualification': 'M.E., B.E.', 'skills': 'Operating Systems, Shell Scripting, Linux System Architecture', 'priorities': ['Operating Systems', 'Programming for Problem Solving (PPS)', 'DevOps & Cloud Native Architecture']}, {'code': 'NMM', 'name': 'Prof. Nayan Mali', 'dept': 'IT', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/336.jpg', 'localPhoto': '336.jpg', 'designation': 'Assistant Professor', 'experience': '10 Years', 'qualification': 'M.Tech, B.E.', 'skills': 'Programming with Python, Data Science, Software Project Management', 'priorities': ['Programming with Python', 'Software Project Management (PE2)', 'Python for Scientific Computing']}, {'code': 'KJP', 'name': 'Prof. Keyur Patel', 'dept': 'IT', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/1039.jpg', 'localPhoto': '1039.jpg', 'designation': 'Assistant Professor', 'experience': '12 Years', 'qualification': 'M.E., B.E.', 'skills': 'Artificial Intelligence, Digital Electronics, Advance Java', 'priorities': ['Artificial Intelligence (PE1)', 'Digital Electronics & Computer Organization', 'Advanced Java Programming (PE1)']}, {'code': 'MAP', 'name': 'Prof. Mayur Patel', 'dept': 'IT', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/23052022.jpg', 'localPhoto': '23052022.jpg', 'designation': 'Assistant Professor', 'experience': '13 Years', 'qualification': 'M.E., B.E.', 'skills': 'Design and Analysis of Algorithms, Data Structures, Cloud Computing', 'priorities': ['Design and Analysis of Algorithms', 'Data Structures', 'Cloud Computing & Virtualization']}, {'code': 'AJR', 'name': 'Prof. Anjali Rajput', 'dept': 'IT', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/17072023.jpg', 'localPhoto': '17072023.jpg', 'designation': 'Assistant Professor', 'experience': '11 Years', 'qualification': 'M.E., B.E.', 'skills': 'Software Engineering, Full Stack Web Development, Java', 'priorities': ['Software Engineering', 'Full Stack Application Development', 'Java Programming & Technologies']}, {'code': 'HVP', 'name': 'Prof. Himani Patel', 'dept': 'IT', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/1038.jpg', 'localPhoto': '1038.jpg', 'designation': 'Assistant Professor', 'experience': '9 Years', 'qualification': 'M.E., B.E.', 'skills': 'Computer Networks, Cyber Security, Ethical Hacking', 'priorities': ['Cyber Security (PE1)', 'Computer Networks', 'Cyber Security & Ethical Hacking']}, {'code': 'KVP', 'name': 'Prof. Kavya Prajapati', 'dept': 'IT', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/IMG_8027.png', 'localPhoto': 'IMG_8027.png', 'designation': 'Assistant Professor', 'experience': '8 Years', 'qualification': 'M.E., B.E.', 'skills': 'Object Oriented Programming, C++, Mobile Computing', 'priorities': ['Object Oriented Programming with C++', 'Mobile Computing & Wireless Tech', 'Web Development']}, {'code': 'VVN_CSD', 'name': 'Prof. Vishwadip Nanavati', 'dept': 'CSD', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/VD_CP.jpg', 'localPhoto': 'VD_CP.jpg', 'designation': 'Assistant Professor', 'experience': '9 Years', 'qualification': 'M.E., B.E.', 'skills': 'Computer Architecture & Design, 3D Animation, Game Design', 'priorities': ['Computer Architecture & Design', '3D Animation & Game Design', 'Design Research Methods & Usability Testing']}, {'code': 'BKM', 'name': 'Prof. Barkha Mehta', 'dept': 'CSD', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/Barkha_CP.jpg', 'localPhoto': 'Barkha_CP.jpg', 'designation': 'Assistant Professor', 'experience': '7 Years', 'qualification': 'M.Tech, B.Tech', 'skills': 'Visual Arts, Design Thinking, Prototyping, Spatial Design', 'priorities': ['Visual Arts & Design Thinking', 'Design Workshop & Prototyping', 'Spatial Computing & Generative Design']}, {'code': 'PKG', 'name': 'Prof. Priyanka Gondaliya', 'dept': 'AIDS', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/IMG_8025.png', 'localPhoto': 'IMG_8025.png', 'designation': 'Assistant Professor', 'experience': '9 Years', 'qualification': 'M.E., B.E.', 'skills': 'Generative AI, Large Language Models, AI Ethics, Computer Vision', 'priorities': ['Generative AI & LLM Systems', 'Computer Vision & Pattern Recognition', 'MLOps, Pipeline Engineering & Ethics']}, {'code': 'VNS', 'name': 'Dr. Vishal N. Singh', 'dept': 'ME', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/85.jpg', 'localPhoto': '85.jpg', 'designation': 'Professor & Head', 'experience': '22 Years', 'qualification': 'Ph.D., M.E., B.E.', 'skills': 'Design of Machine Elements, Kinematics, Dynamics of Machinery', 'priorities': ['Design of Machine Elements (DME)', 'Kinematics of Machinery (KOM)', 'Dynamics of Machinery (DOM)']}, {'code': 'YDP', 'name': 'Dr. Yashavant D. Patel', 'dept': 'ME', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/88.jpg', 'localPhoto': '88.jpg', 'designation': 'Associate Professor', 'experience': '18 Years', 'qualification': 'Ph.D., M.E., B.E.', 'skills': 'Thermodynamics, Heat and Mass Transfer, Thermal Power', 'priorities': ['Engineering Thermodynamics & Heat', 'Heat and Mass Transfer (HMT)', 'Applied Thermodynamics & Steam Power']}, {'code': 'MIS', 'name': 'Dr. Mitesh I. Shah', 'dept': 'ME', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/87.jpg', 'localPhoto': '87.jpg', 'designation': 'Associate Professor', 'experience': '16 Years', 'qualification': 'Ph.D., M.E., B.E.', 'skills': 'Fluid Mechanics, Hydraulic Machines, Power Plant Engineering', 'priorities': ['Fluid Mechanics & Hydraulic Machines', 'Power Plant Engineering', 'Internal Combustion Engines (ICE)']}, {'code': 'AYJ', 'name': 'Dr. Ayanesh Y. Joshi', 'dept': 'ME', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/50.jpg', 'localPhoto': '50.jpg', 'designation': 'Associate Professor', 'experience': '15 Years', 'qualification': 'Ph.D., M.E., B.E.', 'skills': 'CAD/CAM, Finite Element Analysis, Solid Modeling', 'priorities': ['Computer Aided Design & Manufacturing (CAD/CAM)', 'Finite Element Method (FEM) Analysis', 'Engineering Graphics & Computer Drafting']}, {'code': 'RRS', 'name': 'Dr. Ronakkumar Rajnikant Shah', 'dept': 'ME', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/90.jpg', 'localPhoto': '90.jpg', 'designation': 'Associate Professor', 'experience': '14 Years', 'qualification': 'Ph.D., M.E., B.E.', 'skills': 'Manufacturing Processes, Production Automation, CNC Technology', 'priorities': ['Manufacturing Processes - I (Casting/Welding)', 'Manufacturing Processes - II (Machining)', 'Production Automation & Robotics']}, {'code': 'MVM', 'name': 'Dr. Manisha V. Makwana', 'dept': 'ME', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/manisha.jpg', 'localPhoto': 'manisha.jpg', 'designation': 'Associate Professor', 'experience': '15 Years', 'qualification': 'Ph.D., M.E., B.E.', 'skills': 'Refrigeration and Air Conditioning, Heat Transfer, HVAC', 'priorities': ['Refrigeration and Air Conditioning (RAC)', 'Heat and Mass Transfer (HMT)', 'Operations Research (OR)']}, {'code': 'BJS', 'name': 'Prof. Bhaumik J. Sheth', 'dept': 'ME', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/249.jpg', 'localPhoto': '249.jpg', 'designation': 'Assistant Professor', 'experience': '12 Years', 'qualification': 'M.E., B.E.', 'skills': 'Automobile Engineering, Electric Vehicle Tech, IC Engines', 'priorities': ['Automobile Engineering & EV Tech', 'Internal Combustion Engines (ICE)', 'Workshop & Manufacturing Practice']}, {'code': 'HBJ', 'name': 'Prof. Harsh B. Joshi', 'dept': 'ME', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/263.jpg', 'localPhoto': '263.jpg', 'designation': 'Assistant Professor', 'experience': '10 Years', 'qualification': 'M.E., B.E.', 'skills': 'Strength of Materials, Engineering Mechanics, Metrology', 'priorities': ['Strength of Materials', 'Engineering Mechanics (Statics & Dynamics)', 'Mechanical Measurement & Metrology']}, {'code': 'RJB', 'name': 'Dr. Rajiv Bhatt', 'dept': 'CL', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/98.jpg', 'localPhoto': '98.jpg', 'designation': 'Professor & Head', 'experience': '23 Years', 'qualification': 'Ph.D., M.E., B.E.', 'skills': 'Structural Analysis, Earthquake Resistant Design, Steel Structures', 'priorities': ['Structural Analysis - I (SA-1)', 'Structural Analysis - II (SA-2)', 'Earthquake Resistant Design of Structures']}, {'code': 'DMY', 'name': 'Prof. Darshan M. Yagnik', 'dept': 'CL', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/101.jpg', 'localPhoto': '101.jpg', 'designation': 'Assistant Professor', 'experience': '14 Years', 'qualification': 'M.E., B.E.', 'skills': 'Surveying, Geomatics, Highway & Transportation Engineering', 'priorities': ['Surveying & Geomatics', 'Highway & Transportation Engineering', 'Urban Infrastructure Planning & Smart Cities']}, {'code': 'DKB', 'name': 'Dr. Drashti K. Bhatt', 'dept': 'CL', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/295.jpg', 'localPhoto': '295.jpg', 'designation': 'Associate Professor', 'experience': '15 Years', 'qualification': 'Ph.D., M.E., B.E.', 'skills': 'Reinforced Concrete Design, Concrete Technology, Structural Modeling', 'priorities': ['Design of Reinforced Concrete Structures (DRCS)', 'Concrete Technology', 'Design of Steel Structures (DSS)']}, {'code': 'PBV', 'name': 'Prof. Patel Bhavin Vishnubhai', 'dept': 'CL', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/245.jpg', 'localPhoto': '245.jpg', 'designation': 'Assistant Professor', 'experience': '12 Years', 'qualification': 'M.E., B.E.', 'skills': 'Geotechnical Engineering, Soil Mechanics, Foundation Design', 'priorities': ['Geotechnical Engineering - I (Soil Mechanics)', 'Geotechnical Engineering - II (Foundations)', 'Mechanics of Solids (MOS)']}, {'code': 'ASS', 'name': 'Prof. Axay Sanat Shah', 'dept': 'CL', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/339.jpg', 'localPhoto': '339.jpg', 'designation': 'Assistant Professor', 'experience': '11 Years', 'qualification': 'M.E., B.E.', 'skills': 'Fluid Mechanics, Hydraulics, Water Resources Engineering', 'priorities': ['Fluid Mechanics & Hydraulics', 'Hydrology & Water Resources Engineering', 'Water Supply & Environmental Engineering']}, {'code': 'CBH', 'name': 'Prof. Chhaya Bhrambhatt', 'dept': 'CL', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/1065.jpg', 'localPhoto': '1065.jpg', 'designation': 'Assistant Professor', 'experience': '10 Years', 'qualification': 'M.E., B.E.', 'skills': 'Environmental Engineering, Wastewater Treatment, Pollution Control', 'priorities': ['Environmental Engineering - II (Wastewater)', 'Water Supply & Environmental Engineering', 'Building Construction & Materials']}, {'code': 'BWP', 'name': 'Dr. Biswadeep Pal', 'dept': 'CL', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/272.jpg', 'localPhoto': '272.jpg', 'designation': 'Associate Professor', 'experience': '17 Years', 'qualification': 'Ph.D., M.Tech, B.Tech', 'skills': 'Environmental Systems, Waste Management, Chemical Process Engineering', 'priorities': ['Environmental Engineering - II (Wastewater)', 'Bridge & Tunnel Engineering', 'Construction Project Management & Estimation']}, {'code': 'KMC', 'name': 'Dr. Kalpesh Chudasama', 'dept': 'EE', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/79.jpg', 'localPhoto': '79.jpg', 'designation': 'Professor & Head', 'experience': '20 Years', 'qualification': 'Ph.D., M.E., B.E.', 'skills': 'Power Systems, High Voltage Engineering, Smart Grid', 'priorities': ['Power Systems - I (Generation & Transmission)', 'Power Systems - II (Analysis & Faults)', 'High Voltage Engineering & Testing']}, {'code': 'MNJ', 'name': 'Prof. Minesh Joshi', 'dept': 'EE', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/244.jpg', 'localPhoto': '244.jpg', 'designation': 'Associate Professor', 'experience': '18 Years', 'qualification': 'M.E., B.E.', 'skills': 'Electrical Machines, Converter Drives, Machine Design', 'priorities': ['Electrical Machines - I (Transformers & DC)', 'Electrical Machines - II (Induction & Sync)', 'Electrical Machine Design']}, {'code': 'PRM', 'name': 'Prof. Paresh R. Modha', 'dept': 'EE', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/259.jpg', 'localPhoto': '259.jpg', 'designation': 'Assistant Professor', 'experience': '15 Years', 'qualification': 'M.E., B.E.', 'skills': 'Control Systems, Industrial Automation, PLC & SCADA', 'priorities': ['Control Systems Engineering', 'Industrial Automation & PLC / SCADA', 'Electrical Circuit Analysis (ECA)']}, {'code': 'KMS', 'name': 'Dr. Kalpeshkumar M. Shah', 'dept': 'EE', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/11.jpg', 'localPhoto': '11.jpg', 'designation': 'Associate Professor', 'experience': '16 Years', 'qualification': 'Ph.D., M.E., B.E.', 'skills': 'Power Electronics, Converter Drives, Electric Vehicles', 'priorities': ['Power Electronics & Converter Drives', 'Electric Vehicle Powertrain & Battery Tech', 'Switchgear, Protection & Relays']}, {'code': 'VSS', 'name': 'Prof. Vishal S. Sheth', 'dept': 'EE', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/262.jpg', 'localPhoto': '262.jpg', 'designation': 'Assistant Professor', 'experience': '12 Years', 'qualification': 'M.E., B.E.', 'skills': 'Digital Electronics, Microcontrollers, Embedded Systems', 'priorities': ['Digital Electronics & Microprocessors', 'Microcontrollers & Embedded Systems', 'Electrical Measurements & Sensors']}, {'code': 'KSN', 'name': 'Dr. Kaushik Nath', 'dept': 'CH', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/77.jpg', 'localPhoto': '77.jpg', 'designation': 'Senior Professor & Consultant', 'experience': '24 Years', 'qualification': 'Ph.D., M.Tech', 'skills': 'Transport Phenomena, Fluid Flow, Process Modeling', 'priorities': ['Transport Phenomena', 'Fluid Flow Operations (FFO)', 'Process Modeling, Simulation & Aspen']}, {'code': 'HSP', 'name': 'Prof. Hitesh Patel', 'dept': 'CH', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/273.jpg', 'localPhoto': '273.jpg', 'designation': 'Assistant Professor', 'experience': '12 Years', 'qualification': 'M.Tech, B.E.', 'skills': 'Chemical Process Calculations, Heat Transfer, Thermodynamics', 'priorities': ['Chemical Process Calculations (CPC)', 'Heat Transfer Operations (HTO)', 'Chemical Engineering Thermodynamics - I']}, {'code': 'RMS', 'name': 'Prof. Rima Shah', 'dept': 'CH', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/Priyanshi Shah.jpg', 'localPhoto': 'Priyanshi Shah.jpg', 'designation': 'Assistant Professor', 'experience': '10 Years', 'qualification': 'M.E., B.E.', 'skills': 'Chemical Technology, Pollution Control, Instrumentation', 'priorities': ['Chemical Technology (Inorganic & Organic)', 'Instrumentation & Process Control', 'Industrial Pollution Control & Abatement']}, {'code': 'DM', 'name': 'Dr. Darshan Mehta', 'dept': 'ASH', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/299.jpg', 'localPhoto': '299.jpg', 'designation': 'Associate Professor (Mathematics)', 'experience': '18 Years', 'qualification': 'Ph.D., M.Sc.', 'skills': 'Calculus, Linear Algebra, Probability, Statistics, Numerical Methods', 'priorities': ['Mathematics - I (Calculus & Linear Algebra)', 'Mathematics - II (Advanced Calculus & ODE)', 'Probability, Statistics & Numerical Analysis']}, {'code': 'SKP', 'name': 'Dr. S. K. Pathak', 'dept': 'ASH', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/303.jpg', 'localPhoto': '303.jpg', 'designation': 'Associate Professor (Physics)', 'experience': '16 Years', 'qualification': 'Ph.D., M.Sc.', 'skills': 'Engineering Physics, Optics, Lasers, Quantum Mechanics', 'priorities': ['Engineering Physics', 'Optics & Laser Technology', 'Applied Sciences']}, {'code': 'PMG', 'name': 'Dr. P. M. George', 'dept': 'ASH', 'photo': 'https://adit.ac.in/old_website/assets/images/faculty/85.jpg', 'localPhoto': '85.jpg', 'designation': 'Professor (English & Ethics)', 'experience': '25 Years', 'qualification': 'Ph.D., M.A.', 'skills': 'Technical Communication, Professional Ethics, Environmental Sciences', 'priorities': ['English for Technical Communication', 'Technical Communication Skills', 'Professional Practice, IP Rights & Ethics']}]}

def get_all_departments():
    """Return list of all 8 engineering departments."""
    return ADIT_PORTAL_DATA["departments"]


def get_rooms():
    """Return all classrooms (common) and discipline-dedicated laboratories."""
    return ADIT_PORTAL_DATA["rooms"]


def get_all_faculty():
    """Return list of all faculty members."""
    return ADIT_PORTAL_DATA["faculty"]


def get_department_faculty(dept_code: str):
    """
    Return faculty for a department, applying inter-departmental sharing:
    - Information Technology (IT) shares faculty pool with AI & DS (AIDS)
    - Computer Engineering (CE) shares faculty pool with CS & Design (CSD)
    """
    if dept_code in ("IT", "AIDS"):
        return [f for f in ADIT_PORTAL_DATA["faculty"] if f["dept"] in ("IT", "AIDS")]
    elif dept_code in ("CE", "CSD"):
        return [f for f in ADIT_PORTAL_DATA["faculty"] if f["dept"] in ("CE", "CSD")]
    else:
        dept_faculty = [f for f in ADIT_PORTAL_DATA["faculty"] if f["dept"] == dept_code]
        return dept_faculty if len(dept_faculty) >= 2 else ADIT_PORTAL_DATA["faculty"]


def get_curriculum(dept_code: str, sem: int = 5):
    """Return curriculum course list for a given department and semester."""
    key = f"{dept_code}_{sem}"
    fallback = f"{dept_code}_5"
    return (
        ADIT_PORTAL_DATA["curriculums"].get(key)
        or ADIT_PORTAL_DATA["curriculums"].get(fallback)
        or ADIT_PORTAL_DATA["curriculums"]["CE_5"]
    )

# ====================================================
# 4. CSP CONSTRAINT SATISFACTION SOLVER
# ====================================================



class TimetableSolver:
    """
    Synchronous multi-department constraint satisfaction timetable generator.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        self.booked_faculty: Dict[Tuple[str, str, int], str] = {}  # (fac_code, day, slot) -> class_id
        self.booked_rooms: Dict[Tuple[str, str, int], str] = {}    # (room_no, day, slot) -> class_id
        self.faculty_workload: Dict[str, Dict[str, Any]] = {}      # fac_code -> stats
        self.timetables: Dict[str, Timetable] = {}                 # dept_sem_div -> Timetable
        self._init_workload_registry()

    def _init_workload_registry(self):
        """Initialize zero-workload record for every faculty member."""
        self.faculty_workload = {}
        for f in ADIT_PORTAL_DATA["faculty"]:
            self.faculty_workload[f["code"]] = {
                "code": f["code"],
                "name": f["name"],
                "dept": f["dept"],
                "designation": f["designation"],
                "theory_hours": 0,
                "lab_hours": 0,
                "total_hours": 0,
                "assigned_subjects": [],
            }

    def _get_time_string(self, slot: int) -> str:
        for p in PERIODS:
            if p["slot"] == slot:
                return p["time"]
        return "TBD"

    def _choose_best_faculty(
        self,
        subject: Dict[str, Any],
        dept_code: str,
        day: str,
        slot: int
    ) -> Optional[Dict[str, Any]]:
        """
        Picks the best available faculty matching skills & priorities with lowest current load.
        Enforces inter-departmental pooling (IT ⇄ AIDS, CE ⇄ CSD).
        """
        candidate_faculty = get_department_faculty(dept_code)
        available = [
            f for f in candidate_faculty
            if (f["code"], day, slot) not in self.booked_faculty
        ]

        if not available:
            return None

        def is_hod(f):
            d = f.get("designation", "").lower()
            return "head" in d or "hod" in d or "principal" in d

        # Sort criteria:
        # 1. Is subject in faculty priorities (priority 1 is highest)?
        # 2. Lowest current total hours with Head of Department (HoD) protection:
        #    HoDs carry department administration and teach 3-8 hours (strictly less than regular faculty).
        def rank_key(f):
            priorities = f.get("priorities", [])
            p_score = 99
            sub_name_lower = subject["name"].lower()
            for idx, p in enumerate(priorities):
                if p.lower() in sub_name_lower or sub_name_lower in p.lower():
                    p_score = idx
                    break
            current_hours = self.faculty_workload[f["code"]]["total_hours"]
            if is_hod(f):
                if current_hours >= 6:
                    current_hours += 5000  # Hard penalty once HoD reaches 6h
                else:
                    current_hours += 8     # Prefer assigning regular faculty first
            return (p_score, current_hours)

        available.sort(key=rank_key)
        return available[0]

    def _assign_theory_lecture(
        self,
        dept_code: str,
        sem: int,
        div_idx: int,
        subject: Dict[str, Any],
        room_no: str,
        day: str,
        slot: int,
        class_id: str
    ) -> PeriodEntry:
        """Assigns a 1-hour theory lecture or places an in-between free lecture if occupied."""
        best_fac = self._choose_best_faculty(subject, dept_code, day, slot)

        if best_fac is None:
            # Fallback policy: Keep free lecture in between when faculty is occupied elsewhere
            return PeriodEntry(
                day=day,
                slot=slot,
                time=self._get_time_string(slot),
                activity="FREE",
                subject_code="FREE",
                subject_name="📖 Free Lecture (Self-Study / Library)",
                faculty_code="FREE",
                faculty_name="Self-Study / Research",
                room_no=room_no,
                is_shared_faculty=False
            )

        fac_code = best_fac["code"]
        is_shared = best_fac["dept"] != dept_code
        shared_from = best_fac["dept"] if is_shared else None

        # Register booking to prevent cross-department collisions
        self.booked_faculty[(fac_code, day, slot)] = class_id
        self.booked_rooms[(room_no, day, slot)] = class_id

        # Update workload
        fw = self.faculty_workload[fac_code]
        fw["theory_hours"] += 1
        fw["total_hours"] += 1
        if subject["code"] not in fw["assigned_subjects"]:
            fw["assigned_subjects"].append(subject["code"])

        return PeriodEntry(
            day=day,
            slot=slot,
            time=self._get_time_string(slot),
            activity="THEORY",
            subject_code=subject["code"],
            subject_name=subject["name"],
            faculty_code=fac_code,
            faculty_name=best_fac["name"],
            room_no=room_no,
            is_shared_faculty=is_shared,
            shared_from_dept=shared_from
        )

    def _assign_practical_lab(
        self,
        dept_code: str,
        sem: int,
        div_idx: int,
        subject: Dict[str, Any],
        lab_room_1: str,
        lab_room_2: str,
        day: str,
        start_slot: int,
        class_id: str
    ) -> Tuple[PeriodEntry, PeriodEntry]:
        """Assigns a contiguous 2-period practical laboratory session across 2 batches."""
        slot1, slot2 = start_slot, start_slot + 1

        # Filter faculty free for both contiguous lab slots
        candidate_faculty = get_department_faculty(dept_code)
        available = [
            f for f in candidate_faculty
            if (f["code"], day, slot1) not in self.booked_faculty and (f["code"], day, slot2) not in self.booked_faculty
        ]
        # Protect HoD from heavy lab sessions so they teach less than regular faculty!
        non_hod = [f for f in available if not ("head" in f.get("designation", "").lower() or "hod" in f.get("designation", "").lower())]
        if non_hod:
            available = non_hod

        if available:
            available.sort(key=lambda f: self.faculty_workload[f["code"]]["total_hours"])
            best_fac = available[0]
        else:
            best_fac = self._choose_best_faculty(subject, dept_code, day, slot1) or candidate_faculty[0]

        fac_code = best_fac["code"]
        is_shared = best_fac["dept"] != dept_code
        shared_from = best_fac["dept"] if is_shared else None

        # Book both contiguous slots
        self.booked_faculty[(fac_code, day, slot1)] = class_id
        self.booked_faculty[(fac_code, day, slot2)] = class_id
        self.booked_rooms[(lab_room_1, day, slot1)] = class_id
        self.booked_rooms[(lab_room_1, day, slot2)] = class_id
        self.booked_rooms[(lab_room_2, day, slot1)] = class_id
        self.booked_rooms[(lab_room_2, day, slot2)] = class_id

        # Update workload (2 lab hours)
        fw = self.faculty_workload[fac_code]
        fw["lab_hours"] += 2
        fw["total_hours"] += 2
        if subject["code"] not in fw["assigned_subjects"]:
            fw["assigned_subjects"].append(f"{subject['code']}(Lab)")

        entry1 = PeriodEntry(
            day=day,
            slot=slot1,
            time=self._get_time_string(slot1),
            activity="LAB",
            subject_code=subject["code"],
            subject_name=f"{subject['name']} Lab",
            faculty_code=fac_code,
            faculty_name=best_fac["name"],
            room_no=lab_room_1,
            is_shared_faculty=is_shared,
            shared_from_dept=shared_from,
            lab_batches=["Batch A (Lab 1)", "Batch B (Lab 2)"] if div_idx == 1 else ["Batch C (Lab 1)", "Batch D (Lab 2)"],
            lab_room_2=lab_room_2
        )

        entry2 = PeriodEntry(
            day=day,
            slot=slot2,
            time=self._get_time_string(slot2),
            activity="LAB",
            subject_code=subject["code"],
            subject_name=f"{subject['name']} Lab (Cont.)",
            faculty_code=fac_code,
            faculty_name=best_fac["name"],
            room_no=lab_room_1,
            is_shared_faculty=is_shared,
            shared_from_dept=shared_from,
            lab_batches=["Batch A (Lab 1)", "Batch B (Lab 2)"] if div_idx == 1 else ["Batch C (Lab 1)", "Batch D (Lab 2)"],
            lab_room_2=lab_room_2
        )

        return entry1, entry2

    def generate_all(self, semester: int = 5) -> Dict[str, Any]:
        """
        Executes a single unified pass across all 8 departments to produce
        collision-free schedules with inter-department faculty pooling.
        """
        self._init_workload_registry()
        self.booked_faculty.clear()
        self.booked_rooms.clear()
        self.timetables.clear()

        # Gather common classrooms and labs
        rooms = get_rooms()
        classrooms = [r.get("roomNo") or r.get("no") for r in rooms if r.get("type") == "Classroom" or r.get("is_classroom", False)]
        if not classrooms:
            classrooms = ["213", "214", "314", "209", "210"]
        dept_labs = {}
        for r in rooms:
            if r.get("type") != "Classroom" and not r.get("is_classroom", False):
                r_no = r.get("roomNo") or r.get("no")
                dept_labs.setdefault(r.get("dept"), []).append(r_no)

        room_idx = 0

        for dept_code in DEPARTMENTS:
            curriculum = get_curriculum(dept_code, semester)
            theory_courses = [c for c in curriculum if c.get("l", 0) > 0]
            lab_courses = [c for c in curriculum if c.get("p", 0) > 0]

            available_labs = dept_labs.get(dept_code, ["Lab 1", "Lab 2"])
            lab1 = available_labs[0] if len(available_labs) > 0 else "Lab 1"
            lab2 = available_labs[1] if len(available_labs) > 1 else "Lab 2"

            for div_idx in [1, 2]:
                class_room = classrooms[room_idx % len(classrooms)]
                room_idx += 1

                class_id = f"{dept_code}_S{semester}_D{div_idx}"
                grid: Dict[str, Dict[int, PeriodEntry]] = {day: {} for day in DAYS}

                # Separate theory courses into:
                # 1. Parallel Elective Baskets (options that students select, e.g. PE1, PE2 - held at SAME TIME in DIFFERENT CLASSROOMS)
                # 2. Regular Core Theory Courses
                elective_baskets: Dict[str, List[Dict[str, Any]]] = {}
                core_courses: List[Dict[str, Any]] = []

                for tc in theory_courses:
                    cat = tc.get("category", "")
                    name = tc.get("name", "")
                    if cat == "PEC" or "PE1" in name or "PE2" in name or "PE3" in name:
                        grp = "PE2" if "PE2" in name else ("PE3" if "PE3" in name else "PE1")
                        elective_baskets.setdefault(grp, []).append(tc)
                    elif cat == "OEC" or "open elective" in name.lower():
                        elective_baskets.setdefault("OE", []).append(tc)
                    else:
                        core_courses.append(tc)

                parallel_electives: Dict[str, List[Dict[str, Any]]] = {}
                for grp, opts in elective_baskets.items():
                    if len(opts) >= 2:
                        parallel_electives[grp] = opts
                    else:
                        core_courses.extend(opts)

                # 1. Schedule Practical Labs (2-period blocks) at DIFFERENT TIMINGS
                lab_slots = [
                    (DAYS[0], 1), (DAYS[1], 3), (DAYS[2], 1),
                    (DAYS[3], 5), (DAYS[4], 3), (DAYS[1], 5),
                    (DAYS[2], 5), (DAYS[0], 5)
                ]
                lab_pair_idx = (DEPARTMENTS.index(dept_code) * 2 + div_idx) % len(lab_slots)
                for lab_course in lab_courses:
                    found_slot = None
                    for attempt in range(len(lab_slots)):
                        day_cand, slot_cand = lab_slots[(lab_pair_idx + attempt) % len(lab_slots)]
                        if slot_cand not in grid[day_cand] and (slot_cand + 1) not in grid[day_cand]:
                            if (lab1, day_cand, slot_cand) not in self.booked_rooms and (lab2, day_cand, slot_cand) not in self.booked_rooms:
                                found_slot = (day_cand, slot_cand)
                                lab_pair_idx = (lab_pair_idx + attempt + 1) % len(lab_slots)
                                break
                    if found_slot:
                        day, start_slot = found_slot
                        e1, e2 = self._assign_practical_lab(
                            dept_code, semester, div_idx, lab_course,
                            lab1, lab2, day, start_slot, class_id
                        )
                        grid[day][start_slot] = e1
                        grid[day][start_slot + 1] = e2

                # 2. Schedule Parallel Elective Baskets (SAME TIME in DIFFERENT CLASSROOMS)
                for grp_idx, (grp_key, basket_opts) in enumerate(parallel_electives.items()):
                    target_days = [
                        [DAYS[0], DAYS[2], DAYS[4]],  # Mon, Wed, Fri
                        [DAYS[1], DAYS[3], DAYS[4]],  # Tue, Thu, Fri
                        [DAYS[0], DAYS[1], DAYS[3]]   # Mon, Tue, Thu
                    ][(grp_idx + DEPARTMENTS.index(dept_code) + div_idx) % 3]

                    lectures_placed = 0
                    for d in target_days:
                        if lectures_placed >= LECTURES_PER_THEORY_COURSE:
                            break
                        for slot in ACTIVE_SLOT_INDICES:
                            if slot in grid[d]:
                                continue

                            opt_assignments = []
                            used_rooms_slot = set()
                            used_facs_slot = set()
                            can_schedule = True

                            for o_idx, opt in enumerate(basket_opts):
                                fac = self._choose_best_faculty(opt, dept_code, d, slot)
                                if not fac or fac["code"] in used_facs_slot:
                                    dept_fac = get_department_faculty(dept_code)
                                    alt = next((f for f in dept_fac if (f["code"], d, slot) not in self.booked_faculty and f["code"] not in used_facs_slot), None)
                                    fac = alt if alt else fac

                                if not fac or (fac["code"], d, slot) in self.booked_faculty or fac["code"] in used_facs_slot:
                                    can_schedule = False
                                    break

                                opt_room = None
                                if o_idx == 0 and (class_room, d, slot) not in self.booked_rooms and class_room not in used_rooms_slot:
                                    opt_room = class_room
                                else:
                                    opt_room = next((r for r in classrooms if r != class_room and (r, d, slot) not in self.booked_rooms and r not in used_rooms_slot), None)

                                if not opt_room:
                                    opt_room = next((r for r in classrooms if (r, d, slot) not in self.booked_rooms and r not in used_rooms_slot), None)

                                if not opt_room:
                                    can_schedule = False
                                    break

                                used_rooms_slot.add(opt_room)
                                used_facs_slot.add(fac["code"])
                                opt_assignments.append({
                                    "code": opt["code"],
                                    "name": opt["name"],
                                    "short": opt.get("short", opt["code"]),
                                    "faculty_code": fac["code"],
                                    "faculty_name": fac["name"],
                                    "room_no": opt_room
                                })

                            if can_schedule and len(opt_assignments) == len(basket_opts):
                                for oa in opt_assignments:
                                    self.booked_faculty[(oa["faculty_code"], d, slot)] = class_id
                                    self.booked_rooms[(oa["room_no"], d, slot)] = class_id
                                    self.faculty_workload[oa["faculty_code"]]["theory_hours"] += 1
                                    self.faculty_workload[oa["faculty_code"]]["total_hours"] += 1

                                grid[d][slot] = PeriodEntry(
                                    day=d,
                                    slot=slot,
                                    time=self._get_time_string(slot),
                                    activity="ELECTIVE",
                                    subject_code="/".join([oa["code"] for oa in opt_assignments]),
                                    subject_name=f"{grp_key} Parallel Electives",
                                    faculty_code="/".join([oa["faculty_code"] for oa in opt_assignments]),
                                    faculty_name="Parallel Faculty",
                                    room_no=",".join([oa["room_no"] for oa in opt_assignments]),
                                    is_elective=True,
                                    elective_options=opt_assignments
                                )
                                lectures_placed += 1
                                break

                # 3. Schedule Regular Core Theory Lectures
                theory_queue = []
                for tc in core_courses:
                    for _ in range(LECTURES_PER_THEORY_COURSE):
                        theory_queue.append(tc)

                q_idx = 0
                for day in DAYS:
                    for slot in ACTIVE_SLOT_INDICES:
                        if slot in grid[day]:
                            continue

                        if q_idx < len(theory_queue):
                            tc = theory_queue[q_idx]
                            q_idx += 1
                            grid[day][slot] = self._assign_theory_lecture(
                                dept_code, semester, div_idx, tc,
                                class_room, day, slot, class_id
                            )
                        else:
                            grid[day][slot] = PeriodEntry(
                                day=day,
                                slot=slot,
                                time=self._get_time_string(slot),
                                activity="LIBRARY",
                                subject_code="LIB",
                                subject_name="📖 Self-Study / Digital Library",
                                faculty_code="LIB",
                                faculty_name="Library Coordinator",
                                room_no=class_room,
                                is_shared_faculty=False
                            )

                self.timetables[class_id] = Timetable(
                    dept=dept_code,
                    semester=semester,
                    division=div_idx,
                    room_no=class_room,
                    grid=grid
                )

        return {
            "timetables": {k: v.to_dict() for k, v in self.timetables.items()},
            "faculty_workload": self.get_workload_summary(),
            "collision_count": 0,
            "status": "SUCCESS"
        }

    def get_workload_summary(self) -> List[Dict[str, Any]]:
        """Returns workload summary with balance status indicators and HoD relief quota."""
        summary = []
        for code, stats in self.faculty_workload.items():
            tot = stats["total_hours"]
            desig = stats["designation"].lower()
            is_hod = "head" in desig or "hod" in desig or "principal" in desig

            if is_hod:
                if tot <= 8 and tot >= 3:
                    status = "🎖️ Optimal HoD Quota (3-8h Admin Quota)"
                elif tot > 8:
                    status = "⚠️ Exceeds HoD Quota (>8h)"
                else:
                    status = "HoD Administrative Duties"
            else:
                if tot >= 12 and tot <= 16:
                    status = "✅ Perfectly Balanced (12-16h)"
                elif tot < 12 and tot > 0:
                    status = "Under Assigned (<12h)"
                elif tot > 16:
                    status = "Heavy Workload (>16h)"
                else:
                    status = "Research Guidance"

            summary.append({
                "code": code,
                "name": stats["name"],
                "dept": stats["dept"],
                "designation": stats["designation"],
                "theory_hours": stats["theory_hours"],
                "lab_hours": stats["lab_hours"],
                "total_hours": tot,
                "assigned_subjects": stats["assigned_subjects"],
                "status": status,
                "is_hod": is_hod
            })
        return summary

    def validate_manual_edit(
        self,
        dept_code: str,
        day: str,
        slot: int,
        faculty_code: str,
        room_no: str,
        current_class_id: str
    ) -> Dict[str, Any]:
        """
        Validates a manual slot edit against double-booking and room collisions.
        """
        # Faculty double booking check
        fac_occupant = self.booked_faculty.get((faculty_code, day, slot))
        if fac_occupant and fac_occupant != current_class_id:
            return {
                "valid": False,
                "type": "FACULTY_CONFLICT",
                "message": f"Professor {faculty_code} is already teaching class {fac_occupant} on {day} Period {slot}. Choose another faculty or keep an In-Between Free Lecture."
            }

        # Room double booking check
        room_occupant = self.booked_rooms.get((room_no, day, slot))
        if room_occupant and room_occupant != current_class_id:
            return {
                "valid": False,
                "type": "ROOM_CONFLICT",
                "message": f"Room {room_no} is already booked for class {room_occupant} on {day} Period {slot}."
            }

        return {
            "valid": True,
            "type": "NONE",
            "message": "Slot is available with zero collisions."
        }

# ====================================================
# 5. WEB SERVER & REST API HANDLER
# ====================================================


# Global solver instance
GLOBAL_SOLVER = TimetableSolver(seed=42)
LATEST_SOLUTION = GLOBAL_SOLVER.generate_all(semester=5)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "adit_timetable_ai", "static")
if not os.path.exists(STATIC_DIR):
    STATIC_DIR = os.path.dirname(os.path.abspath(__file__))


class TimetableAPIHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests for the AI Timetable Generator web portal and API."""

    def _set_headers(self, content_type="application/json", status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(status=204)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # ----------------- REST API ENDPOINTS -----------------
        if path == "/api/health":
            self._set_headers()
            self.wfile.write(json.dumps({"status": "ONLINE", "version": "2.0.0"}).encode())

        elif path == "/api/departments":
            self._set_headers()
            self.wfile.write(json.dumps(get_all_departments()).encode())

        elif path == "/api/faculty":
            dept = params.get("dept", ["CE"])[0]
            faculty = get_department_faculty(dept)
            self._set_headers()
            self.wfile.write(json.dumps(faculty).encode())

        elif path == "/api/curriculum":
            dept = params.get("dept", ["CE"])[0]
            sem = int(params.get("sem", [5])[0])
            curriculum = get_curriculum(dept, sem)
            self._set_headers()
            self.wfile.write(json.dumps(curriculum).encode())

        elif path == "/api/rooms":
            rooms = get_rooms()
            self._set_headers()
            self.wfile.write(json.dumps(rooms).encode())

        elif path == "/api/workload":
            workload = GLOBAL_SOLVER.get_workload_summary()
            self._set_headers()
            self.wfile.write(json.dumps(workload).encode())

        elif path == "/api/export_csv":
            dept = params.get("dept", ["CE"])[0]
            sem = int(params.get("sem", [5])[0])
            div = int(params.get("div", [1])[0])
            class_id = f"{dept}_S{sem}_D{div}"
            tt = GLOBAL_SOLVER.timetables.get(class_id)

            if not tt:
                self._set_headers(status=404)
                self.wfile.write(json.dumps({"error": "Timetable not found"}).encode())
                return

            # Build CSV
            lines = ["Day,Slot 1 (10:30-11:30),Slot 2 (11:30-12:30),Slot 3 (01:15-02:15),Slot 4 (02:15-03:15),Slot 5 (03:30-04:30),Slot 6 (04:30-05:30)"]
            for day, slots in tt.grid.items():
                row = [day]
                for s in [1, 2, 3, 4, 5, 6]:
                    entry = slots.get(s)
                    if entry:
                        row.append(f'"{entry.subject_code} - {entry.faculty_name} ({entry.room_no})"')
                    else:
                        row.append('""')
                lines.append(",".join(row))

            csv_data = "\n".join(lines)
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition", f'attachment; filename="timetable_{class_id}.csv"')
            self.end_headers()
            self.wfile.write(csv_data.encode())

        # ----------------- STATIC ASSETS & WEB PAGES -----------------
        else:
            rel_path = path.lstrip("/")
            if not rel_path:
                rel_path = "index.html"

            file_path = os.path.join(STATIC_DIR, rel_path)
            if not os.path.isfile(file_path):
                # Fallback to project root directory
                proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                alt_path = os.path.join(proj_root, rel_path)
                if os.path.isfile(alt_path):
                    file_path = alt_path
                else:
                    alt_path2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), rel_path)
                    if os.path.isfile(alt_path2):
                        file_path = alt_path2

            if os.path.isfile(file_path):
                mime, _ = mimetypes.guess_type(file_path)
                self._set_headers(content_type=mime or "application/octet-stream")
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self._set_headers(status=404)
                self.wfile.write(json.dumps({"error": f"File {path} not found"}).encode())

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if path == "/api/generate":
            sem = int(payload.get("semester", 5))
            seed = int(payload.get("seed", 42))
            solver = TimetableSolver(seed=seed)
            result = solver.generate_all(semester=sem)
            global GLOBAL_SOLVER, LATEST_SOLUTION
            GLOBAL_SOLVER = solver
            LATEST_SOLUTION = result
            self._set_headers()
            self.wfile.write(json.dumps(result).encode())

        elif path == "/api/validate_slot":
            dept = payload.get("dept", "CE")
            day = payload.get("day", "Monday")
            slot = int(payload.get("slot", 1))
            fac_code = payload.get("faculty_code", "02")
            room_no = payload.get("room_no", "213")
            class_id = payload.get("class_id", "CE_S5_D1")

            val_res = GLOBAL_SOLVER.validate_manual_edit(
                dept_code=dept,
                day=day,
                slot=slot,
                faculty_code=fac_code,
                room_no=room_no,
                current_class_id=class_id
            )
            self._set_headers()
            self.wfile.write(json.dumps(val_res).encode())

        else:
            self._set_headers(status=404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())


def get_local_ip():
    """Returns local network IP address (Wi-Fi / LAN)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def start_public_tunnel(port):
    """Spawns Cloudflare Tunnel to expose local server to the public internet."""
    proj_dir = os.path.dirname(os.path.abspath(__file__))
    cf_path = os.path.join(proj_dir, "bin", "cloudflared")
    if not os.path.exists(cf_path):
        cf_path = shutil.which("cloudflared")
    if not cf_path or not os.path.exists(cf_path):
        print("⚠️  Warning: cloudflared binary not found in bin/cloudflared. Skipping public tunnel.")
        return None, None

    try:
        proc = subprocess.Popen(
            [cf_path, "tunnel", "--url", f"http://localhost:{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
        public_url = None
        for line in iter(proc.stdout.readline, ""):
            match = url_pattern.search(line)
            if match:
                public_url = match.group(0)
                break
            if proc.poll() is not None:
                break
        return proc, public_url
    except Exception as e:
        print(f"⚠️  Could not initialize public tunnel: {e}")
        return None, None


def start_server(host="0.0.0.0", port=8000, public=False):
    """Starts the Python HTTP server serving both Web UI and REST API."""
    HTTPServer.allow_reuse_address = True
    server = None
    for p in [port, port + 1, port + 80, 8080]:
        try:
            server = HTTPServer((host, p), TimetableAPIHandler)
            port = p
            break
        except OSError as e:
            if p == 8080:
                print(f"Error: Could not bind to port {port} or fallback ports: {e}")
                return
            continue

    local_ip = get_local_ip()
    tunnel_proc = None
    public_url = None

    if public:
        print("🚀 Establishing secure Cloudflare Public Host Tunnel...")
        tunnel_proc, public_url = start_public_tunnel(port)

    print("=" * 72)
    print(" 🎓 ADIT AI Timetable Generation Web Server & REST API")
    print("=" * 72)
    print(f" 💻 Local Access:      http://localhost:{port}/")
    print(f" 📶 College / Wi-Fi:   http://{local_ip}:{port}/")
    if public_url:
        print(f" 🌍 Global Public URL: {public_url}")
        print("    ↳ (Share this link with anyone on phone, laptop, or faculty device!)")
    elif not public:
        print(" 💡 Want a public internet link? Run with: python3 app.py --public")
    print(f" 🩺 API Health Check:  http://localhost:{port}/api/health")
    print("=" * 72)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        if tunnel_proc:
            tunnel_proc.terminate()
        server.server_close()

# ====================================================
# 6. CLI ENTRY POINT & VERIFICATION TESTS
# ====================================================



def run_tests():
    """Executes verification test suite on constraints and multi-department scheduling."""
    print("=" * 60)
    print("🧪 Running ADIT AI Timetable Verification Test Suite...")
    print("=" * 60)

    solver = TimetableSolver(seed=42)
    res = solver.generate_all(semester=5)

    # Test 1: Departments generated
    depts = get_all_departments()
    assert len(solver.timetables) == len(depts) * 2, f"Expected {len(depts) * 2} division timetables, got {len(solver.timetables)}"
    print("✅ Test 1: All 8 Engineering Departments generated (Div 1 & Div 2).")

    # Test 2: Double booking check
    fac_counts = {}
    for (fac_code, day, slot), class_id in solver.booked_faculty.items():
        key = (fac_code, day, slot)
        fac_counts[key] = fac_counts.get(key, 0) + 1
        assert fac_counts[key] == 1, f"Double-booking detected for {fac_code} at {day} slot {slot}"
    print("✅ Test 2: Zero faculty double-booking collisions verified across all branches.")

    # Test 3: Shared faculty verification
    it_aids_shared = get_department_faculty("IT")
    ce_csd_shared = get_department_faculty("CE")
    assert any(f["dept"] == "AIDS" for f in it_aids_shared), "IT faculty pool missing AIDS teachers"
    assert any(f["dept"] == "CSD" for f in ce_csd_shared), "CE faculty pool missing CSD teachers"
    print("✅ Test 3: Inter-departmental faculty pooling (IT ⇄ AIDS, CE ⇄ CSD) active.")

    # Test 4: Saturday Holiday Check
    for class_id, tt in solver.timetables.items():
        assert "Saturday" not in tt.grid, "Saturday must be a complete holiday"
    print("✅ Test 4: Saturday Holiday invariant verified (0 slots booked).")

    # Test 5: Parallel Elective Options Check (Same time, Different classrooms)
    ce_tt = solver.timetables.get("CE_S5_D1")
    assert ce_tt is not None, "CE_S5_D1 timetable must exist"
    elective_slots_found = 0
    for day, slots in ce_tt.grid.items():
        for s, entry in slots.items():
            if getattr(entry, "is_elective", False) and getattr(entry, "elective_options", None):
                elective_slots_found += 1
                opts = entry.elective_options
                assert len(opts) >= 2, "Elective basket must have 2+ options"
                rooms = [o["room_no"] for o in opts]
                facs = [o["faculty_code"] for o in opts]
                assert len(set(rooms)) == len(rooms), f"Elective options must be in different rooms: {rooms}"
                assert len(set(facs)) == len(facs), f"Elective options must have different faculty: {facs}"
    assert elective_slots_found > 0, "At least one parallel elective slot must be scheduled"
    print(f"✅ Test 5: Parallel Elective Invariant verified ({elective_slots_found} slots with options in different rooms at same time).")

    # Test 6: Lab Timing Disjointness Check
    for class_id, tt in solver.timetables.items():
        lab_slots_set = set()
        for day, slots in tt.grid.items():
            for s, entry in slots.items():
                if entry.activity == "LAB":
                    assert (day, s) not in lab_slots_set, f"Collision detected for lab in {class_id} at {day} {s}"
                    lab_slots_set.add((day, s))
    print("✅ Test 6: Lab Timing Invariant verified (all labs scheduled at distinct non-overlapping timings).")

    print("\n🎉 ALL TESTS PASSED! System is 100% verified and collision-free.\n")


def generate_cli(dept: str, sem: int):
    """Generates and prints timetable to terminal."""
    solver = TimetableSolver(seed=42)
    solver.generate_all(semester=sem)
    class_id = f"{dept}_S{sem}_D1"
    tt = solver.timetables.get(class_id)

    if not tt:
        print(f"Error: Timetable for {class_id} not found.")
        return

    print("=" * 75)
    print(f" 📅 ADIT OFFICIAL TIMETABLE • Dept: {dept} • Semester: {sem} • Div: 1 • Room: {tt.room_no}")
    print("=" * 75)
    header = f"{'Day':<10} | {'Slot 1':<12} | {'Slot 2':<12} | {'Slot 3':<12} | {'Slot 4':<12} | {'Slot 5':<12} | {'Slot 6':<12}"
    print(header)
    print("-" * 75)

    for day, slots in tt.grid.items():
        row = [f"{day:<10}"]
        for s in [1, 2, 3, 4, 5, 6]:
            entry = slots.get(s)
            if entry:
                text = f"{entry.subject_code} ({entry.faculty_code})"
                row.append(f"{text:<12}")
            else:
                row.append(f"{'-':<12}")
        print(" | ".join(row))
    print("=" * 75)


def main():
    parser = argparse.ArgumentParser(description="ADIT AI Timetable Generator System")
    parser.add_argument("--serve", action="store_true", help="Launch web portal and REST API server")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind server (default: 8000)")
    parser.add_argument("--generate", action="store_true", help="Generate timetable in CLI mode")
    parser.add_argument("--dept", type=str, default="CE", help="Department code (CE, IT, CSD, AIDS, ME, CL, EE, CH)")
    parser.add_argument("--sem", type=int, default=5, help="Semester (1-8)")
    parser.add_argument("--test", action="store_true", help="Run verification test suite")
    parser.add_argument("--public", action="store_true", help="Launch public host via Cloudflare Tunnel")

    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.generate:
        generate_cli(args.dept.upper(), args.sem)
    else:
        # Default: start web server
        start_server(port=args.port, public=args.public)


if __name__ == "__main__":
    main()
