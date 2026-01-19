"""
Self-Improvement Engine (V2)

Core logic for analyzing the codebase and generating improvement proposals.
Implements the READ-ONLY analysis phase.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import os

from selfai.core.improvement_suggestions import ImprovementProposal, parse_proposals_from_json
from selfai.ui.terminal_ui import TerminalUI

class SelfImprovementEngine:
    def __init__(self, project_root: Path, llm_interface, ui: TerminalUI):
        self.project_root = project_root
        self.llm_interface = llm_interface
        self.ui = ui

    def analyze_codebase(self) -> Dict[str, Any]:
        """
        Scans the project structure to provide context for analysis.
        Does NOT read all files, just structure and stats.
        """
        total_files = 0
        total_lines = 0
        modules = []
        file_list = []

        # Focus on core directories
        target_dirs = ["selfai", "scripts"]
        
        for target in target_dirs:
            path = self.project_root / target
            if not path.exists():
                continue

            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(".py"):
                        file_path = Path(root) / file
                        try:
                            # Read lines for stats only
                            with open(file_path, "r", encoding="utf-8") as f:
                                lines = len(f.readlines())
                            
                            rel_path = str(file_path.relative_to(self.project_root))
                            file_list.append({"path": rel_path, "lines": lines})
                            
                            total_files += 1
                            total_lines += lines
                            
                            module_name = rel_path.replace("/", ".").replace(".py", "")
                            if "__init__" not in module_name:
                                modules.append(module_name)
                                
                        except Exception:
                            pass

        return {
            "total_files": total_files,
            "total_lines": total_lines,
            "modules": modules,
            "files": sorted(file_list, key=lambda x: x["lines"], reverse=True)
        }

    def generate_proposals(self, goal: str) -> List[ImprovementProposal]:
        """
        Generates improvement proposals based on the goal and code analysis.
        """
        self.ui.status("Analysiere Projekt-Struktur...", "info")
        analysis = self.analyze_codebase()
        
        # Prepare context for LLM
        files_summary = "\n".join([
            f"- {f['path']} ({f['lines']} lines)" 
            for f in analysis["files"][:30]  # Top 30 largest files
        ])

        prompt = f"""
        You are a Senior Software Architect analyzing the SelfAI codebase.
        
        GOAL: {goal} 
        
        CODEBASE STATS:
        - Files: {analysis['total_files']} Python files
        - Lines: {analysis['total_lines']} lines of code
        
        KEY FILES:
        {files_summary}
        
        TASK:
        Identify 3 concrete, actionable improvement proposals to achieve the GOAL.
        
        REQUIREMENTS:
        1. Proposals must be realistic and implementable.
        2. Focus on high impact changes.
        3. Estimate effort correctly.
        4. Identify affected files accurately.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "proposals": [
                {{
                    "id": 1,
                    "title": "Short Title",
                    "description": "Clear description of the change",
                    "files": ["path/to/file1.py", "path/to/file2.py"],
                    "effort_minutes": 15,
                    "impact_percent": 30,
                    "implementation_steps": [
                        "Step 1: ...",
                        "Step 2: ..."
                    ],
                    "priority": "high"
                }}
            ]
        }}
        
        Return ONLY valid JSON. No markdown, no explanations.
        """

        self.ui.status("Generiere Verbesserungsvorschläge (LLM)...", "info")

        # Call LLM - try direct API call if MiniMax to avoid tool-calling interference
        if hasattr(self.llm_interface, "_call_api_direct"):
            # Use direct API call (bypasses identity enforcement and tool-calling)
            response = self.llm_interface._call_api_direct(
                system_prompt="You are a JSON-generating code architect. Output ONLY valid JSON, no markdown, no XML tags, no explanations.",
                user_prompt=prompt,
                max_tokens=2048,
                temperature=0.3  # Lower temperature for structured output
            )
        elif hasattr(self.llm_interface, "generate_response"):
            response = self.llm_interface.generate_response(
                system_prompt="You are a JSON-generating code architect. Output ONLY valid JSON.",
                user_prompt=prompt,
                max_tokens=2048
            )
        else:
            # Fallback
            response = self.llm_interface.chat(
                system_prompt="You are a JSON-generating code architect. Output ONLY valid JSON.",
                user_prompt=prompt
            )

        # Parse JSON
        proposals = parse_proposals_from_json(response)
        
        return proposals
