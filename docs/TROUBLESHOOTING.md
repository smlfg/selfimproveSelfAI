# Troubleshooting

Dieses Dokument listet häufige Fehlerbilder und deren Behebung auf.

## Black Box Diagnostik

- **Problem**: Generische oder fehlende Fehlermeldungen erschweren die Fehlerdiagnose.
- **Lösung**: Implementierung von detailliertem Logging im `NPUInterfaceLayer`, um spezifische Fehlerinformationen zu erhalten.

## Inkonsequente Entwicklungsumgebung

- **Problem**: "Works on my machine"-Effekte durch instabile `venvs` und fehlendes Dependency-Management.
- **Lösung**: Verwendung von Dev Containern (Docker), um eine reproduzierbare Entwicklungsumgebung zu gewährleisten.

## Integrität von Modell-Assets

- **Problem**: Einsatz beschädigter oder manipulierter Modelldateien.
- **Lösung**: Automatisierte Integritätsprüfungen (SHA256, `gguf-checksum.py`) vor dem Laden von Modellen.

## Wissensmanagement

- **Problem**: Fragmentierte Dokumentation führt zu wiederholten Fehlern.
- **Lösung**: Etablierung eines zentralen Wissensmanagements mit `LESSONS_LEARNED.md`, `TROUBLESHOOTING.md` und `BUILD.md`.
