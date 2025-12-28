# Self-Improve Proposal System - Design Doc

**Datum**: 2025-01-21
**Ziel**: `/selfimprove` und `/errorcorrection` sollen Lösungsvorschläge präsentieren, User wählt aus

---

## 🎯 Konzept (wie Claude Code)

### Current Flow (Problem):
```
User: /selfimprove verbessere performance
↓
System: Erstellt Plan
↓
System: "Plan bestätigen?" (Ja/Nein)
↓
System: Führt SOFORT aus (schreibt Code!)
```

**Problem**: Keine Optionen zur Auswahl, nur Ja/Nein!

---

### Desired Flow (Solution):
```
User: /selfimprove verbessere performance
↓
System: Analysiert Code (READ-ONLY!)
↓
System: Präsentiert 3 Optionen:

  📋 VORSCHLAG 1: Caching optimieren
     - Füge LRU-Cache zu häufig genutzten Funktionen hinzu
     - Files: memory_system.py, execution_dispatcher.py
     - Effort: 15 Min
     - Impact: 30% schneller

  📋 VORSCHLAG 2: Parallel Execution
     - Nutze ThreadPoolExecutor für Subtasks
     - Files: execution_dispatcher.py
     - Effort: 30 Min
     - Impact: 50% schneller bei parallelen Tasks

  📋 VORSCHLAG 3: Lazy Loading
     - Lade Agents/Tools nur bei Bedarf
     - Files: agent_manager.py, tool_registry.py
     - Effort: 20 Min
     - Impact: 20% schnellerer Start

  Wähle Option (1/2/3) oder 'alle' oder 'abbrechen':

↓
User: 2
↓
System: Erstellt Plan für Option 2
System: "Plan bestätigen?" (Ja/Nein)
↓
User: Ja
↓
System: Führt aus (schreibt Code!)
```

---

## 🏗️ Implementation Design

### Phase 1: Analysis Phase (READ-ONLY)

**Ziel**: Code analysieren, Verbesserungen identifizieren, NICHTS schreiben!

```python
def _analyze_improvement_opportunities(goal, code_analysis, llm_interface, ui):
    """
    Analysiert Code und generiert Verbesserungsvorschläge.

    Returns:
        List[ImprovementProposal]: 3 konkrete Vorschläge
    """

    analysis_prompt = f"""
    Analysiere den SelfAI Code für: {goal}

    Code-Struktur:
    - {code_analysis['total_files']} Dateien
    - {code_analysis['total_lines']} Zeilen
    - Module: {code_analysis['modules']}

    Identifiziere 3 konkrete Verbesserungen:

    Für jede Verbesserung gib an:
    1. Title: Kurzer Titel (z.B. "Caching optimieren")
    2. Description: Was wird gemacht (2-3 Sätze)
    3. Files: Welche Dateien betroffen (Liste)
    4. Effort: Geschätzte Zeit (in Minuten)
    5. Impact: Erwarteter Nutzen (%)
    6. Implementation: Konkrete Schritte (Stichpunkte)

    WICHTIG:
    - NUR lesende Analyse, KEINE Code-Änderungen jetzt!
    - Konkrete, umsetzbare Vorschläge
    - Realistische Effort-Schätzungen

    Antwort als JSON:
    {
      "proposals": [
        {
          "id": 1,
          "title": "...",
          "description": "...",
          "files": ["file1.py", "file2.py"],
          "effort_minutes": 30,
          "impact_percent": 50,
          "implementation_steps": [...]
        }
      ]
    }
    """

    # Call LLM (READ-ONLY, no tools!)
    response = llm_interface.generate_response(
        system_prompt="Du bist ein Code-Analyst für SelfAI.",
        user_prompt=analysis_prompt,
        max_output_tokens=2048
    )

    # Parse proposals
    proposals = json.loads(response)["proposals"]

    return [ImprovementProposal(**p) for p in proposals]
```

---

### Phase 2: Proposal Presentation

```python
def _present_proposals(proposals, ui):
    """
    Zeigt Vorschläge dem User, lässt wählen.

    Returns:
        ImprovementProposal or List[ImprovementProposal] or None
    """

    ui.status("\n📋 VERBESSERUNGSVORSCHLÄGE:\n", "info")

    for i, proposal in enumerate(proposals, 1):
        print(f"\n  {ui.colorize(f'VORSCHLAG {i}', 'cyan')}: {proposal.title}")
        print(f"  {ui.colorize('Beschreibung:', 'yellow')} {proposal.description}")
        print(f"  {ui.colorize('Dateien:', 'yellow')} {', '.join(proposal.files)}")
        print(f"  {ui.colorize('Aufwand:', 'yellow')} {proposal.effort_minutes} Minuten")
        print(f"  {ui.colorize('Impact:', 'green')} +{proposal.impact_percent}% Verbesserung")

        if proposal.implementation_steps:
            print(f"  {ui.colorize('Schritte:', 'yellow')}")
            for step in proposal.implementation_steps:
                print(f"    - {step}")

    print("\n")

    # User wählt
    choice = input(ui.colorize("Wähle Option (1/2/3) oder 'alle' oder 'abbrechen': ", "cyan")).strip().lower()

    if choice == "abbrechen":
        return None
    elif choice == "alle":
        return proposals
    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(proposals):
            return proposals[idx]
        else:
            ui.status("Ungültige Auswahl!", "error")
            return None
    else:
        ui.status("Ungültige Eingabe!", "error")
        return None
```

---

### Phase 3: Plan Creation (for selected proposal)

```python
def _create_implementation_plan(proposal, agent_manager, planner_interface):
    """
    Erstellt DPPM-Plan für gewählten Vorschlag.

    Args:
        proposal: ImprovementProposal object

    Returns:
        dict: DPPM plan
    """

    goal = f"Implementiere: {proposal.title}\n\n{proposal.description}"

    # Create plan with planner
    plan = planner_interface.plan(
        goal=goal,
        context=PlannerContext(
            agents=agent_manager.list_agents(),
            memory_summary=f"Implementierung von: {proposal.title}"
        )
    )

    # Add metadata
    plan["metadata"]["proposal"] = {
        "id": proposal.id,
        "title": proposal.title,
        "effort_minutes": proposal.effort_minutes,
        "impact_percent": proposal.impact_percent,
        "files": proposal.files
    }

    return plan
```

---

### Phase 4: Execution (with confirmation)

```python
def _execute_improvement(plan, ui, ...):
    """Führt Plan aus nach finaler Bestätigung."""

    # Show plan
    ui.show_plan(plan)

    # Final confirmation
    if not ui.confirm_plan():
        ui.status("Plan verworfen.", "warning")
        return False

    # Execute
    ui.status("Starte Implementierung...", "info")

    dispatcher = ExecutionDispatcher(
        plan_path=plan_path,
        agent_manager=agent_manager,
        memory_system=memory_system,
        llm_backends=execution_backends,
        ui=ui,
        ...
    )

    dispatcher.run()

    return True
```

---

## 🔄 Complete Flow

```python
def _handle_selfimprove_v2(goal, agent_manager, memory_system, ui, llm_interface, planner_interface, execution_backends):
    """
    Neue Self-Improve Implementation mit Proposal-System.
    """

    # 1. Analyze (READ-ONLY!)
    ui.status("Analysiere Code für Verbesserungen...", "info")

    code_analysis = _analyze_selfai_code(ui)

    proposals = _analyze_improvement_opportunities(
        goal=goal,
        code_analysis=code_analysis,
        llm_interface=llm_interface,
        ui=ui
    )

    if not proposals:
        ui.status("Keine Verbesserungsvorschläge gefunden.", "warning")
        return

    # 2. Present & Select
    selected = _present_proposals(proposals, ui)

    if selected is None:
        ui.status("Abgebrochen.", "info")
        return

    # 3. Create Plan(s)
    if isinstance(selected, list):
        # Multiple proposals
        plans = []
        for proposal in selected:
            plan = _create_implementation_plan(proposal, agent_manager, planner_interface)
            plans.append((proposal, plan))
    else:
        # Single proposal
        plan = _create_implementation_plan(selected, agent_manager, planner_interface)
        plans = [(selected, plan)]

    # 4. Execute each plan
    for proposal, plan in plans:
        ui.status(f"\n🚀 Implementiere: {proposal.title}", "info")

        # Save plan
        plan_path = memory_system.save_plan(f"SelfImprove: {proposal.title}", plan)

        # Execute with confirmation
        success = _execute_improvement(
            plan=plan,
            plan_path=plan_path,
            ui=ui,
            agent_manager=agent_manager,
            memory_system=memory_system,
            execution_backends=execution_backends,
            ...
        )

        if success:
            ui.status(f"✅ {proposal.title} erfolgreich implementiert!", "success")
        else:
            ui.status(f"⚠️ {proposal.title} übersprungen.", "warning")
```

---

## 📊 Beispiel-Output

```
Du: /selfimprove verbessere performance

ℹ️ Analysiere Code für Verbesserungen...

📋 VERBESSERUNGSVORSCHLÄGE:

  VORSCHLAG 1: LRU-Cache für Memory-System
  Beschreibung: Füge @lru_cache zu häufig aufgerufenen load_relevant_context()
                hinzu. Reduziert redundante Datei-Zugriffe.
  Dateien: selfai/core/memory_system.py
  Aufwand: 10 Minuten
  Impact: +25% schneller bei wiederholten Queries
  Schritte:
    - Import functools.lru_cache
    - Dekoriere load_relevant_context mit @lru_cache(maxsize=128)
    - Teste mit wiederholten Memory-Loads

  VORSCHLAG 2: Parallel Subtask Execution
  Beschreibung: Nutze ThreadPoolExecutor in execution_dispatcher.py um Subtasks
                mit gleicher parallel_group wirklich parallel auszuführen.
  Dateien: selfai/core/execution_dispatcher.py
  Aufwand: 30 Minuten
  Impact: +50% schneller bei parallelen Tasks
  Schritte:
    - Import concurrent.futures.ThreadPoolExecutor
    - Refactor run() method für Thread-Pool
    - Gruppiere Tasks nach parallel_group
    - Führe jede Gruppe parallel aus

  VORSCHLAG 3: Tool Registry Lazy Loading
  Beschreibung: Lade Tools erst wenn gebraucht statt alle beim Start zu konvertieren.
                Reduziert Startup-Zeit.
  Dateien: selfai/tools/tool_registry.py
  Aufwand: 15 Minuten
  Impact: +30% schnellerer Start
  Schritte:
    - Lazy-load to_smol_tool() Konvertierung
    - Cache konvertierte Tools
    - Nur konvertieren bei Bedarf

Wähle Option (1/2/3) oder 'alle' oder 'abbrechen': 2

✅ Vorschlag ausgewählt: Parallel Subtask Execution

ℹ️ Erstelle Implementierungsplan...

📝 PLAN:
Subtasks:
  S1: Analysiere execution_dispatcher.py ThreadPool-Integration
  S2: Implementiere ThreadPoolExecutor in run() method
  S3: Teste parallele Execution mit Beispiel-Plan

Plan bestätigen? (y/n): y

🚀 Starte Implementierung...

[Tool-Calls, Code-Änderungen, etc.]

✅ Parallel Subtask Execution erfolgreich implementiert!
```

---

## 🎯 Key Benefits

1. **User Control**: User sieht ALLE Optionen vor Entscheidung
2. **Informed Choice**: Effort, Impact, Files klar kommuniziert
3. **No Surprises**: Keine unerwarteten Code-Änderungen
4. **Claude Code Style**: Vertrautes UX-Pattern
5. **Flexible**: User kann 1, mehrere, oder alle wählen

---

## 📋 Implementation Checklist

- [ ] Create `ImprovementProposal` dataclass
- [ ] Implement `_analyze_improvement_opportunities()`
- [ ] Implement `_present_proposals()` with UI
- [ ] Modify `_handle_selfimprove()` to use new flow
- [ ] Test with `/selfimprove verbessere performance`
- [ ] Same for `/errorcorrection` command

---

## 🚀 Next Steps

**Option A**: Implement full Proposal System (2-3 hours)
- Complete re-design of /selfimprove
- ImprovementProposal class
- Analysis phase
- Selection UI

**Option B**: Quick Enhancement (30 Min)
- Add simple "Wähle Implementierungs-Strategie" prompt
- Present 2-3 options as text
- User types choice
- Create plan based on choice

**Was bevorzugst du?**

---

**Created**: 2025-01-21
**Status**: Design Doc
**Complexity**: Medium (2-3 hours for full system)
**Value**: High (matches Claude Code UX!)
