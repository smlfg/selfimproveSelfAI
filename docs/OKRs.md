# Objectives and Key Results (OKRs) - SelfAI Hybrid Inference

Dieses Dokument definiert die Ziele, Metriken und Akzeptanzkriterien für das SelfAI Hybrid Inference Projekt. Es dient als Referenz für Entwicklung, Testing und Abnahme.

---

## 1. Projektziele (Stakeholder Goals)

| Ziel-ID | Zielbeschreibung | Akzeptanzkriterium |
| :--- | :--- | :--- |
| **G-1** | **Stabile und Reproduzierbare NPU-Inferenz** | Ein Prompt wird erfolgreich und wiederholbar vom NPU-Backend verarbeitet. Die Umgebung kann mittels Dev Container deterministisch aufgebaut werden. |
| **G-2** | **Robuster Hybrid-Betrieb mit CPU-Fallback** | Bei Ausfall des NPU-Backends schaltet das System transparent auf das CPU-Fallback um und liefert eine valide Antwort ohne Absturz. |
| **G-3** | **Modulare und erweiterbare Agenten-Architektur** | Die Codebasis ist sauber in die `SelfAI`-Kernmodule (`AgentManager`, `MemorySystem`, `NPUInterface`) getrennt. |

---

## 2. Key Performance Indicators (KPIs) und Metriken

### 2.1. Service-Verfügbarkeit

*   **Ziel: 99% Uptime**
    *   **Definition:** 99 von 100 Benutzer-Prompts führen zu einer erfolgreichen Antwort (via NPU oder CPU).
    *   **Metrik (M-1): Gesamte Fehlerrate:** < 1% der Anfragen führen zu einem Absturz, Timeout oder einer unbehandelten Fehlermeldung.
    *   **Metrik (M-2): Fallback-Quote:** < 5% der Anfragen müssen vom CPU-Fallback bearbeitet werden. Dies ist ein Indikator für die Stabilität des primären NPU-Backends.

### 2.2. Performance und Latenz

*   **Ziel: Nahtlose Benutzererfahrung**
    *   **Metrik (M-3): p95 Time-to-First-Token (TTFT):** Die Zeit bis zum ersten sichtbaren Token liegt in 95% der Fälle unter den Zielwerten.
        *   **NPU-Ziel:** < 1.0 Sekunden
        *   **CPU-Ziel:** < 2.5 Sekunden
    *   **Metrik (M-4): p95 Tokens per Second (TPS):** Die Generierungsgeschwindigkeit liegt in 95% der Fälle über den Zielwerten.
        *   **NPU-Ziel:** > 50 TPS
        *   **CPU-Ziel:** > 15 TPS

### 2.3. Engineering & Reproduzierbarkeit

*   **Ziel: Effiziente Entwicklung und Wartung**
    *   **Metrik (M-5): Umgebungs-Setup-Erfolgsrate:** 100% der Setup-Versuche über den Dev Container sind erfolgreich.
    *   **Metrik (M-6): Umgebungs-Setup-Zeit:** < 10 Minuten vom Klonen des Repos bis zur ersten erfolgreichen Inferenz.

---

## 3. Skizzierte Akzeptanztests

Die folgenden Testszenarien werden zur Validierung der Akzeptanzkriterien herangezogen:

| Test-ID | Szenario | Erwartetes Ergebnis |
| :--- | :--- | :--- |
| **AT-1** | **Happy Path (NPU)** | Ein Standard-Prompt wird an das System gesendet. Das NPU-Backend ist aktiv. | Das System liefert eine Antwort innerhalb der p95-Latenzziele für die NPU. |
| **AT-2** | **Failover (CPU)** | Das NPU-Backend wird deaktiviert (z.B. AnythingLLM-Server gestoppt). Ein Standard-Prompt wird gesendet. | Das System erkennt den Ausfall, protokolliert ihn, wechselt zum CPU-Fallback und liefert eine Antwort innerhalb der p95-Latenzziele für die CPU. |
| **AT-3** | **Recovery (NPU)** | Nach AT-2 wird das NPU-Backend wieder aktiviert. | Das System erkennt die Wiederverfügbarkeit (via Health Check) und verarbeitet den nächsten Prompt erfolgreich über die NPU. |
| **AT-4** | **Reproduzierbarkeit** | Ein neuer Entwickler folgt der Anleitung in `README.md` und `docs/BUILD.md` in einer sauberen Umgebung. | Der Dev Container wird erfolgreich gebaut und die Anwendung kann gestartet und für eine Inferenz genutzt werden. |
| **AT-5** | **Architektur-Validierung** | Code-Review und statische Analyse. | Die Kernlogik ist klar den Modulen `AgentManager`, `MemorySystem` und `NPUInterface` zugeordnet. |
