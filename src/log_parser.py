import re
import json
import yaml
from datetime import datetime

class LogParser:
    """A multi-method log parser driven by a YAML configuration file."""

    def __init__(self, rules_path="parsing_rules.yml"):
        """
        Initializes the parser by loading and pre-compiling parsing rules.
        """
        try:
            with open(rules_path, "r") as f:
                self.rules = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"  Error: Parsing rules file not found at {rules_path}. Aborting.")
            raise
        except yaml.YAMLError as e:
            print(f"  Error parsing rules file: {e}. Aborting.")
            raise

        self._prepare_rules()

    def _prepare_rules(self):
        """
        Pre-compiles regex patterns and groups rules by log_source for efficiency.
        """
        prepared_rules = {}
        for rule in self.rules:
            if rule.get("parsing_method") == "regex":
                try:
                    rule["_compiled_regex"] = re.compile(rule["regex"])
                except re.error as e:
                    print(f"  Warning: Invalid regex for rule '{rule['name']}': {e}. Skipping.")
                    continue
            
            log_source = rule.get("log_source")
            if log_source not in prepared_rules:
                prepared_rules[log_source] = []
            prepared_rules[log_source].append(rule)
        
        self.rules = prepared_rules

    def _parse_generic_header(self, line: str):
        """
        Parses the common syslog header to extract timestamp and hostname.
        Returns a tuple of (datetime_obj, hostname, message).
        Returns (None, None, line) if no match is found.
        """
        header_pattern = re.compile(
            r"^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+([\w\-\.]+)\s+(.*)$"
        )
        match = header_pattern.match(line)
        if not match:
            return None, None, line

        timestamp_str, hostname, message = match.groups()
        
        try:
            # Handle year-rollover by checking if the parsed date is in the future
            current_year = datetime.now().year
            full_timestamp_str = f"{current_year} {timestamp_str}"
            dt_obj = datetime.strptime(full_timestamp_str, "%Y %b %d %H:%M:%S")
            if dt_obj > datetime.now():
                dt_obj = dt_obj.replace(year=dt_obj.year - 1)
        except ValueError:
            dt_obj = datetime.now() # Fallback to current time if parsing fails

        return dt_obj, hostname, message.strip()

    def parse(self, line: str, log_source: str):
        """
        Parses a single log line according to the rules for its log source.
        """
        source_rules = self.rules.get(log_source, [])

        # First, try JSON rules as they are self-contained and don't have a header
        for rule in source_rules:
            if rule["parsing_method"] == "json":
                parsed_data = self._apply_json_rule(line, rule)
                if parsed_data:
                    final_data = self._map_data(parsed_data, rule)
                    # JSON logs might have their own timestamp
                    if 'timestamp' not in final_data:
                        final_data['timestamp'] = datetime.now()
                    final_data["log_source"] = log_source
                    final_data["raw_message"] = line
                    return final_data

        # If no JSON rule matched, proceed with generic header parsing for syslog-like formats
        dt_obj, hostname, message = self._parse_generic_header(line)

        for rule in source_rules:
            if rule["parsing_method"] == "regex":
                parsed_data = self._apply_regex_rule(message, rule)
                if parsed_data:
                    final_data = self._map_data(parsed_data, rule)
                    final_data["timestamp"] = dt_obj or datetime.now()
                    final_data["hostname"] = hostname or "unknown"
                    final_data["log_source"] = log_source
                    final_data["raw_message"] = line
                    return final_data

        # Fallback if no rules match at all
        return {
            "timestamp": dt_obj or datetime.now(),
            "hostname": hostname or "unknown",
            "raw_message": line,
            "log_source": log_source,
            "action": "unparsed",
        }

    def _apply_regex_rule(self, message: str, rule: dict):
        """Applies a single regex rule's compiled pattern to the message."""
        match = rule["_compiled_regex"].search(message)
        return match.groupdict() if match else None

    def _apply_json_rule(self, line: str, rule: dict):
        """Attempts to parse the line as JSON."""
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            return None

    def _map_data(self, parsed_data: dict, rule: dict) -> dict:
        """Maps extracted data to CIM fields based on the rule's mapping."""
        final_data = rule.get("cim_mapping", {}).copy()
        for key, value in final_data.items():
            if isinstance(value, str):
                try:
                    final_data[key] = value.format(**parsed_data)
                except KeyError as e:
                    # A key in the format string was not found in the parsed data
                    print(f"  Warning: Mapping failed for rule '{rule['name']}'. Key {e} not found. Setting field to None.")
                    final_data[key] = None
        return final_data