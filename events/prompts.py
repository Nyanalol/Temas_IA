from datetime import date
from langchain_core.prompts import ChatPromptTemplate


def get_extract_prompt(format_instructions: str) -> ChatPromptTemplate:
    today = date.today().isoformat()

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are a calendar assistant. "
                    "The user will describe an event in natural language (possibly in Spanish). "
                    "Extract all relevant event fields and return only a valid JSON object. "
                    "Do not add explanations, markdown, or any text outside the JSON.\n\n"
                    f"Today's date is {today}. "
                    "Use it to resolve relative dates like 'mañana', 'el martes', 'la próxima semana'.\n\n"
                    "Rules:\n"
                    "- If end time is not specified, set it to 1 hour after start.\n"
                    "- If the user mentions reminders or recordatorios, extract them as alarms.\n"
                    "- For recurring events, map the user's description to DAILY, WEEKLY, MONTHLY or YEARLY.\n"
                    "- Only set all_day to true if the user explicitly says it is an all-day event.\n"
                    "- Leave optional fields as null if the user did not mention them."
                ),
            ),
            (
                "human",
                (
                    "Create a calendar event based on this message:\n\n"
                    "{user_message}\n\n"
                    "Return only a valid JSON object following these instructions:\n"
                    "{format_instructions}"
                ),
            ),
        ]
    ).partial(format_instructions=format_instructions)
