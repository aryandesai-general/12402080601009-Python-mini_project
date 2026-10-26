# AI Timetable Maker & Intelligent Scheduler

An intelligent, multi-department academic timetable generator built for colleges, universities, and schools.

## Key Features
- **Faculty Priority Allocation**: Match faculty to subjects based on their ranked preferences (1st, 2nd, 3rd choice) and departmental affinity.
- **Department & Division Management**: Support for multiple departments (e.g. CSE, Mechanical, Chemical, Electrical) and their respective divisions/sections (Div A, Div B, etc.).
- **Specialized Lab & Classroom Routing**:
  - Classrooms for theory lectures.
  - Dedicated labs (Computer Lab, Chemical Lab, Mechanical Lab, Electrical Lab, etc.) mapped strictly to matching lab subjects.
  - Guaranteed zero collision: No two faculties or departments can book the same lab or classroom at the same time.
- **Burnout Prevention / Break Guarantees**:
  - Fixed student breaks (Lunch, Recess).
  - Faculty break enforcement (avoids consecutive back-to-back lectures beyond limit).
- **Multi-View Timetable Viewer**:
  - View by Division / Class
  - View by Faculty (personal schedule with breaks)
  - View by Room / Lab (occupancy matrix)
- **Export & Persistence**:
  - Print / PDF export
  - CSV export
  - JSON save & load
  - 1-Click Sample College Pre-loader
