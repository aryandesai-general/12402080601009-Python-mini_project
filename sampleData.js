/**
 * Sample College Dataset for AI Timetable Maker
 * Includes realistic Engineering Departments:
 * 1. Computer Science & Engineering (CSE)
 * 2. Chemical Engineering (CHEM)
 * 3. Mechanical Engineering (MECH)
 */

export const SAMPLE_DATA = {
  config: {
    days: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    periods: [
      { id: "P1", name: "Period 1", time: "09:00 - 10:00", isBreak: false },
      { id: "P2", name: "Period 2", time: "10:00 - 11:00", isBreak: false },
      { id: "B1", name: "Morning Break", time: "11:00 - 11:20", isBreak: true },
      { id: "P3", name: "Period 3", time: "11:20 - 12:20", isBreak: false },
      { id: "P4", name: "Period 4", time: "12:20 - 01:20", isBreak: false },
      { id: "B2", name: "Lunch Break", time: "01:20 - 02:10", isBreak: true },
      { id: "P5", name: "Period 5", time: "02:10 - 03:10", isBreak: false },
      { id: "P6", name: "Period 6", time: "03:10 - 04:10", isBreak: false }
    ],
    maxConsecutiveLecturesPerTeacher: 2,
    academicPeriodIds: ["P1", "P2", "P3", "P4", "P5", "P6"]
  },

  rooms: [
    // Classrooms
    { id: "CR-101", name: "Classroom 101", type: "Classroom", labType: null, capacity: 60, floor: "1st Floor" },
    { id: "CR-102", name: "Classroom 102", type: "Classroom", labType: null, capacity: 60, floor: "1st Floor" },
    { id: "CR-201", name: "Classroom 201", type: "Classroom", labType: null, capacity: 60, floor: "2nd Floor" },
    { id: "CR-202", name: "Classroom 202", type: "Classroom", labType: null, capacity: 60, floor: "2nd Floor" },
    { id: "CR-301", name: "Classroom 301", type: "Classroom", labType: null, capacity: 60, floor: "3rd Floor" },
    
    // Specialized Labs
    { id: "LAB-CS1", name: "Turing Lab (Comp Lab 1)", type: "Lab", labType: "Computer Lab", capacity: 40, floor: "Ground Floor" },
    { id: "LAB-CS2", name: "Ada Lab (Comp Lab 2)", type: "Lab", labType: "Computer Lab", capacity: 40, floor: "Ground Floor" },
    { id: "LAB-CH1", name: "Curie Lab (Chemical Lab 1)", type: "Lab", labType: "Chemical Lab", capacity: 35, floor: "Chemical Wing" },
    { id: "LAB-CH2", name: "Lavoisier Lab (Chemical Lab 2)", type: "Lab", labType: "Chemical Lab", capacity: 35, floor: "Chemical Wing" },
    { id: "LAB-ME1", name: "Thermodynamics Lab (Mech Lab 1)", type: "Lab", labType: "Mechanical Lab", capacity: 35, floor: "Workshop Wing" },
    { id: "LAB-ME2", name: "CAD/CAM Simulation Lab (Mech Lab 2)", type: "Lab", labType: "Mechanical Lab", capacity: 35, floor: "Workshop Wing" }
  ],

  departments: [
    {
      id: "DEP-CSE",
      name: "Computer Science & Engineering",
      code: "CSE",
      divisions: [
        {
          id: "CSE-DIV-A",
          name: "CSE - Year 3 (Div A)",
          subjects: [
            { id: "SUB-CS301", name: "Operating Systems", type: "Theory", labType: null, weeklyHours: 3 },
            { id: "SUB-CS302", name: "Database Management Systems", type: "Theory", labType: null, weeklyHours: 3 },
            { id: "SUB-CS303", name: "Machine Learning Fundamentals", type: "Theory", labType: null, weeklyHours: 3 },
            { id: "SUB-CS304", name: "Computer Networks", type: "Theory", labType: null, weeklyHours: 3 },
            { id: "SUB-CS305L", name: "DBMS & SQL Laboratory", type: "Lab", labType: "Computer Lab", weeklyHours: 2, isLabBlock: true },
            { id: "SUB-CS306L", name: "Machine Learning Lab", type: "Lab", labType: "Computer Lab", weeklyHours: 2, isLabBlock: true }
          ]
        },
        {
          id: "CSE-DIV-B",
          name: "CSE - Year 3 (Div B)",
          subjects: [
            { id: "SUB-CS301", name: "Operating Systems", type: "Theory", labType: null, weeklyHours: 3 },
            { id: "SUB-CS302", name: "Database Management Systems", type: "Theory", labType: null, weeklyHours: 3 },
            { id: "SUB-CS303", name: "Machine Learning Fundamentals", type: "Theory", labType: null, weeklyHours: 3 },
            { id: "SUB-CS304", name: "Computer Networks", type: "Theory", labType: null, weeklyHours: 3 },
            { id: "SUB-CS305L", name: "DBMS & SQL Laboratory", type: "Lab", labType: "Computer Lab", weeklyHours: 2, isLabBlock: true },
            { id: "SUB-CS306L", name: "Machine Learning Lab", type: "Lab", labType: "Computer Lab", weeklyHours: 2, isLabBlock: true }
          ]
        }
      ]
    },
    {
      id: "DEP-CHEM",
      name: "Chemical Engineering",
      code: "CHEM",
      divisions: [
        {
          id: "CHEM-DIV-A",
          name: "Chemical - Year 3 (Div A)",
          subjects: [
            { id: "SUB-CH301", name: "Chemical Reaction Engineering", type: "Theory", labType: null, weeklyHours: 3 },
            { id: "SUB-CH302", name: "Mass Transfer Operations", type: "Theory", labType: null, weeklyHours: 3 },
            { id: "SUB-CH303", name: "Process Dynamics & Control", type: "Theory", labType: null, weeklyHours: 3 },
            { id: "SUB-CH304", name: "Organic Chemical Technology", type: "Theory", labType: null, weeklyHours: 3 },
            { id: "SUB-CH305L", name: "Chemical Reaction Engg Lab", type: "Lab", labType: "Chemical Lab", weeklyHours: 2, isLabBlock: true },
            { id: "SUB-CH306L", name: "Mass Transfer Laboratory", type: "Lab", labType: "Chemical Lab", weeklyHours: 2, isLabBlock: true }
          ]
        }
      ]
    },
    {
      id: "DEP-MECH",
      name: "Mechanical Engineering",
      code: "MECH",
      divisions: [
        {
          id: "MECH-DIV-A",
          name: "Mechanical - Year 3 (Div A)",
          subjects: [
            { id: "SUB-ME301", name: "Applied Thermodynamics", type: "Theory", labType: null, weeklyHours: 3 },
            { id: "SUB-ME302", name: "Fluid Mechanics & Turbomachinery", type: "Theory", labType: null, weeklyHours: 3 },
            { id: "SUB-ME303", name: "Design of Machine Elements", type: "Theory", labType: null, weeklyHours: 3 },
            { id: "SUB-ME304", name: "Manufacturing Processes", type: "Theory", labType: null, weeklyHours: 3 },
            { id: "SUB-ME305L", name: "Applied Thermodynamics Lab", type: "Lab", labType: "Mechanical Lab", weeklyHours: 2, isLabBlock: true },
            { id: "SUB-ME306L", name: "CAD/CAM Mechanical Lab", type: "Lab", labType: "Mechanical Lab", weeklyHours: 2, isLabBlock: true }
          ]
        }
      ]
    }
  ],

  faculty: [
    // Computer Science Faculty
    {
      id: "FAC-101",
      name: "Dr. Alan Sharma",
      department: "Computer Science & Engineering",
      email: "alan.sharma@college.edu",
      maxHoursPerDay: 4,
      priorities: [
        { priority: 1, subjectName: "Machine Learning Fundamentals" },
        { priority: 2, subjectName: "Machine Learning Lab" },
        { priority: 3, subjectName: "Operating Systems" }
      ]
    },
    {
      id: "FAC-102",
      name: "Prof. Priya Nair",
      department: "Computer Science & Engineering",
      email: "priya.nair@college.edu",
      maxHoursPerDay: 4,
      priorities: [
        { priority: 1, subjectName: "Database Management Systems" },
        { priority: 2, subjectName: "DBMS & SQL Laboratory" },
        { priority: 3, subjectName: "Computer Networks" }
      ]
    },
    {
      id: "FAC-103",
      name: "Prof. Rajesh Verma",
      department: "Computer Science & Engineering",
      email: "rajesh.verma@college.edu",
      maxHoursPerDay: 4,
      priorities: [
        { priority: 1, subjectName: "Operating Systems" },
        { priority: 2, subjectName: "Computer Networks" },
        { priority: 3, subjectName: "Database Management Systems" }
      ]
    },
    {
      id: "FAC-104",
      name: "Dr. Ananya Roy",
      department: "Computer Science & Engineering",
      email: "ananya.roy@college.edu",
      maxHoursPerDay: 4,
      priorities: [
        { priority: 1, subjectName: "Computer Networks" },
        { priority: 2, subjectName: "DBMS & SQL Laboratory" },
        { priority: 3, subjectName: "Machine Learning Fundamentals" }
      ]
    },

    // Chemical Engineering Faculty
    {
      id: "FAC-201",
      name: "Dr. Vikram Sethi",
      department: "Chemical Engineering",
      email: "vikram.sethi@college.edu",
      maxHoursPerDay: 4,
      priorities: [
        { priority: 1, subjectName: "Chemical Reaction Engineering" },
        { priority: 2, subjectName: "Chemical Reaction Engg Lab" },
        { priority: 3, subjectName: "Process Dynamics & Control" }
      ]
    },
    {
      id: "FAC-202",
      name: "Prof. Meera Kulkarni",
      department: "Chemical Engineering",
      email: "meera.k@college.edu",
      maxHoursPerDay: 4,
      priorities: [
        { priority: 1, subjectName: "Mass Transfer Operations" },
        { priority: 2, subjectName: "Mass Transfer Laboratory" },
        { priority: 3, subjectName: "Organic Chemical Technology" }
      ]
    },
    {
      id: "FAC-203",
      name: "Dr. Ramesh Patel",
      department: "Chemical Engineering",
      email: "ramesh.patel@college.edu",
      maxHoursPerDay: 4,
      priorities: [
        { priority: 1, subjectName: "Process Dynamics & Control" },
        { priority: 2, subjectName: "Organic Chemical Technology" },
        { priority: 3, subjectName: "Chemical Reaction Engineering" }
      ]
    },

    // Mechanical Engineering Faculty
    {
      id: "FAC-301",
      name: "Dr. Arvind Joshi",
      department: "Mechanical Engineering",
      email: "arvind.joshi@college.edu",
      maxHoursPerDay: 4,
      priorities: [
        { priority: 1, subjectName: "Applied Thermodynamics" },
        { priority: 2, subjectName: "Applied Thermodynamics Lab" },
        { priority: 3, subjectName: "Fluid Mechanics & Turbomachinery" }
      ]
    },
    {
      id: "FAC-302",
      name: "Prof. Sneha Deshmukh",
      department: "Mechanical Engineering",
      email: "sneha.d@college.edu",
      maxHoursPerDay: 4,
      priorities: [
        { priority: 1, subjectName: "Fluid Mechanics & Turbomachinery" },
        { priority: 2, subjectName: "Design of Machine Elements" },
        { priority: 3, subjectName: "CAD/CAM Mechanical Lab" }
      ]
    },
    {
      id: "FAC-303",
      name: "Dr. Gurpreet Singh",
      department: "Mechanical Engineering",
      email: "gurpreet.singh@college.edu",
      maxHoursPerDay: 4,
      priorities: [
        { priority: 1, subjectName: "Design of Machine Elements" },
        { priority: 2, subjectName: "Manufacturing Processes" },
        { priority: 3, subjectName: "CAD/CAM Mechanical Lab" }
      ]
    }
  ]
};
