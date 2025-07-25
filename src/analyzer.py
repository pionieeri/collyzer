import yaml
from sqlalchemy.orm import Session
from .database import LogEntry

def run_analysis(session: Session):
    """Loads rules from a YAML file and runs them against the database."""
    print("\n### Starting Log Analysis ###")
    try:
        with open("analysis_rules.yml", "r") as f:
            rules = yaml.safe_load(f)
    except FileNotFoundError:
        print("  Error: analysis_rules.yml not found. Skipping analysis.")
        return
    except yaml.YAMLError as e:
        print(f"  Error parsing analysis_rules.yml: {e}")
        return

    if not rules:
        print("  No analysis rules loaded. Skipping.")
        return

    print(f"  Loaded {len(rules)} analysis rules.")

    for rule in rules:
        _execute_rule(session, rule)

    print("\n### Log Analysis Finished ###")

def _execute_rule(session: Session, rule: dict):
    """Executes a single analysis rule and prints alerts for any findings."""
    rule_name = rule.get("name", "Unnamed Rule")
    filters = rule.get("query_filters")

    if not filters:
        print(f"  Skipping invalid rule: {rule_name}")
        return

    try:
        query = session.query(LogEntry).filter_by(**filters)
        
        results = query.all()
        
        if results:
            print(f"\nALERT [{rule_name}]: Found {len(results)} matching log entries!")
            for entry in results:
                print(f"  - Time: {entry.timestamp}, Host: {entry.hostname}, App: {entry.app}, User: {entry.user}, Action: {entry.action}")

    except Exception as e:
        print(f"  Error executing rule '{rule_name}': {e}")