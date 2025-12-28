"""
UI Metrics Collection for A/B Testing

Tracks UI variant usage and user interactions to compare
TerminalUI (V1) vs GeminiUI (V2) performance and preferences.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class UIMetricsCollector:
    """Collects usage metrics for UI A/B testing"""

    def __init__(self, metrics_dir: Path):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.ui_variant: Optional[str] = None
        self.session_start: datetime = datetime.now()

        # Session metrics
        self.metrics = {
            "session_id": self.session_id,
            "ui_variant": None,
            "session_start": self.session_start.isoformat(),
            "session_end": None,
            "total_interactions": 0,
            "commands_used": [],
            "errors_encountered": 0,
            "plans_created": 0,
            "plans_executed": 0,
            "agent_switches": 0,
            "yolo_mode_activations": 0,
            "ui_variant_checks": 0,
        }

    def set_ui_variant(self, variant: str):
        """Set the UI variant for this session"""
        self.ui_variant = variant
        self.metrics["ui_variant"] = variant

    def record_interaction(self, interaction_type: str, details: Optional[Dict[str, Any]] = None):
        """Record a user interaction"""
        self.metrics["total_interactions"] += 1

        # Track specific interaction types
        if interaction_type == "command":
            cmd = details.get("command", "unknown") if details else "unknown"
            self.metrics["commands_used"].append({
                "command": cmd,
                "timestamp": datetime.now().isoformat()
            })
        elif interaction_type == "error":
            self.metrics["errors_encountered"] += 1
        elif interaction_type == "plan_created":
            self.metrics["plans_created"] += 1
        elif interaction_type == "plan_executed":
            self.metrics["plans_executed"] += 1
        elif interaction_type == "agent_switch":
            self.metrics["agent_switches"] += 1
        elif interaction_type == "yolo_toggle":
            self.metrics["yolo_mode_activations"] += 1
        elif interaction_type == "ui_check":
            self.metrics["ui_variant_checks"] += 1

    def end_session(self):
        """Mark session end and save metrics"""
        self.metrics["session_end"] = datetime.now().isoformat()
        self._save_metrics()

    def _save_metrics(self):
        """Save metrics to JSON file"""
        filename = f"ui_metrics_{self.session_id}.json"
        filepath = self.metrics_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, indent=2, ensure_ascii=False)

    def get_summary(self) -> str:
        """Get session summary for display"""
        duration = (datetime.now() - self.session_start).total_seconds() / 60

        summary = f"""
╔═══════════════════════════════════════════════════════════╗
║              SESSION METRICS SUMMARY                      ║
╚═══════════════════════════════════════════════════════════╝

UI Variant: {self.ui_variant or 'Unknown'}
Session Duration: {duration:.1f} minutes

Total Interactions: {self.metrics['total_interactions']}
Commands Used: {len(self.metrics['commands_used'])}
Plans Created: {self.metrics['plans_created']}
Plans Executed: {self.metrics['plans_executed']}
Agent Switches: {self.metrics['agent_switches']}
Errors Encountered: {self.metrics['errors_encountered']}
YOLO Mode Toggles: {self.metrics['yolo_mode_activations']}

Most Used Commands:
"""
        # Count command frequency
        cmd_freq = {}
        for cmd_entry in self.metrics["commands_used"]:
            cmd = cmd_entry["command"]
            cmd_freq[cmd] = cmd_freq.get(cmd, 0) + 1

        # Show top 5
        top_cmds = sorted(cmd_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        for cmd, count in top_cmds:
            summary += f"  • {cmd}: {count}x\n"

        return summary


def analyze_ui_metrics(metrics_dir: Path) -> str:
    """Analyze all collected metrics and compare UI variants"""
    metrics_dir = Path(metrics_dir)

    if not metrics_dir.exists():
        return "No metrics collected yet."

    v1_sessions = []
    v2_sessions = []

    # Load all metric files
    for filepath in metrics_dir.glob("ui_metrics_*.json"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            variant = data.get("ui_variant", "unknown")
            if "V1" in variant or "Terminal" in variant:
                v1_sessions.append(data)
            elif "V2" in variant or "Gemini" in variant:
                v2_sessions.append(data)
        except Exception:
            continue

    # Calculate averages
    def avg_metric(sessions, key):
        if not sessions:
            return 0
        return sum(s.get(key, 0) for s in sessions) / len(sessions)

    report = f"""
╔═══════════════════════════════════════════════════════════╗
║           UI A/B TESTING ANALYSIS REPORT                  ║
╚═══════════════════════════════════════════════════════════╝

TerminalUI (V1):
  Sessions: {len(v1_sessions)}
  Avg Interactions: {avg_metric(v1_sessions, 'total_interactions'):.1f}
  Avg Plans: {avg_metric(v1_sessions, 'plans_created'):.1f}
  Avg Errors: {avg_metric(v1_sessions, 'errors_encountered'):.1f}
  Avg Agent Switches: {avg_metric(v1_sessions, 'agent_switches'):.1f}

GeminiUI (V2):
  Sessions: {len(v2_sessions)}
  Avg Interactions: {avg_metric(v2_sessions, 'total_interactions'):.1f}
  Avg Plans: {avg_metric(v2_sessions, 'plans_created'):.1f}
  Avg Errors: {avg_metric(v2_sessions, 'errors_encountered'):.1f}
  Avg Agent Switches: {avg_metric(v2_sessions, 'agent_switches'):.1f}

Recommendation:
"""

    if len(v1_sessions) == 0 and len(v2_sessions) == 0:
        report += "  Insufficient data for comparison.\n"
    elif len(v1_sessions) >= 3 and len(v2_sessions) >= 3:
        # Simple comparison
        v1_score = avg_metric(v1_sessions, 'total_interactions') - avg_metric(v1_sessions, 'errors_encountered')
        v2_score = avg_metric(v2_sessions, 'total_interactions') - avg_metric(v2_sessions, 'errors_encountered')

        if v2_score > v1_score:
            report += "  ✅ GeminiUI (V2) shows better engagement and fewer errors.\n"
        elif v1_score > v2_score:
            report += "  ✅ TerminalUI (V1) shows better engagement and fewer errors.\n"
        else:
            report += "  ⚖️  Both UI variants perform similarly.\n"
    else:
        report += f"  Collect more sessions (V1: {len(v1_sessions)}/3, V2: {len(v2_sessions)}/3)\n"

    return report
