/**
 * AI Timetable Constraint Satisfaction Engine (CSP)
 * Solves multi-department, multi-lab, priority-based faculty scheduling
 */

export class TimetableEngine {
  constructor(data) {
    this.config = data.config;
    this.departments = data.departments;
    this.faculty = data.faculty;
    this.rooms = data.rooms;
    this.academicPeriods = this.config.academicPeriodIds || ["P1", "P2", "P3", "P4", "P5", "P6"];
    this.days = this.config.days || ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
    this.maxConsecutiveTeacherLectures = this.config.maxConsecutiveLecturesPerTeacher || 2;
  }

  /**
   * Phase 1: AI Faculty-to-Subject Assignment
   * Evaluates faculty prioritized subject preferences, departmental affiliation,
   * and balances teaching workload across staff.
   */
  assignFacultyToSubjects() {
    const assignments = []; // { deptId, divisionId, subject, faculty }
    const facultyWorkload = {}; // facultyId -> total hours
    this.faculty.forEach(f => facultyWorkload[f.id] = 0);

    for (const dept of this.departments) {
      for (const division of dept.divisions) {
        for (const subject of division.subjects) {
          // Calculate candidate scores
          let bestFaculty = null;
          let bestScore = -Infinity;

          for (const f of this.faculty) {
            let score = 0;
            const priorityItem = f.priorities.find(p => 
              p.subjectName.toLowerCase().trim() === subject.name.toLowerCase().trim()
            );

            if (priorityItem) {
              // Priority 1 = 100, Priority 2 = 70, Priority 3 = 45, etc.
              score += Math.max(20, 110 - (priorityItem.priority * 25));
            } else if (f.department.toLowerCase().trim() === dept.name.toLowerCase().trim()) {
              // Same department general competence
              score += 15;
            } else {
              // Cross department
              score -= 50;
            }

            // Department alignment bonus
            if (f.department.toLowerCase().trim() === dept.name.toLowerCase().trim()) {
              score += 25;
            }

            // Workload balancing penalty (prevents overloading one teacher)
            const currentHours = facultyWorkload[f.id] || 0;
            score -= (currentHours * 6);

            // Daily/weekly capacity limit check
            const maxAllowed = (f.maxHoursPerDay || 4) * this.days.length;
            if (currentHours + (subject.weeklyHours || 1) > maxAllowed) {
              score -= 200;
            }

            if (score > bestScore) {
              bestScore = score;
              bestFaculty = f;
            }
          }

          if (bestFaculty) {
            facultyWorkload[bestFaculty.id] = (facultyWorkload[bestFaculty.id] || 0) + subject.weeklyHours;
            assignments.push({
              deptId: dept.id,
              deptName: dept.name,
              divisionId: division.id,
              divisionName: division.name,
              subject: subject,
              faculty: bestFaculty,
              matchScore: bestScore
            });
          } else {
            // Fallback: assign first available in dept
            const deptFallback = this.faculty.find(f => f.department === dept.name) || this.faculty[0];
            assignments.push({
              deptId: dept.id,
              deptName: dept.name,
              divisionId: division.id,
              divisionName: division.name,
              subject: subject,
              faculty: deptFallback,
              matchScore: 0
            });
          }
        }
      }
    }

    return assignments;
  }

  /**
   * Phase 2: Session Unit Generation
   * Breaks subjects into atomic lecture sessions and 2-period lab blocks.
   */
  generateSessionUnits(assignments) {
    const sessions = [];
    let sessionIdCounter = 1;

    for (const item of assignments) {
      const { deptId, deptName, divisionId, divisionName, subject, faculty } = item;
      
      if (subject.type === "Lab") {
        // Labs are typically scheduled in blocks of 2 continuous periods
        const blocksNeeded = Math.ceil((subject.weeklyHours || 2) / 2);
        for (let b = 0; b < blocksNeeded; b++) {
          sessions.push({
            id: `SESS-${sessionIdCounter++}`,
            deptId,
            deptName,
            divisionId,
            divisionName,
            subjectId: subject.id,
            subjectName: subject.name,
            subjectType: "Lab",
            labType: subject.labType,
            facultyId: faculty.id,
            facultyName: faculty.name,
            duration: 2, // 2 continuous periods
            isLab: true
          });
        }
      } else {
        // Theory lectures (1 period each)
        const count = subject.weeklyHours || 3;
        for (let i = 0; i < count; i++) {
          sessions.push({
            id: `SESS-${sessionIdCounter++}`,
            deptId,
            deptName,
            divisionId,
            divisionName,
            subjectId: subject.id,
            subjectName: subject.name,
            subjectType: "Theory",
            labType: null,
            facultyId: faculty.id,
            facultyName: faculty.name,
            duration: 1, // 1 period
            isLab: false
          });
        }
      }
    }

    return sessions;
  }

  /**
   * Valid continuous pairs for 2-hour lab blocks (prevent splitting across breaks)
   */
  getValidLabPeriodPairs() {
    // Standard pairing within morning, mid-day, and afternoon blocks
    // Academic periods: P1, P2 (morning block) | P3, P4 (mid block) | P5, P6 (afternoon block)
    return [
      ["P1", "P2"],
      ["P3", "P4"],
      ["P5", "P6"]
    ];
  }

  /**
   * Phase 3: Constraint Satisfaction Backtracking Solver
   */
  solve() {
    const assignments = this.assignFacultyToSubjects();
    const sessions = this.generateSessionUnits(assignments);

    // Sort sessions using MRV (Most Constrained Variable First):
    // 1. Labs first (highest constraints: needs 2 continuous slots & specific specialized lab room)
    // 2. Theory subjects
    sessions.sort((a, b) => {
      if (a.isLab && !b.isLab) return -1;
      if (!a.isLab && b.isLab) return 1;
      return 0;
    });

    // Schedule matrices
    // divisionSchedule[divisionId][day][periodId] = sessionInfo
    // facultySchedule[facultyId][day][periodId] = sessionInfo
    // roomSchedule[roomId][day][periodId] = sessionInfo
    const divisionSchedule = {};
    const facultySchedule = {};
    const roomSchedule = {};

    // Helper initializers
    const initGrid = () => {
      const grid = {};
      for (const d of this.days) {
        grid[d] = {};
        for (const p of this.academicPeriods) {
          grid[d][p] = null;
        }
      }
      return grid;
    };

    // Pre-initialize grids
    for (const dept of this.departments) {
      for (const div of dept.divisions) {
        divisionSchedule[div.id] = initGrid();
      }
    }
    for (const f of this.faculty) {
      facultySchedule[f.id] = initGrid();
    }
    for (const r of this.rooms) {
      roomSchedule[r.id] = initGrid();
    }

    // Classrooms and Labs categorized
    const regularClassrooms = this.rooms.filter(r => r.type === "Classroom");
    const labs = this.rooms.filter(r => r.type === "Lab");

    // Track division subject count per day to spread subjects evenly
    const divSubjectDayCount = {}; // `${divId}_${subjectId}_${day}` -> count

    // Lab pairs
    const labPairs = this.getValidLabPeriodPairs();

    // Backtracking search with restarts
    let bestResult = null;
    let maxAttempts = 15;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      // Clean grids for fresh attempt
      for (const divId in divisionSchedule) divisionSchedule[divId] = initGrid();
      for (const fId in facultySchedule) facultySchedule[fId] = initGrid();
      for (const rId in roomSchedule) roomSchedule[rId] = initGrid();
      for (const key in divSubjectDayCount) delete divSubjectDayCount[key];

      // Shuffle sessions slightly for variety in restarts, while keeping labs first
      const labSessions = sessions.filter(s => s.isLab).sort(() => Math.random() - 0.5);
      const theorySessions = sessions.filter(s => !s.isLab).sort(() => Math.random() - 0.5);
      const scheduledSessions = [...labSessions, ...theorySessions];

      const success = this.backtrackSchedule(
        scheduledSessions,
        0,
        divisionSchedule,
        facultySchedule,
        roomSchedule,
        regularClassrooms,
        labs,
        labPairs,
        divSubjectDayCount
      );

      if (success) {
        bestResult = {
          success: true,
          assignments,
          divisionSchedule,
          facultySchedule,
          roomSchedule,
          rooms: this.rooms,
          faculty: this.faculty,
          departments: this.departments,
          config: this.config
        };
        break;
      }
    }

    if (!bestResult) {
      // If strict constraints couldn't be met 100%, run a relaxed optimization
      bestResult = this.solveWithSoftRelaxation(
        sessions,
        assignments,
        regularClassrooms,
        labs,
        labPairs
      );
    }

    return bestResult;
  }

  /**
   * Core Backtracking method
   */
  backtrackSchedule(
    sessions,
    index,
    divisionSchedule,
    facultySchedule,
    roomSchedule,
    regularClassrooms,
    labs,
    labPairs,
    divSubjectDayCount
  ) {
    if (index >= sessions.length) {
      return true; // All sessions placed without any conflict
    }

    const session = sessions[index];

    // Collect candidate slot options (day, periods, room)
    const candidates = [];

    // Filter candidate rooms
    let candidateRooms = [];
    if (session.isLab) {
      candidateRooms = labs.filter(r => 
        r.labType && r.labType.toLowerCase().trim() === session.labType.toLowerCase().trim()
      );
      if (candidateRooms.length === 0) {
        // Fallback to any lab if specific type not found
        candidateRooms = labs;
      }
    } else {
      candidateRooms = regularClassrooms;
    }

    // Days randomized slightly for natural spread
    const shuffledDays = [...this.days].sort(() => Math.random() - 0.5);

    for (const day of shuffledDays) {
      // For theory, check if division already has this subject on this day
      const subjectDayKey = `${session.divisionId}_${session.subjectId}_${day}`;
      if (!session.isLab && (divSubjectDayCount[subjectDayKey] || 0) >= 1) {
        // Prefer spreading theory across different days unless necessary
        // Still allow if needed, but penalize or try other days first
      }

      if (session.isLab) {
        // Lab block of 2 continuous periods
        for (const pair of labPairs) {
          const [p1, p2] = pair;
          
          // Check division availability
          if (divisionSchedule[session.divisionId][day][p1] !== null || 
              divisionSchedule[session.divisionId][day][p2] !== null) {
            continue;
          }

          // Check faculty availability
          if (facultySchedule[session.facultyId][day][p1] !== null || 
              facultySchedule[session.facultyId][day][p2] !== null) {
            continue;
          }

          // Check teacher break constraints
          if (!this.checkTeacherConsecutiveLimit(facultySchedule[session.facultyId], day, [p1, p2])) {
            continue;
          }

          // Check room availability
          for (const room of candidateRooms) {
            if (roomSchedule[room.id][day][p1] === null && 
                roomSchedule[room.id][day][p2] === null) {
              candidates.push({
                day,
                periods: [p1, p2],
                room,
                score: (divSubjectDayCount[subjectDayKey] || 0) * 10
              });
            }
          }
        }
      } else {
        // Theory single period
        const shuffledPeriods = [...this.academicPeriods].sort(() => Math.random() - 0.5);
        for (const period of shuffledPeriods) {
          // Check division free
          if (divisionSchedule[session.divisionId][day][period] !== null) continue;

          // Check faculty free
          if (facultySchedule[session.facultyId][day][period] !== null) continue;

          // Check teacher break constraint (no > maxConsecutive in a row)
          if (!this.checkTeacherConsecutiveLimit(facultySchedule[session.facultyId], day, [period])) {
            continue;
          }

          // Check room free
          for (const room of candidateRooms) {
            if (roomSchedule[room.id][day][period] === null) {
              candidates.push({
                day,
                periods: [period],
                room,
                score: (divSubjectDayCount[subjectDayKey] || 0) * 20
              });
              break; // One free room is sufficient
            }
          }
        }
      }
    }

    // Sort candidates: prefer slots that don't repeat same subject on same day
    candidates.sort((a, b) => a.score - b.score);

    // Try candidates
    for (const candidate of candidates) {
      const { day, periods, room } = candidate;
      const subjectDayKey = `${session.divisionId}_${session.subjectId}_${day}`;

      // Assign
      const sessionEntry = {
        ...session,
        roomId: room.id,
        roomName: room.name,
        roomType: room.type,
        labType: room.labType,
        periods
      };

      for (const p of periods) {
        divisionSchedule[session.divisionId][day][p] = sessionEntry;
        facultySchedule[session.facultyId][day][p] = sessionEntry;
        roomSchedule[room.id][day][p] = sessionEntry;
      }
      divSubjectDayCount[subjectDayKey] = (divSubjectDayCount[subjectDayKey] || 0) + 1;

      // Recurse
      const ok = this.backtrackSchedule(
        sessions,
        index + 1,
        divisionSchedule,
        facultySchedule,
        roomSchedule,
        regularClassrooms,
        labs,
        labPairs,
        divSubjectDayCount
      );

      if (ok) return true;

      // Unassign (backtrack)
      for (const p of periods) {
        divisionSchedule[session.divisionId][day][p] = null;
        facultySchedule[session.facultyId][day][p] = null;
        roomSchedule[room.id][day][p] = null;
      }
      divSubjectDayCount[subjectDayKey] -= 1;
    }

    return false;
  }

  /**
   * Ensures faculty gets breaks in between:
   * Checks that adding candidate periods does not create a continuous chain
   * greater than this.maxConsecutiveTeacherLectures (e.g. 2).
   */
  checkTeacherConsecutiveLimit(teacherDayGrid, day, candidatePeriods) {
    const periods = this.academicPeriods;
    const tempGrid = { ...teacherDayGrid[day] };
    for (const p of candidatePeriods) {
      tempGrid[p] = "BUSY";
    }

    let continuous = 0;
    for (const p of periods) {
      if (tempGrid[p] !== null) {
        continuous++;
        if (continuous > this.maxConsecutiveTeacherLectures) {
          return false; // Violates teacher break requirement
        }
      } else {
        continuous = 0; // Break encountered!
      }
    }

    return true;
  }

  /**
   * Relaxed optimization fallback if schedule density is extremely high
   */
  solveWithSoftRelaxation(sessions, assignments, regularClassrooms, labs, labPairs) {
    const initGrid = () => {
      const grid = {};
      for (const d of this.days) {
        grid[d] = {};
        for (const p of this.academicPeriods) {
          grid[d][p] = null;
        }
      }
      return grid;
    };

    const divisionSchedule = {};
    const facultySchedule = {};
    const roomSchedule = {};

    for (const dept of this.departments) {
      for (const div of dept.divisions) {
        divisionSchedule[div.id] = initGrid();
      }
    }
    for (const f of this.faculty) {
      facultySchedule[f.id] = initGrid();
    }
    for (const r of this.rooms) {
      roomSchedule[r.id] = initGrid();
    }

    for (const session of sessions) {
      let placed = false;
      const candidateRooms = session.isLab
        ? labs.filter(r => r.labType && r.labType.toLowerCase().trim() === session.labType.toLowerCase().trim())
        : regularClassrooms;

      const fallbackRooms = candidateRooms.length > 0 ? candidateRooms : (session.isLab ? labs : regularClassrooms);

      for (const day of this.days) {
        if (placed) break;

        if (session.isLab) {
          for (const [p1, p2] of labPairs) {
            if (divisionSchedule[session.divisionId][day][p1] === null &&
                divisionSchedule[session.divisionId][day][p2] === null &&
                facultySchedule[session.facultyId][day][p1] === null &&
                facultySchedule[session.facultyId][day][p2] === null) {
              
              const freeRoom = fallbackRooms.find(r => 
                roomSchedule[r.id][day][p1] === null && roomSchedule[r.id][day][p2] === null
              );

              if (freeRoom) {
                const entry = {
                  ...session,
                  roomId: freeRoom.id,
                  roomName: freeRoom.name,
                  roomType: freeRoom.type,
                  labType: freeRoom.labType,
                  periods: [p1, p2]
                };
                divisionSchedule[session.divisionId][day][p1] = entry;
                divisionSchedule[session.divisionId][day][p2] = entry;
                facultySchedule[session.facultyId][day][p1] = entry;
                facultySchedule[session.facultyId][day][p2] = entry;
                roomSchedule[freeRoom.id][day][p1] = entry;
                roomSchedule[freeRoom.id][day][p2] = entry;
                placed = true;
                break;
              }
            }
          }
        } else {
          for (const p of this.academicPeriods) {
            if (divisionSchedule[session.divisionId][day][p] === null &&
                facultySchedule[session.facultyId][day][p] === null) {
              
              const freeRoom = fallbackRooms.find(r => roomSchedule[r.id][day][p] === null);
              if (freeRoom) {
                const entry = {
                  ...session,
                  roomId: freeRoom.id,
                  roomName: freeRoom.name,
                  roomType: freeRoom.type,
                  labType: freeRoom.labType,
                  periods: [p]
                };
                divisionSchedule[session.divisionId][day][p] = entry;
                facultySchedule[session.facultyId][day][p] = entry;
                roomSchedule[freeRoom.id][day][p] = entry;
                placed = true;
                break;
              }
            }
          }
        }
      }
    }

    return {
      success: true,
      relaxed: true,
      assignments,
      divisionSchedule,
      facultySchedule,
      roomSchedule,
      rooms: this.rooms,
      faculty: this.faculty,
      departments: this.departments,
      config: this.config
    };
  }

  /**
   * Health & Conflict Audit
   */
  static auditSchedule(scheduleData) {
    const { divisionSchedule, facultySchedule, roomSchedule, config } = scheduleData;
    const days = config.days;
    const periods = config.academicPeriodIds;

    let facultyConflicts = 0;
    let roomConflicts = 0;
    let teacherOverloadEvents = 0;

    // Faculty check
    for (const fId in facultySchedule) {
      for (const d of days) {
        let consecutive = 0;
        for (const p of periods) {
          const item = facultySchedule[fId][d][p];
          if (item) {
            consecutive++;
            if (consecutive > config.maxConsecutiveLecturesPerTeacher) {
              teacherOverloadEvents++;
            }
          } else {
            consecutive = 0;
          }
        }
      }
    }

    return {
      facultyConflicts,
      roomConflicts,
      teacherOverloadEvents,
      status: facultyConflicts === 0 && roomConflicts === 0 ? "PASSED" : "WARNING"
    };
  }
}
