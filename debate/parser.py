"""
Design Parameter Parser
=======================
Extracts quantitative parameter values from LLM JSON responses.
Handles malformed JSON, missing fields, and type coercion.
"""

import json
import re
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class ParameterValue:
    """A single parsed parameter value with metadata."""
    domain_id: str
    param_id: str
    value: Any  # numeric or categorical
    unit: str = ""
    justification: str = ""
    uncertainty_range: Optional[List[float]] = None
    key_assumption: str = ""
    raw_text: str = ""


@dataclass
class ParameterSet:
    """Complete set of parsed parameters from one agent's proposal."""
    values: Dict[str, ParameterValue] = field(default_factory=dict)  # key = "domain_id.param_id"
    parse_errors: List[str] = field(default_factory=list)

    def get(self, domain_id: str, param_id: str) -> Optional[ParameterValue]:
        key = f"{domain_id}.{param_id}"
        return self.values.get(key)

    def get_numeric(self, domain_id: str, param_id: str) -> Optional[float]:
        pv = self.get(domain_id, param_id)
        if pv is None:
            return None
        try:
            return float(pv.value)
        except (TypeError, ValueError):
            return None

    def get_categorical(self, domain_id: str, param_id: str) -> Optional[str]:
        pv = self.get(domain_id, param_id)
        if pv is None:
            return None
        return str(pv.value)


def _repair_truncated_json(text: str) -> Optional[str]:
    """Attempt to repair JSON truncated by max_tokens limit."""
    # Count open/close braces and brackets
    open_braces = text.count('{') - text.count('}')
    open_brackets = text.count('[') - text.count(']')

    if open_braces <= 0 and open_brackets <= 0:
        return None  # Not truncated

    # Find last complete key-value pair
    # Remove incomplete trailing content after last complete value
    # Look for last complete "}" or "]" or quoted string
    repaired = text.rstrip()

    # Remove incomplete trailing content (partial key, partial string, etc.)
    # Find the last comma or complete value
    patterns_to_strip = [
        r',?\s*"[^"]*$',              # trailing partial key (with or without comma)
        r',\s*"[^"]*":\s*$',          # trailing key with no value
        r',\s*"[^"]*":\s*"[^"]*$',    # trailing key with partial string value
        r',\s*"[^"]*":\s*\{[^}]*$',   # trailing key with partial object
        r',\s*"[^"]*":\s*\[[^\]]*$',  # trailing key with partial array
        r',\s*$',                      # trailing comma
    ]
    for p in patterns_to_strip:
        repaired = re.sub(p, '', repaired, flags=re.DOTALL)

    # Recalculate balance after stripping (stripping may have removed braces/brackets)
    open_braces = repaired.count('{') - repaired.count('}')
    open_brackets = repaired.count('[') - repaired.count(']')

    # Close open brackets and braces
    repaired += ']' * max(0, open_brackets)
    repaired += '}' * max(0, open_braces)

    try:
        result = json.loads(repaired)
        if isinstance(result, dict):
            logger.info(f"Repaired truncated JSON: added {open_braces} braces, {open_brackets} brackets")
            return repaired
    except json.JSONDecodeError:
        pass

    return None


def _extract_json(text: str) -> Optional[Dict]:
    """Extract JSON from LLM response, handling markdown code blocks and prose."""
    # Try direct JSON parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block (most reliable)
    for pattern in [r"```json\s*\n(.*?)```", r"```\s*\n(.*?)```"]:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in sorted(matches, key=len, reverse=True):
            try:
                parsed = json.loads(match)
                if isinstance(parsed, dict) and len(parsed) >= 3:
                    return parsed
            except json.JSONDecodeError:
                # Try repairing truncated JSON inside code block
                repaired = _repair_truncated_json(match)
                if repaired:
                    try:
                        parsed = json.loads(repaired)
                        if isinstance(parsed, dict) and len(parsed) >= 3:
                            return parsed
                    except json.JSONDecodeError:
                        pass
                continue
        for match in sorted(matches, key=len, reverse=True):
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                repaired = _repair_truncated_json(match)
                if repaired:
                    try:
                        return json.loads(repaired)
                    except json.JSONDecodeError:
                        pass
                continue

    # Handle case where text starts with ```json but is truncated (no closing ```)
    code_start = re.match(r'^```(?:json)?\s*\n', text)
    if code_start:
        json_text = text[code_start.end():]
        # Remove trailing ``` if present
        json_text = re.sub(r'\n```\s*$', '', json_text)
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            repaired = _repair_truncated_json(json_text)
            if repaired:
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError:
                    pass

    # Try to find JSON objects in the text by matching balanced braces
    # Start from each { and try to find a matching } that parses as JSON
    brace_positions = [i for i, c in enumerate(text) if c == '{']
    best_result = None
    best_len = 0
    for start in brace_positions:
        depth = 0
        for end in range(start, len(text)):
            if text[end] == '{':
                depth += 1
            elif text[end] == '}':
                depth -= 1
                if depth == 0:
                    candidate = text[start:end + 1]
                    if len(candidate) > best_len:
                        try:
                            parsed = json.loads(candidate)
                            if isinstance(parsed, dict) and len(parsed) >= 2:
                                best_result = parsed
                                best_len = len(candidate)
                        except json.JSONDecodeError:
                            pass
                    break
    if best_result is not None:
        return best_result

    # Last resort: try to repair truncated JSON (from max_tokens cutoff)
    # Extract the JSON portion (strip leading prose, markdown fences)
    json_text = text
    # Strip markdown fences
    json_text = re.sub(r'^```json\s*\n', '', json_text)
    json_text = re.sub(r'^```\s*\n', '', json_text)
    json_text = re.sub(r'\n```\s*$', '', json_text)
    # Find first {
    first_brace = json_text.find('{')
    if first_brace >= 0:
        json_text = json_text[first_brace:]
        repaired = _repair_truncated_json(json_text)
        if repaired:
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass

    return None


def _normalize_domain_key(key: str, valid_domains: List[str]) -> Optional[str]:
    """Fuzzy-match a key from LLM output to a valid domain ID."""
    key_lower = key.lower().strip().replace(" ", "_").replace("-", "_")

    # Direct match
    if key_lower in valid_domains:
        return key_lower

    # Strip numeric prefix (e.g., "1. Clinical Model" -> "clinical_model")
    stripped = re.sub(r"^\d+[\.\)]\s*", "", key_lower)
    if stripped in valid_domains:
        return stripped

    # Partial match
    for domain in valid_domains:
        if domain in key_lower or key_lower in domain:
            return domain

    # Word overlap
    key_words = set(key_lower.split("_"))
    best_match = None
    best_overlap = 0
    for domain in valid_domains:
        domain_words = set(domain.split("_"))
        overlap = len(key_words & domain_words)
        if overlap > best_overlap:
            best_overlap = overlap
            best_match = domain
    if best_overlap >= 1:
        return best_match

    return None


def extract_parameters(raw_text: str, domain_ids: List[str]) -> ParameterSet:
    """
    Parse LLM response into structured ParameterSet.

    Handles various JSON structures agents might produce:
    - Flat: {"domain_name": {"value": ..., "unit": ...}}
    - Nested: {"domain_name": {"param_name": {"value": ..., "unit": ...}}}
    - Array-style: {"domains": [{"name": "...", "value": ...}]}
    """
    result = ParameterSet()
    data = _extract_json(raw_text)

    if data is None:
        result.parse_errors.append("Failed to extract JSON from response")
        logger.debug(f"Failed to extract JSON. Text starts with: {raw_text[:300]}")
        return result

    # Unwrap common top-level wrappers (e.g., {"proposal": {...}}, {"domains": {...}})
    wrapper_keys = ("proposal", "domains", "design", "parameters", "ai_aco_design",
                    "ai_aco", "response", "recommendations")
    for wk in wrapper_keys:
        if wk in data and isinstance(data[wk], dict) and len(data) <= 3:
            data = data[wk]
            break
        # Also handle list-style: {"domains": [{"name": "...", ...}]}
        if wk in data and isinstance(data[wk], list):
            unwrapped = {}
            for item in data[wk]:
                if isinstance(item, dict) and "name" in item:
                    unwrapped[item["name"]] = {k: v for k, v in item.items() if k != "name"}
            if unwrapped:
                data = unwrapped
                break

    skip_keys = {"changes", "dissent", "error", "dissents", "summary",
                 "overall_assessment", "overall_viability_assessment",
                 "implementation_notes", "notes", "evaluation_criteria"}

    for key, value in data.items():
        if key.lower() in skip_keys:
            continue

        domain_id = _normalize_domain_key(key, domain_ids)
        if domain_id is None:
            continue

        if not isinstance(value, dict):
            # Direct scalar value for a domain
            pv = ParameterValue(
                domain_id=domain_id,
                param_id="primary",
                value=value,
                raw_text=str(value),
            )
            result.values[f"{domain_id}.primary"] = pv
            continue

        # Check if this is a domain-level dict with sub-parameters
        # or a single parameter dict with "value" key
        if "value" in value:
            # Single parameter for the whole domain
            pv = _parse_param_value(domain_id, "primary", value, raw_text)
            if pv:
                result.values[f"{domain_id}.primary"] = pv
        else:
            # Sub-parameters
            for sub_key, sub_value in value.items():
                if sub_key in ("changes", "dissent", "error"):
                    continue
                if isinstance(sub_value, dict):
                    pv = _parse_param_value(domain_id, sub_key, sub_value, raw_text)
                    if pv:
                        result.values[f"{domain_id}.{sub_key}"] = pv
                else:
                    # Direct value without metadata
                    pv = ParameterValue(
                        domain_id=domain_id,
                        param_id=sub_key,
                        value=sub_value,
                        raw_text=str(sub_value),
                    )
                    result.values[f"{domain_id}.{sub_key}"] = pv

    if not result.values:
        result.parse_errors.append("No valid parameters extracted")

    return result


def _parse_param_value(
    domain_id: str, param_id: str, data: Dict, raw_text: str
) -> Optional[ParameterValue]:
    """Parse a single parameter value from a dict."""
    value = data.get("value")
    if value is None:
        # Try alternative keys
        for alt_key in ("recommended", "recommendation", "parameter", "amount", "rate", "percentage"):
            if alt_key in data:
                value = data[alt_key]
                break

    if value is None:
        return None

    uncertainty = data.get("uncertainty_range")
    if isinstance(uncertainty, (list, tuple)) and len(uncertainty) == 2:
        try:
            uncertainty = [float(uncertainty[0]), float(uncertainty[1])]
        except (TypeError, ValueError):
            uncertainty = None
    else:
        uncertainty = None

    return ParameterValue(
        domain_id=domain_id,
        param_id=param_id,
        value=value,
        unit=str(data.get("unit", "")),
        justification=str(data.get("justification", "")),
        uncertainty_range=uncertainty,
        key_assumption=str(data.get("key_assumption", "")),
        raw_text=raw_text[:200],
    )
