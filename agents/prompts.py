from langchain_core.prompts import ChatPromptTemplate


def get_extract_prompt(format_instructions: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are a data incident extraction assistant. "
                    "Read a user message about a failed data pipeline and return only a valid JSON object. "
                    "Do not add explanations. "
                    "Do not add markdown. "
                    "Do not add text before the JSON. "
                    "Do not add text after the JSON."
                ),
            ),
            (
                "human",
                (
                    "Extract structured incident information from this message:\n\n"
                    "{user_message}\n\n"
                    "Return only a valid JSON object following these instructions:\n"
                    "{format_instructions}"
                ),
            ),
        ]
    ).partial(format_instructions=format_instructions)


def get_response_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are a data platform support assistant. "
                    "Create an operational response for a data incident. "
                    "Return only a valid JSON object. "
                    "Do not add explanations. "
                    "Do not add markdown. "
                    "Do not add text before the JSON. "
                    "Do not add text after the JSON."
                ),
            ),
            (
                "human",
                (
                    "Using this structured incident context:\n\n"
                    "{incident_context}\n\n"
                    "Generate a short operational response for an internal data team.\n\n"
                    "Return only a valid JSON object following these instructions:\n"
                    "{format_instructions}"
                ),
            ),
        ]
    )