"""
Fix Generator Module for SelfAI Error Correction System

This module provides functionality to:
- Generate fix strategies for identified errors
- Create multiple fix options (quick/better/best)
- Generate DPPM plans for fixes
- Apply fixes using Aider
- Track fix success rate
"""

import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum

from selfai.core.error_analyzer import ErrorEntry, ErrorPattern


class FixComplexity(Enum):
    """Fix complexity classification"""
    QUICK = "quick"        # Simple one-liner fix (< 5 min)
    MODERATE = "moderate"  # Multiple changes (5-15 min)
    COMPLEX = "complex"    # Refactoring required (15-30 min)
    MAJOR = "major"        # Architectural change (> 30 min)


class FixRisk(Enum):
    """Risk level of applying fix"""
    LOW = "low"          # Safe, tested pattern
    MEDIUM = "medium"    # Some risk, needs testing
    HIGH = "high"        # Breaking changes possible
    CRITICAL = "critical"  # Major system impact


@dataclass
class FixOption:
    """Represents a single fix strategy"""
    option_id: str                    # A, B, C, etc.
    title: str                        # Short description
    description: str                  # Detailed explanation
    complexity: FixComplexity         # How complex to implement
    risk: FixRisk                     # Risk level
    estimated_time: int               # Minutes
    changes: List[str] = field(default_factory=list)  # List of changes to make
    files_affected: List[str] = field(default_factory=list)
    code_diff: Optional[str] = None   # Expected code diff
    success_rate: float = 0.0         # Historical success rate
    breaking_changes: bool = False     # Will this break API?

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['complexity'] = self.complexity.value
        data['risk'] = self.risk.value
        return data


@dataclass
class FixPlan:
    """Complete fix plan with multiple options"""
    error_pattern: ErrorPattern
    options: List[FixOption]
    recommended_option: Optional[str] = None  # Option ID
    analysis: str = ""                        # LLM analysis of error
    root_cause: str = ""                      # Identified root cause
    prevention_suggestions: List[str] = field(default_factory=list)


class FixGenerator:
    """
    Generates fix strategies for identified errors using LLM.

    Features:
    - Analyzes error context
    - Generates multiple fix options
    - Estimates complexity and risk
    - Creates DPPM execution plans
    - Tracks fix success rate
    """

    def __init__(self, llm_interface, project_root: Path):
        """
        Initialize fix generator.

        Args:
            llm_interface: LLM interface for code generation
            project_root: Root directory of project
        """
        self.llm = llm_interface
        self.project_root = Path(project_root)
        self.knowledge_base_path = project_root / "memory" / "error_fixes"
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)

    def analyze_error(self, error_pattern: ErrorPattern) -> FixPlan:
        """
        Analyze error and generate fix options.

        Args:
            error_pattern: ErrorPattern to analyze

        Returns:
            FixPlan with multiple fix options
        """
        # Get error context
        example = error_pattern.examples[0] if error_pattern.examples else None

        if not example:
            return FixPlan(
                error_pattern=error_pattern,
                options=[],
                analysis="No error examples available for analysis"
            )

        # Build analysis prompt
        analysis_prompt = self._build_analysis_prompt(error_pattern, example)

        # Get LLM analysis
        try:
            response = self.llm.generate_response(
                system_prompt="You are an expert Python debugger and error analyst. Analyze errors and suggest fixes.",
                user_prompt=analysis_prompt,
                history=[],
                max_output_tokens=1024
            )

            # Parse response to extract fix options
            fix_plan = self._parse_fix_response(response, error_pattern)

            # Load historical data if available
            self._enrich_with_history(fix_plan)

            return fix_plan

        except Exception as e:
            return FixPlan(
                error_pattern=error_pattern,
                options=[],
                analysis=f"Failed to analyze error: {str(e)}"
            )

    def _build_analysis_prompt(self, pattern: ErrorPattern, example: ErrorEntry) -> str:
        """
        Build prompt for LLM error analysis.

        Args:
            pattern: ErrorPattern to analyze
            example: Example ErrorEntry

        Returns:
            Formatted prompt string
        """
        prompt = f"""Analyze this Python error and suggest fixes:

ERROR TYPE: {pattern.error_type}
OCCURRENCES: {pattern.occurrences}
MESSAGE: {example.message}

"""

        if example.file_path:
            prompt += f"FILE: {example.file_path}\n"

        if example.line_number:
            prompt += f"LINE: {example.line_number}\n"

        if example.traceback:
            prompt += f"\nTRACEBACK:\n" + "\n".join(example.traceback[:10]) + "\n"

        prompt += """
Provide analysis in this JSON format:
{
  "root_cause": "Brief explanation of what causes this error",
  "analysis": "Detailed analysis of the problem",
  "options": [
    {
      "id": "A",
      "title": "Quick fix",
      "description": "Detailed description",
      "complexity": "quick|moderate|complex|major",
      "risk": "low|medium|high|critical",
      "estimated_time": <minutes>,
      "changes": ["Change 1", "Change 2"],
      "files_affected": ["file1.py"],
      "breaking_changes": false
    },
    {
      "id": "B",
      "title": "Better fix",
      "description": "...",
      ...
    },
    {
      "id": "C",
      "title": "Best fix",
      "description": "...",
      ...
    }
  ],
  "recommended": "A",
  "prevention": ["Suggestion 1", "Suggestion 2"]
}

Provide 2-3 fix options with increasing quality but also complexity.
"""

        return prompt

    def _parse_fix_response(self, response: str, pattern: ErrorPattern) -> FixPlan:
        """
        Parse LLM response into FixPlan.

        Args:
            response: LLM response text
            pattern: Original error pattern

        Returns:
            Parsed FixPlan
        """
        try:
            # Try to extract JSON from response
            response = response.strip()

            # Remove markdown code blocks if present
            if response.startswith('```json'):
                response = '\n'.join(response.split('\n')[1:])
            if response.startswith('```'):
                response = '\n'.join(response.split('\n')[1:])
            if response.endswith('```'):
                response = '\n'.join(response.split('\n')[:-1])

            data = json.loads(response.strip())

            # Parse options
            options = []
            for opt_data in data.get('options', []):
                option = FixOption(
                    option_id=opt_data.get('id', '?'),
                    title=opt_data.get('title', 'Unnamed fix'),
                    description=opt_data.get('description', ''),
                    complexity=FixComplexity(opt_data.get('complexity', 'moderate')),
                    risk=FixRisk(opt_data.get('risk', 'medium')),
                    estimated_time=opt_data.get('estimated_time', 10),
                    changes=opt_data.get('changes', []),
                    files_affected=opt_data.get('files_affected', []),
                    breaking_changes=opt_data.get('breaking_changes', False)
                )
                options.append(option)

            return FixPlan(
                error_pattern=pattern,
                options=options,
                recommended_option=data.get('recommended'),
                analysis=data.get('analysis', ''),
                root_cause=data.get('root_cause', ''),
                prevention_suggestions=data.get('prevention', [])
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback: create generic fix option
            return FixPlan(
                error_pattern=pattern,
                options=[
                    FixOption(
                        option_id="A",
                        title="Generic fix",
                        description=f"Fix {pattern.error_type} error",
                        complexity=FixComplexity.MODERATE,
                        risk=FixRisk.MEDIUM,
                        estimated_time=10,
                        changes=["Investigate and fix error"],
                        files_affected=[pattern.examples[0].file_path] if pattern.examples and pattern.examples[0].file_path else []
                    )
                ],
                analysis=response[:500],  # Use raw response as analysis
                root_cause=f"Parse error: {str(e)}"
            )

    def _enrich_with_history(self, fix_plan: FixPlan) -> None:
        """
        Enrich fix options with historical success data.

        Args:
            fix_plan: FixPlan to enrich
        """
        error_type = fix_plan.error_pattern.error_type
        history_file = self.knowledge_base_path / f"{error_type}.json"

        if not history_file.exists():
            return

        try:
            history = json.loads(history_file.read_text(encoding='utf-8'))

            for option in fix_plan.options:
                # Match option by title similarity
                for hist_entry in history.get('fixes', []):
                    if self._similar_strings(option.title, hist_entry.get('title', '')):
                        option.success_rate = hist_entry.get('success_rate', 0.0)
                        break

        except Exception:
            pass  # Silently fail if history can't be loaded

    def _similar_strings(self, s1: str, s2: str, threshold: float = 0.6) -> bool:
        """
        Check if two strings are similar (simple heuristic).

        Args:
            s1: First string
            s2: Second string
            threshold: Similarity threshold (0-1)

        Returns:
            True if strings are similar enough
        """
        s1_lower = s1.lower()
        s2_lower = s2.lower()

        # Simple word overlap check
        words1 = set(s1_lower.split())
        words2 = set(s2_lower.split())

        if not words1 or not words2:
            return False

        overlap = len(words1 & words2)
        total = max(len(words1), len(words2))

        return (overlap / total) >= threshold

    def create_dppm_plan(self, fix_option: FixOption, error_pattern: ErrorPattern, agent_key: str = "default") -> Dict[str, Any]:
        """
        Create DPPM plan for applying a fix.

        Args:
            fix_option: FixOption to execute
            error_pattern: Original error pattern
            agent_key: Agent to use for execution

        Returns:
            DPPM plan dictionary
        """
        # Build subtasks
        subtasks = []

        # S1: Analyze current code
        subtasks.append({
            "id": "S1",
            "title": "Analyze error location",
            "objective": f"Read and analyze code at error location: {fix_option.files_affected}",
            "agent_key": agent_key,
            "engine": "minimax",
            "parallel_group": 1,
            "depends_on": [],
            "notes": f"Understanding {error_pattern.error_type}"
        })

        # S2: Apply fix with Aider
        fix_description = f"""Fix {error_pattern.error_type} error using this strategy:

{fix_option.description}

Changes to make:
""" + "\n".join(f"- {change}" for change in fix_option.changes)

        subtasks.append({
            "id": "S2",
            "title": f"Apply {fix_option.title}",
            "objective": fix_description,
            "agent_key": agent_key,
            "engine": "minimax",
            "parallel_group": 2,
            "depends_on": ["S1"],
            "notes": f"Complexity: {fix_option.complexity.value}, Risk: {fix_option.risk.value}"
        })

        # S3: Validate fix
        subtasks.append({
            "id": "S3",
            "title": "Validate fix",
            "objective": "Verify that the error is fixed and no new errors introduced",
            "agent_key": agent_key,
            "engine": "minimax",
            "parallel_group": 3,
            "depends_on": ["S2"],
            "notes": "Check syntax, run tests if available"
        })

        # Create plan
        plan = {
            "subtasks": subtasks,
            "merge": {
                "strategy": "Verify error fix was successful and summarize changes",
                "steps": [
                    {
                        "title": "Fix Summary",
                        "description": "Summarize what was fixed and verify no regressions",
                        "depends_on": ["S3"]
                    }
                ]
            },
            "metadata": {
                "error_type": error_pattern.error_type,
                "fix_option_id": fix_option.option_id,
                "fix_complexity": fix_option.complexity.value,
                "fix_risk": fix_option.risk.value,
                "estimated_time": fix_option.estimated_time
            }
        }

        return plan

    def save_fix_result(self, fix_option: FixOption, error_pattern: ErrorPattern, success: bool) -> None:
        """
        Save fix result to knowledge base for learning.

        Args:
            fix_option: FixOption that was applied
            error_pattern: Original error pattern
            success: Whether fix was successful
        """
        error_type = error_pattern.error_type
        history_file = self.knowledge_base_path / f"{error_type}.json"

        # Load existing history
        if history_file.exists():
            try:
                history = json.loads(history_file.read_text(encoding='utf-8'))
            except Exception:
                history = {'error_type': error_type, 'fixes': []}
        else:
            history = {'error_type': error_type, 'fixes': []}

        # Find or create fix entry
        fix_entry = None
        for entry in history['fixes']:
            if entry.get('title') == fix_option.title:
                fix_entry = entry
                break

        if not fix_entry:
            fix_entry = {
                'title': fix_option.title,
                'description': fix_option.description,
                'complexity': fix_option.complexity.value,
                'total_attempts': 0,
                'successful_attempts': 0,
                'success_rate': 0.0
            }
            history['fixes'].append(fix_entry)

        # Update statistics
        fix_entry['total_attempts'] += 1
        if success:
            fix_entry['successful_attempts'] += 1

        fix_entry['success_rate'] = (
            fix_entry['successful_attempts'] / fix_entry['total_attempts']
        )

        # Save updated history
        try:
            history_file.write_text(
                json.dumps(history, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception:
            pass  # Silently fail if can't save
