# Die Komplette Geschichte von SelfAI: Eine technische Chronik

Dieses Dokument zeichnet die technische Evolution des SelfAI-Projekts nach. Es ist eine Chronik von ambitionierten Zielen, technischen Hürden und den strategischen Entscheidungen (Pivots), die das Projekt von einem spezialisierten Hardware-Experiment zu einem robusten, proaktiven Multi-Agenten-System geformt haben. Die Geschichte gliedert sich in vier prägnante Phasen.

---

## Phase 1: Der NPU-Traum und die hybride Realität

**Das ursprüngliche Ziel:** Das SelfAI-Projekt begann mit einer klaren und ambitionierten Vision: die Entwicklung eines lokalen LLM-Chatbots, der die Hardware-Beschleunigung moderner NPUs (Neural Processing Units), speziell des Qualcomm Hexagon DSP auf Snapdragon-Plattformen, voll ausnutzt. Das strategische Kernziel war es, eine maximale Performance bei lokaler Inferenz zu erreichen und die Abhängigkeit von Cloud-APIs zu minimieren.

**Die Herausforderung: Ein Kampf an der Hardware-Front**

Die Umsetzung dieser Vision erwies sich als ein zermürbender Kampf gegen technische Widrigkeiten, wie die zahlreichen Feedback- und Problemdokumente belegen.

1.  **Tooling-Komplexität:** Die zentrale Bibliothek `llama-cpp-python` war der Schlüssel zur NPU-Anbindung. Doch ihre Kompilierung mit den notwendigen QNN (Qualcomm AI Engine Direct SDK) Flags war ein Albtraum. Der Prozess war unzureichend dokumentiert, erforderte eine fragile Kette von `CMAKE_ARGS`, spezifischen SDK-Pfaden und Umgebungsvariablen. Erfolgreiche Builds waren eher die Ausnahme als die Regel.
2.  **Instabile Entwicklungsumgebungen:** Die Probleme wurden durch instabile Python Virtual Environments (`venv`) verschärft, insbesondere in der WSL-Umgebung (Windows Subsystem for Linux). Anhaltende Fehler bei der Erstellung und Aktivierung von Umgebungen, Dateisystem-Sperren und Inkompatibilitäten blockierten die grundlegendsten Entwicklungsschritte.
3.  **Irreführende Fehler:** Selbst wenn ein Build scheinbar gelang, scheiterte die Kernfunktionalität – das Laden eines Modells – konsistent. Generische Fehlermeldungen wie `"Failed to load model from file"` verschleierten die wahren Ursachen, die oft in einer stillen Fehlfunktion des Hardware-Backends lagen. Alternative Bibliotheken wie `qai_hub_models` erwiesen sich als "Black Boxes", die ohne aussagekräftige Fehlermeldungen versagten.

**Der Pivot: Die Geburt der "Hybrid Inference"-Architektur**

Die Projekt-Reviews aus dieser Zeit (`Projekt_Manager_Feedback.txt`) zeigen eine entscheidende Erkenntnis: Die alleinige Konzentration auf die NPU-Integration war zu riskant. Das Projekt drohte zu scheitern, ohne jemals eine funktionierende Anwendung hervorzubringen.

Um dieses Risiko zu minimieren und ein greifbares Ergebnis zu sichern, wurde die strategische Entscheidung für einen **hybriden Ansatz** getroffen. Ein **CPU-basierter Fallback** wurde als Priorität definiert. Dieser Pfad, der eine Standardkompilierung von `llama-cpp-python` ohne komplexe NPU-Flags nutzt, war weitaus stabiler und einfacher einzurichten.

Dieser Pivot, in den Projektzielen (`docs/OKRs.md`) als **"Hybrid Inference"** formalisiert, war ein Akt des Pragmatismus. Er garantierte eine funktionierende Basis-Anwendung und schuf die Grundlage für alle weiteren Entwicklungen, während die NPU-Forschung parallel weiterlaufen konnte.

---

## Phase 2: Die Konzeption des proaktiven Agenten

**Die neue Grenze:** Mit dem hybriden Modell existierte nun ein funktionierender Chatbot. Doch schnell wurde die nächste Limitierung offensichtlich: Das System war rein **reaktiv**. Es konnte brillante Antworten im Rahmen eines direkten Dialogs generieren, aber es konnte keine komplexen, mehrstufigen Ziele verfolgen. Es war ein Gesprächspartner, aber noch kein autonomer Problemlöser.

**Die Vision: Ein planendes System**

Die Dokumente `Ollama+` und `SelfAI+OllamaEngineering.txt` beschreiben den nächsten großen evolutionären Sprung. Das Ziel war es, SelfAI von einem einfachen Request-Response-System zu einem **proaktiven, zielorientierten Agenten** zu entwickeln. Die Lösung war die Einführung einer komplett neuen Architekturschicht: des **Planner Layer**.

**Der Prototyp: Die Implementierung mit Ollama**

Die erste Implementierung und der Proof-of-Concept für diese Vision wurden mit einem lokal betriebenen **Ollama** als Backend realisiert.
1.  **Planung mit Ollama:** Ein dediziertes LLM innerhalb von Ollama zerlegte das hochgesteckte Ziel des Benutzers in einen detaillierten, schrittweisen Plan aus Subtasks.
2.  **Der Execution Dispatcher:** Ein neuer zentraler Orchestrator, der `ExecutionDispatcher`, wurde geschaffen, um diesen Plan abzuarbeiten.
3.  **Die Merge-Phase:** Eine finale **Merge-Phase** wurde konzipiert, um die Einzelergebnisse zu einer kohärenten Antwort zusammenzufügen.

Dieser mit Ollama realisierte Prototyp war transformativ. Er bewies die Machbarkeit der Architektur und schuf die Grundlage für ein System, das aktiv **plant, ausführt und zusammenführt**. Er ebnete den Weg für die nächste Stufe der Evolution.

---

## Phase 3: Die Zähmung des Chaos durch Prozessreife

**Das wiederkehrende Problem:** Ein Thema zieht sich durch alle frühen Feedback-Dokumente: das Entwicklungs-Chaos. Manuelle `pip install`-Zyklen, das Fehlen einer `requirements.txt`, inkonsistente Python-Versionen und plattformspezifische Probleme (WSL vs. Linux) führten zu ständigen Frustrationen und dem gefürchteten "Works on my machine"-Syndrom. Wertvolles Wissen über Build-Flags und Workarounds ging verloren, und dieselben Probleme wurden immer wieder neu gelöst.

**Die Erkenntnis: Prozess ist wichtiger als Code**

Die Management-Reviews (`Developer_Manager_Feednack.txt`) machten deutlich, dass der ineffiziente und fehleranfällige Entwicklungsprozess eine größere Bremse war als jede einzelne Code-Herausforderung. Die mangelnde Reproduzierbarkeit der Umgebung kostete immense Mengen an Zeit und Energie.

**Der Pivot: Die Einführung von Dev Containern**

Die Lösung war kein Code, sondern eine fundamentale Änderung der Entwicklungsmethodik. Der entscheidende Pivot war die konsequente Einführung von **Dev Containern**.

1.  **Kodifizierte Umgebungen:** Durch eine `devcontainer.json` und ein `Dockerfile` wurde die **gesamte Entwicklungsumgebung** kodifiziert. Dies umfasste die exakte Betriebssystemversion, alle Systemabhängigkeiten (`cmake`, C++ Compiler), die korrekte Python-Version, alle Python-Pakete und die notwendigen Umgebungsvariablen.
2.  **Garantierte Reproduzierbarkeit:** Dieser Schritt eliminierte die gesamte Klasse der Umgebungsprobleme. Jeder Entwickler – und jede Build-Pipeline – arbeitet nun in einer exakt identischen, vorhersagbaren und stabilen Umgebung. Das Onboarding neuer Teammitglieder wurde von Tagen auf Minuten reduziert.

Dieser dritte Pivot war ein Zeichen der Reife des Projekts. Er zeigte die Erkenntnis, dass ein robustes Produkt eine ebenso robuste und professionelle Entwicklungsumgebung erfordert. Er schuf die stabile Grundlage, auf der die komplexen Architekturen der Phasen 1 und 2 zuverlässig betrieben und weiterentwickelt werden konnten.

---

## Phase 4: Konsolidierung und der Aufstieg zum Super-Agenten

**Die neuen Herausforderungen: Skalierung, Stabilität und Aktion**

Mit dem funktionierenden, planenden Prototypen traten zwei neue Herausforderungen in den Vordergrund:
1.  **Abhängigkeit und Stabilität:** Die Abhängigkeit von einem lokal laufenden Ollama-Dienst war für eine robuste Anwendung nicht ideal.
2.  **Vom Plan zur Tat:** Der Agent konnte brillante Pläne schmieden, ihm fehlte aber die Fähigkeit, diese Pläne in konkrete Aktionen im Dateisystem umzusetzen, also **aktiv Code zu lesen, zu schreiben und zu modifizieren.**

**Der Doppel-Pivot: Das Provider-Modell und die Einführung von Tools**

Die Lösung war ein umfassender Umbau in Phase 4, der SelfAI zu seiner heutigen Form als Super-Agent verhalf.

1.  **Umstellung auf ein flexibles Provider-Modell:** Anstatt Ollama zu ersetzen, wurde die Architektur zu einem agnostischen **Provider-Modell** weiterentwickelt.
    *   Sowohl der Planner als auch der Merger wurden so umgebaut, dass sie ihre Implementierung dynamisch aus der `config.yaml` laden.
    *   **Minimax** wurde aufgrund seiner überlegenen Performance, Stabilität und Kosteneffizienz als neuer, **primärer und standardmäßiger Provider** für Planung, Merge und alle anderen LLM-Aufgaben integriert. Ollama blieb als konfigurierbare Option im Code erhalten, was die Flexibilität der Architektur unterstreicht.

2.  **Integration externer Coding-Tools:** Um dem Agenten "Hände zu geben", wurde ein allgemeines **Tool-System** geschaffen, das externe Agenten als Werkzeuge einbindet.
    *   **Aider (`run_aider_task`)** wurde als schnelles Werkzeug für gezielte Code-Änderungen integriert.
    *   **OpenHands** wurde als mächtigeres Werkzeug für komplexe, autonome Refactorings hinzugefügt.
    *   Diese Tools, angetrieben vom leistungsstarken Minimax-Backend, gaben dem Planner erstmals die Möglichkeit, Aktionen in der realen Welt auszuführen.

**Die ultimative Fähigkeit: `/selfimprove`**

Der Höhepunkt dieser Phase ist der `/selfimprove`-Befehl, eine Synthese aller bisherigen Entwicklungsstufen:
1.  Der Benutzer gibt ein hochabstraktes Ziel vor (z.B. `/selfimprove add emoji indicators to UI`).
2.  Der **Planner** (konzipiert in Phase 2, jetzt auf Minimax laufend) erstellt einen detaillierten Plan.
3.  Der **Execution Dispatcher** (Phase 2) orchestriert die Ausführung.
4.  Ein Plan-Schritt ruft das **Aider-Tool** (Phase 4) auf.
5.  Aider, angetrieben vom **Minimax-Backend** (Phase 4), modifiziert die SelfAI-Quelldateien und committet die Änderungen.
6.  Umfangreiche **Sicherheitsmechanismen** (Phase 4) stellen sicher, dass der Agent sich nicht selbst zerstört.

Mit diesem Feature schließt sich der Kreis: SelfAI wurde zu einem Agenten, der sich selbst reflektieren, planen und aktiv verbessern kann.

---

**Fazit (Aktualisiert):** Die Geschichte von SelfAI ist eine Reise von der hardwarenahen Spezialisierung (Phase 1) über die architektonische Neuerfindung zum planenden Agenten (Phase 2) und die prozessuale Professionalisierung (Phase 3) bis hin zum **handelnden und sich selbst modifizierenden Super-Agenten** (Phase 4). Jeder Pivot war eine direkte Reaktion auf eine reale Herausforderung und trug dazu bei, das Projekt widerstandsfähiger, fähiger und letztlich autonomer zu machen.