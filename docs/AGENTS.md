# Agenten-Handbuch

Dieses Projekt verwaltet SelfAI-Personas in separaten Ordnern unter `selfai/agents/`.
Jede Persona besteht aus:

- `config.yaml` – Metadaten (Name, Workspace, Farben, Memory-Kategorien, Prompt-Datei)
- `system_prompt.md` – Ausformulierter System-Prompt in Markdown
- (optional) weitere Dateien z. B. `memory_policies.md`, Tests oder Beispiele

## Strukturbeispiel

```
selfai/agents/
  code_helfer/
    config.yaml
    system_prompt.md
  verhandlungspartner/
    config.yaml
    system_prompt.md
  projektmanager/
    config.yaml
    system_prompt.md
```

### config.yaml

```yaml
agent:
  name: "code_helfer"                # interner Schlüssel, klein & ohne Leerzeichen
  display_name: "Code-Helfer"        # wird im UI angezeigt
  workspace_slug: "coding"           # AnythingLLM Workspace
  color: "green"                     # Terminal-Farbe (ANSI Name)
  memory_categories: ["projekt1"]    # Ordner im SelfAI-Speicher
  system_prompt_file: "system_prompt.md"
  description: "Kurzbeschreibung für die Agentenliste."
  tags: ["code", "review"]           # optional
```

### system_prompt.md

Markdown-Datei für Persona, Stil und Arbeitsauftrag:

```markdown
## Rolle
…

## Auftrag
- …
- …

## Stil
- …
```

## Workflow für neue Agenten

1. **Need klären** – Warum wird die Rolle gebraucht? Welche Aufgaben übernimmt sie?
2. **Ordner kopieren** – `selfai/agents/_template/` (falls vorhanden) oder bestehenden Agenten duplizieren.
3. **Prompt ausarbeiten** – Klar definierte Aufgaben, Stil, Grenzen; Beispiele ergänzen.
4. **config.yaml** anpassen – neue `name`, `display_name`, `workspace_slug`, Farben usw.
5. **Dokumentieren** – Kurzbeschreibung hier ergänzen, ggf. Test-Prompts unter `tests/agents/<name>/`.
6. **Review** – Änderungen via PR überprüfen lassen, damit Prompts konsistent bleiben.

## Aktive Personas (Stand jetzt)

| Schlüssel            | Anzeige                | Zweck                                    |
|---------------------|------------------------|------------------------------------------|
| `code_helfer`       | Code-Helfer            | Code-Analyse, Architektur, Best Practices|
| `verhandlungspartner` | Verhandlungsexperte  | Strategische Gesprächsführung & Mediation|
| `projektmanager`    | Projektmanager         | Roadmaps, Risiken, Aufgabenplanung       |
| `reiseplaner`       | Reise- und Verkehrsplaner | Bahnverbindungen, Pendel- und Ausflugsplanung mit Tool-Unterstützung |

> Tipp: Im SelfAI-Terminal kannst du mit `/switch 2` oder `/switch Projektmanager` die Agenten wechseln.

> Tipp: In `config.yaml` (Projektroot) kann mit `agent_config.default_agent` der Standard-Agent gesetzt werden.
