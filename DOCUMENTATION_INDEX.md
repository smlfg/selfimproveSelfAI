# Documentation Index

This directory contains comprehensive documentation for the AI NPU Agent Project. Here's a guide to each document:

## Main Documentation Files

### 1. **CLAUDE.md** (33 KB, 1,020 lines) - COMPREHENSIVE ARCHITECTURE GUIDE
**Read this for:** Complete technical understanding and deep dives
- **What's Inside:**
  - Detailed architecture overview with ASCII diagrams
  - Complete component descriptions
  - Configuration system deep dive
  - All key modules explained
  - Setup instructions with step-by-step guidance
  - Troubleshooting guide
  - Development notes and design patterns
  - Performance considerations
  - Security notes
  - Extension guidelines

- **Best For:** Developers who need full context, architects planning modifications, advanced users

- **Key Sections:**
  - Project Overview
  - Architecture Overview (with diagrams)
  - Directory Structure
  - Configuration System
  - Key Components (8 major components explained)
  - Entry Points & Execution Flow
  - Component Interaction Diagram
  - Dependencies
  - Setup Instructions
  - Workflows
  - Extending the System
  - Troubleshooting

---

### 2. **ARCHITECTURE_SUMMARY.txt** (12 KB, 362 lines) - QUICK REFERENCE
**Read this for:** Quick lookup and system overview without deep dives
- **What's Inside:**
  - Project purpose in 1-2 lines
  - Three-phase pipeline explained simply
  - Backend support overview
  - Key entry points
  - Configuration structure (quick reference)
  - Component structure (file listing with descriptions)
  - Memory and persistence format
  - Agent system overview
  - Dependencies list
  - Common workflows (4 quick examples)
  - Troubleshooting quick reference (table format)
  - Performance tips
  - Security notes
  - Development patterns
  - Key files to know

- **Best For:** Quick reference, team onboarding, remembering key concepts

- **Perfect When You Need:**
  - To remember which backend runs first
  - Quick answer on where config files are
  - List of main entry points
  - Common troubleshooting solutions
  - Component overview

---

### 3. **QUICK_START.md** (3.9 KB, 198 lines) - GET RUNNING IN 5 MINUTES
**Read this for:** Immediate setup and first steps
- **What's Inside:**
  - 5-step setup (venv, install, configure, download, run)
  - First commands to try
  - Core concepts (3 backends, 3 phases, agents)
  - File locations table
  - Key config settings snippet
  - Environment variables template
  - Quick troubleshooting table
  - Quick command reference
  - System requirements

- **Best For:** New users, quick setup, trying the system immediately

- **Perfect When You:**
  - Just cloned the repository
  - Want to run your first test
  - Need a quick reminder of key commands
  - Are setting up for the first time

---

### 4. **README.md** - PROJECT OVERVIEW
**Read this for:** High-level project description and basic usage
- Located in repository root
- User-facing introduction
- Basic setup instructions
- Overview of SelfAI pipeline

---

### 5. **UI_GUIDE.md** - TERMINAL INTERFACE
**Read this for:** Terminal UI features and customization
- Rich terminal features
- Animation configuration
- Color customization
- Different UI modes

---

## Documentation Reading Paths

### Path 1: "Just Get It Running" (15 minutes)
1. QUICK_START.md (5 min)
2. Run `python selfai/selfai.py` (immediate feedback)
3. Try `/plan Create a simple script` command

### Path 2: "I Need to Understand Everything" (2 hours)
1. ARCHITECTURE_SUMMARY.txt (20 min) - get oriented
2. CLAUDE.md sections in order (80 min):
   - Architecture Overview
   - Key Components
   - Configuration System
   - Entry Points
3. Brief code review of selfai/selfai.py (20 min)

### Path 3: "I Need to Modify or Extend" (3 hours)
1. ARCHITECTURE_SUMMARY.txt (20 min) - concepts
2. CLAUDE.md sections (90 min):
   - Architecture Overview
   - Key Components
   - Component Interaction
   - How to Extend
3. Code review of relevant modules (70 min)
4. Try modification or extension

### Path 4: "Quick Reference During Development" (ongoing)
1. Keep ARCHITECTURE_SUMMARY.txt handy
2. Reference specific CLAUDE.md sections as needed
3. Check QUICK_START.md for commands

---

## Quick Navigation by Topic

### Understanding the System
- **Overall architecture:** CLAUDE.md > Architecture Overview
- **Three-phase pipeline:** ARCHITECTURE_SUMMARY.txt > THREE-PHASE PIPELINE
- **Component overview:** ARCHITECTURE_SUMMARY.txt > COMPONENT STRUCTURE
- **Deep dives:** CLAUDE.md > Key Components section

### Setup & Configuration
- **Quick setup:** QUICK_START.md > 5-Minute Setup
- **Detailed setup:** CLAUDE.md > Setup Instructions
- **Configuration details:** CLAUDE.md > Configuration System
- **Config options:** config.yaml.template (with inline comments)

### Running the System
- **First commands:** QUICK_START.md > First Commands to Try
- **Entry points:** ARCHITECTURE_SUMMARY.txt > KEY ENTRY POINTS
- **Common workflows:** ARCHITECTURE_SUMMARY.txt > COMMON WORKFLOWS

### Troubleshooting
- **Quick solutions:** QUICK_START.md > Troubleshooting table
- **Detailed troubleshooting:** CLAUDE.md > Troubleshooting section
- **Quick reference:** ARCHITECTURE_SUMMARY.txt > TROUBLESHOOTING QUICK REFERENCE

### Extending the System
- **Adding agents:** CLAUDE.md > How to Extend > Adding a New Agent
- **Adding tools:** CLAUDE.md > How to Extend > Adding a New Tool
- **Adding backends:** CLAUDE.md > How to Extend > Adding New LLM Backend

### Performance & Optimization
- **Performance tips:** ARCHITECTURE_SUMMARY.txt > PERFORMANCE TIPS
- **Performance considerations:** CLAUDE.md > Performance Considerations section
- **Token limits:** ARCHITECTURE_SUMMARY.txt > PERFORMANCE TIPS

### Security
- **Security basics:** QUICK_START.md > Environment Variables section
- **Security details:** CLAUDE.md > Security Considerations

---

## File Organization Legend

### Documentation Files (Read These)
- `CLAUDE.md` - Comprehensive architecture (main reference)
- `ARCHITECTURE_SUMMARY.txt` - Quick reference guide
- `QUICK_START.md` - Setup and first steps
- `README.md` - Project overview
- `UI_GUIDE.md` - Terminal interface features
- `DOCUMENTATION_INDEX.md` - This file

### Configuration Files (Edit These)
- `config.yaml.template` - Configuration template
- `.env.example` - Environment variables template

### Source Code (Study These)
- `selfai/selfai.py` - Main pipeline (1,400+ lines)
- `config_loader.py` - Configuration loading
- `selfai/core/*.py` - Core modules
- `selfai/tools/*.py` - Tool implementations
- `selfai/ui/terminal_ui.py` - User interface

### Data Directories (Will Be Created)
- `models/` - GGUF model files
- `memory/` - Conversation and plan storage
- `agents/` - Agent configurations

---

## Key Concepts Reference

### Architecture Layers
```
User Input
    ↓
[Configuration System] ← config.yaml, .env
    ↓
[Agent Manager] ← agents/
    ↓
[Three-Phase Pipeline]
  1. Planning (Ollama)
  2. Execution (LLM backends)
  3. Merge (Ollama or fallback)
    ↓
[Backend Selection] → AnythingLLM → QNN → CPU
    ↓
[Memory System] → memory/
    ↓
[Terminal UI] → User display
```

### Backend Priority
1. **AnythingLLM** (Primary) - HTTP API, NPU acceleration
2. **QNN** (Secondary) - Direct model, NPU acceleration
3. **CPU** (Fallback) - GGUF model, pure CPU

### File Locations
| What | Where |
|------|-------|
| Main script | `selfai/selfai.py` |
| Config | `config.yaml` |
| Models | `models/` |
| Memory | `memory/` |
| Agents | `agents/` |

---

## Recommendations by Role

### As a **User** (just running it)
1. Start with: QUICK_START.md
2. Reference: ARCHITECTURE_SUMMARY.txt for quick lookups
3. Advanced use: CLAUDE.md > Workflows section

### As a **Developer** (modifying code)
1. Start with: ARCHITECTURE_SUMMARY.txt
2. Deep dive: CLAUDE.md > Key Components section
3. Extend: CLAUDE.md > How to Extend section
4. Reference source code as needed

### As a **DevOps/Architect** (deploying/scaling)
1. Start with: ARCHITECTURE_SUMMARY.txt
2. Study: CLAUDE.md > Configuration System
3. Plan: CLAUDE.md > Performance Considerations
4. Secure: CLAUDE.md > Security Considerations

### As a **Newcomer** (first time)
1. 5-min overview: QUICK_START.md
2. Run system: `python selfai/selfai.py`
3. Try commands from QUICK_START.md
4. Read ARCHITECTURE_SUMMARY.txt for understanding
5. Deep dive into CLAUDE.md as questions arise

---

## Document Statistics

| Document | Size | Lines | Purpose |
|----------|------|-------|---------|
| CLAUDE.md | 33 KB | 1,020 | Comprehensive reference |
| ARCHITECTURE_SUMMARY.txt | 12 KB | 362 | Quick lookup |
| QUICK_START.md | 3.9 KB | 198 | Get running |
| README.md | 2.5 KB | 76 | Project intro |
| UI_GUIDE.md | ~8 KB | 144 | UI features |

**Total Documentation: ~60 KB covering all aspects**

---

## Checklist for Reading

### Essential (Required)
- [ ] QUICK_START.md (first 10 minutes)
- [ ] Run system successfully
- [ ] Try /plan command

### Recommended (30 minutes)
- [ ] ARCHITECTURE_SUMMARY.txt (quick overview)
- [ ] Understand three backends
- [ ] Understand three phases

### Comprehensive (2+ hours)
- [ ] Read CLAUDE.md sections of interest
- [ ] Review source code structure
- [ ] Plan any modifications

---

## Getting Help

1. **Quick question?** → Check ARCHITECTURE_SUMMARY.txt
2. **How do I...?** → Check QUICK_START.md > Quick Command Reference
3. **Something broken?** → Check troubleshooting in ARCHITECTURE_SUMMARY.txt or CLAUDE.md
4. **Understand everything?** → Start with CLAUDE.md > Architecture Overview
5. **Want to modify?** → CLAUDE.md > How to Extend section

---

**Last Updated:** January 2025
**Coverage:** 100% of system architecture and features
**Audience:** Users, developers, architects
