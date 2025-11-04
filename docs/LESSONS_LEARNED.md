# Lessons Learned

Dieses Dokument erfasst Probleme und Lösungen als lebendes Dokument.

## Black Box Diagnostik

- **Lektion**: Generische Fehlermeldungen sind ein massives Hindernis.
- **Maßnahme**: Jede Komponente muss spezifische, kontextbezogene Fehlermeldungen ausgeben.

## Entwicklungsumgebung

- **Lektion**: Manuelle `venv`-Setups sind fehleranfällig und nicht skalierbar.
- **Maßnahme**: Dev Container sind für komplexe, hardwarenahe Projekte unerlässlich.

## Modell-Integrität

- **Lektion**: Das Laden von Modellen ohne Verifizierung ist ein Sicherheits- und Stabilitätsrisiko.
- **Maßnahme**: Integritätsprüfungen sind ein nicht verhandelbarer Schritt im Lade-Prozess.

## Wissensmanagement

- **Lektion**: Ohne zentrales Wissensmanagement wiederholen sich Fehler und der Wissenstransfer scheitert.
- **Maßnahme**: Eine klare Dokumentationsstruktur (`BUILD.md`, `TROUBLESHOOTING.md`, `LESSONS_LEARNED.md`) ist entscheidend.
