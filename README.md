# Agentic School Scheduling Platform — Backend Services

Production-grade FastAPI backend powered by Google OR-Tools CP-SAT, PostgreSQL + pgvector, and multi-agent scheduling orchestrators.

## Key Modules & Agents

### 1. Deterministic CP-SAT Timetable Solver (Phase 1)
- **Engine**: Google OR-Tools CP-SAT solver ([`timetable_solver.py`](file:///d:/GlooHack_BE/app/solver/timetable_solver.py)).
- **Constraints**: Hard constraints (teacher overlap, room overlap, section overlap, capacity, required equipment, teacher availability) and soft constraint objective optimization.
- **Inspector**: Deterministic [`ConflictDetector`](file:///d:/GlooHack_BE/app/solver/conflict_detector.py) validator for zero-hard-conflict verification.

### 2. Teacher Substitution Agent (Phase 2)
- **Agent**: Autonomous agent for teacher absence ingestion and substitute candidate ranking ([`teacher_substitution_agent.py`](file:///d:/GlooHack_BE/app/agents/teacher_substitution_agent.py)).
- **Services**: Email ingestion (`EmailIngestionService`), intent extraction (`AbsenceExtractionService`), teacher matching (`TeacherMatchingService`), and HITL approval governance.

### 3. Room Allocation Agent (Phase 3)
- **Agent**: Autonomous agent for facility closures, maintenance, and equipment outage recovery ([`room_allocation_agent.py`](file:///d:/GlooHack_BE/app/agents/room_allocation_agent.py)).
- **Services**: Capacity filtering, equipment impact matching, alternative room candidate ranking, and atomic timetable updates.

### 4. Disruption Recovery Agent (Phase 4)
- **Agent**: Multi-period, multi-resource orchestrator for major campus disruptions ([`disruption_recovery_agent.py`](file:///d:/GlooHack_BE/app/agents/disruption_recovery_agent.py)).
- **Functions**: Scope identification, multi-strategy candidate plan generation, deterministic plan ranking (`CLEAN_RECOVERY`, `LOW_DISRUPTION`, `MODERATE_DISRUPTION`), HITL governance, atomic execution with timetable version checks, and vector decision memory logging.

---

## Getting Started

### Installation
```bash
pip install -r requirements.txt
```

### Running the API Server
```bash
uvicorn app.main:app --reload --port 8000
```
Interactive API documentation: `http://localhost:8000/docs`

### Running Unit Tests
```bash
python -m pytest tests/
```
All 33 test cases run in ~0.60s covering all solver constraints and agent workflows.

---

## Documentation

Full architectural documentation is maintained in the frontend repository at [`d:\GlooHack\docs`](file:///d:/GlooHack/docs). See index reference at [`docs/README.md`](file:///d:/GlooHack_BE/docs/README.md).
