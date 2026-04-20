"""
Entry point for the incident analysis chain.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents.chain_factory import build_incident_chain
from agents.runnables import print_title




USER_MESSAGE = (
    "The daily sales pipeline failed at 06:10. "
    "The silver job for customer_orders crashed because the source file "
    "arrived without customer_id. "
    "This is high priority because the finance dashboard was not refreshed."
)


def main():
    chain, extraction_parser = build_incident_chain()

    inputs = {
        "user_message": USER_MESSAGE,
        "format_instructions": extraction_parser.get_format_instructions(),
    }

    print_title("INPUT_ORIGINAL")
    print(USER_MESSAGE)


    result = chain.invoke(inputs)

    print_title("FINAL_RESULT")
    print(result)

    print_title("FINAL_FIELDS")
    print("incident_summary:", result.incident_summary)
    print("business_impact:", result.business_impact)
    print("next_action:", result.next_action)
    print("owner_team:", result.owner_team)


if __name__ == "__main__":
    main()