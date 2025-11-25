import logging
from strands import tool
from questions import QuestionManager

logger = logging.getLogger(__name__)

@tool
def log_unanswered_question(question: str, name: str, email: str) -> str:
    """
    Logs a question that could not be answered by the knowledge base, along
    with the user's name and email address for follow-up.

    Args:
        question: The user's original question that could not be answered.
        name: The user's name.
        email: The user's email address.
    
    Returns:
        A confirmation message indicating that the question has been logged.
    """
    logger.info(f"Logging unanswered question: '{question}' from {name} ({email})")
    try:
        question_manager = QuestionManager()
        question_manager.add_question(
            question=question,
            user_name=name,
            user_email=email
        )
        confirmation_message = f"Successfully logged question from {name}."
        logger.info(confirmation_message)
        return confirmation_message
    except Exception as e:
        error_message = f"Failed to log unanswered question. Error: {e}"
        logger.error(error_message, exc_info=True)
        return error_message
