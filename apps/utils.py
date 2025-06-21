import json
import logging
from datetime import datetime
from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import load_dotenv
import os


load_dotenv()

def send_webhook(event_type, payload, webhook_url):
    """
    Sends a webhook to the specified Discord webhook URL using discord-webhook library.

    Args:
        event_type (str): A string indicating the type of event (e.g. "user_signup", "api_call").
        payload (dict): Dictionary of data to send in the webhook.
        webhook_url (str): Discord webhook URL to send the message to.

    Returns:
        dict: Contains 'success' (bool) and 'message' (str).
    """

    try:
        # Check if webhook URL is a placeholder
        if webhook_url.startswith("PLACEHOLDER_"):
            logging.warning(f"Webhook URL is a placeholder: {webhook_url}")
            return {"success": False, "message": f"Webhook URL not configured: {webhook_url}"}

        # Create webhook instance
        webhook = DiscordWebhook(
            url=webhook_url,
            username="Sisimpur Bot",
            rate_limit_retry=True
        )

        # Create embed with better formatting
        embed = DiscordEmbed(
            title=f"📡 {event_type.replace('_', ' ').title()}",
            color="03b2f8"  # Blue color
        )

        # Add timestamp
        embed.set_timestamp()

        # Add footer
        embed.set_footer(text="Sisimpur Platform", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")

        # Format payload data into fields
        if isinstance(payload, dict):
            for key, value in payload.items():
                # Format the key to be more readable
                field_name = key.replace('_', ' ').title()

                # Handle different value types
                if isinstance(value, (dict, list)):
                    field_value = f"```json\n{json.dumps(value, indent=2, default=str)}\n```"
                elif isinstance(value, datetime):
                    field_value = value.strftime("%Y-%m-%d %H:%M:%S UTC")
                else:
                    field_value = str(value)

                # Limit field value length (Discord limit is 1024 characters)
                if len(field_value) > 1000:
                    field_value = field_value[:997] + "..."

                embed.add_embed_field(
                    name=field_name,
                    value=field_value,
                    inline=True
                )
        else:
            # If payload is not a dict, add it as description
            embed.description = f"```json\n{json.dumps(payload, indent=2, default=str)}\n```"

        # Add embed to webhook
        webhook.add_embed(embed)

        # Execute webhook
        response = webhook.execute()

        if response.status_code in [200, 204]:
            return {"success": True, "message": "Discord webhook sent successfully."}
        else:
            logging.error(f"Discord webhook failed with status {response.status_code}: {response.text}")
            return {"success": False, "message": f"Failed to send Discord webhook: {response.status_code}"}

    except Exception as e:
        logging.exception("Exception while sending Discord webhook:")
        return {"success": False, "message": f"Discord webhook error: {str(e)}"}


def send_user_signup_webhook(user, webhook_url=os.getenv("SIGNUP_WEBHOOK_URL")):
    """
    Send a specialized webhook for user signups with enhanced formatting.

    Args:
        user: Django User instance
        webhook_url: Discord webhook URL (default: placeholder)

    Returns:
        dict: Contains 'success' (bool) and 'message' (str).
    """
    payload = {
        "user_id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.get_full_name(),
        "date_joined": user.date_joined,
        "is_active": user.is_active,
    }

    return send_webhook("user_signup", payload, webhook_url)


def send_user_login_webhook(user, login_method="email", webhook_url=os.getenv("SIGNIN_WEBHOOK_URL")):
    """
    Send a specialized webhook for user logins.

    Args:
        user: Django User instance
        login_method: Method used for login (email, google, etc.)
        webhook_url: Discord webhook URL (default: placeholder)

    Returns:
        dict: Contains 'success' (bool) and 'message' (str).
    """
    payload = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "login_method": login_method,
        "last_login": user.last_login,
        "login_time": datetime.now(),
    }

    return send_webhook("user_login", payload, webhook_url)


def send_quiz_generation_webhook(user, job, questions_count):
    """
    Send a webhook for quiz generation events.

    Args:
        user: Django User instance
        job: ProcessingJob instance
        questions_count: Number of questions generated

    Returns:
        dict: Contains 'success' (bool) and 'message' (str).
    """
    payload = {
        "user_id": user.id,
        "username": user.username,
        "job_id": job.id,
        "document_name": job.document_name,
        "language": job.language,
        "question_type": job.question_type,
        "questions_generated": questions_count,
        "processing_time": (job.completed_at - job.created_at).total_seconds() if job.completed_at else None,
    }

    return send_webhook("quiz_generated", payload)


def send_exam_completion_webhook(user, exam_session, webhook_url=os.getenv("EXAM_WEBHOOK_URL")):
    """
    Send a webhook for exam completion events.

    Args:
        user: Django User instance
        exam_session: ExamSession instance
        webhook_url: Discord webhook URL (default: placeholder)

    Returns:
        dict: Contains 'success' (bool) and 'message' (str).
    """
    payload = {
        "user_id": user.id,
        "username": user.username,
        "exam_session_id": exam_session.session_id,
        "quiz_name": exam_session.processing_job.document_name,
        "total_questions": exam_session.total_questions,
        "score": exam_session.total_score,
        "percentage": exam_session.percentage_score,
        "time_taken": (exam_session.completed_at - exam_session.started_at).total_seconds() if exam_session.completed_at else None,
        "attempt_number": exam_session.attempt_number,
    }

    return send_webhook("exam_completed", payload, webhook_url)


def send_document_processing_success_webhook(user, job, questions_count, qa_data=None, webhook_url=os.getenv("DOC_PROCESS_WEBHOOK_URL")):
    """
    Send a webhook for successful document processing.

    Args:
        user: Django User instance
        job: ProcessingJob instance
        questions_count: Number of questions generated
        qa_data: Generated questions JSON data (optional)
        webhook_url: Discord webhook URL (default: placeholder)

    Returns:
        dict: Contains 'success' (bool) and 'message' (str).
    """
    # If no questions generated, treat as failure
    if questions_count == 0:
        return send_document_processing_failed_webhook(
            user, job, "No questions were generated from the document", qa_data, webhook_url
        )

    try:
        # Check if webhook URL is a placeholder
        if webhook_url.startswith("PLACEHOLDER_"):
            logging.warning(f"Webhook URL is a placeholder: {webhook_url}")
            return {"success": False, "message": f"Webhook URL not configured: {webhook_url}"}

        # Create webhook instance
        webhook = DiscordWebhook(
            url=webhook_url,
            username="Sisimpur Bot",
            rate_limit_retry=True
        )

        # Create embed with success formatting
        embed = DiscordEmbed(
            title="📡 Document Processing Success",
            color="00ff00"  # Green color for success
        )

        # Add timestamp
        embed.set_timestamp()

        # Add footer
        embed.set_footer(text="Sisimpur Platform", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")

        # Add user and job information
        embed.add_embed_field(name="User Id", value=str(user.id), inline=True)
        embed.add_embed_field(name="Username", value=user.username, inline=True)
        embed.add_embed_field(name="Email", value=user.email, inline=True)
        embed.add_embed_field(name="Job Id", value=str(job.id), inline=True)
        embed.add_embed_field(name="Document Name", value=job.document_name, inline=True)
        embed.add_embed_field(name="Language", value=job.language, inline=True)
        embed.add_embed_field(name="Question Type", value=job.question_type, inline=True)
        embed.add_embed_field(name="Questions Generated", value=str(questions_count), inline=True)

        processing_time = (job.completed_at - job.created_at).total_seconds() if job.completed_at else None
        embed.add_embed_field(name="Processing Time", value=f"{processing_time:.6f}s" if processing_time else "N/A", inline=True)
        embed.add_embed_field(name="Document Type", value=job.document_type or "unknown", inline=True)
        embed.add_embed_field(name="Is Question Paper", value=str(job.is_question_paper), inline=True)

        # Add embed to webhook
        webhook.add_embed(embed)

        # Add JSON output as file if available
        if qa_data:
            json_content = json.dumps(qa_data, indent=2, ensure_ascii=False)
            webhook.add_file(file=json_content.encode('utf-8'), filename=f"questions_job_{job.id}.json")

        # Add uploaded document as file if available
        if job.document_file:
            try:
                from django.core.files.storage import default_storage
                if default_storage.exists(job.document_file.name):
                    with default_storage.open(job.document_file.name, 'rb') as f:
                        file_content = f.read()
                        webhook.add_file(file=file_content, filename=job.document_name)
            except Exception as file_error:
                logging.warning(f"Could not attach document file: {file_error}")

        # Execute webhook
        response = webhook.execute()

        if response.status_code in [200, 204]:
            return {"success": True, "message": "Discord webhook sent successfully."}
        else:
            logging.error(f"Discord webhook failed with status {response.status_code}: {response.text}")
            return {"success": False, "message": f"Failed to send Discord webhook: {response.status_code}"}

    except Exception as e:
        logging.exception("Exception while sending Discord webhook:")
        return {"success": False, "message": f"Discord webhook error: {str(e)}"}


def send_document_processing_failed_webhook(user, job, error_message, qa_data=None, webhook_url=os.getenv("DOC_PROCESS_WEBHOOK_URL")):
    """
    Send a webhook for failed document processing.

    Args:
        user: Django User instance
        job: ProcessingJob instance
        error_message: Error message string
        qa_data: Generated questions JSON data (optional, for partial failures)
        webhook_url: Discord webhook URL (default: placeholder)

    Returns:
        dict: Contains 'success' (bool) and 'message' (str).
    """
    try:
        # Check if webhook URL is a placeholder
        if webhook_url.startswith("PLACEHOLDER_"):
            logging.warning(f"Webhook URL is a placeholder: {webhook_url}")
            return {"success": False, "message": f"Webhook URL not configured: {webhook_url}"}

        # Create webhook instance
        webhook = DiscordWebhook(
            url=webhook_url,
            username="Sisimpur Bot",
            rate_limit_retry=True
        )

        # Create embed with failure formatting
        embed = DiscordEmbed(
            title="📡 Document Processing Failed",
            color="ff0000"  # Red color for failure
        )

        # Add timestamp
        embed.set_timestamp()

        # Add footer
        embed.set_footer(text="Sisimpur Platform", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")

        # Add user and job information
        embed.add_embed_field(name="User Id", value=str(user.id), inline=True)
        embed.add_embed_field(name="Username", value=user.username, inline=True)
        embed.add_embed_field(name="Email", value=user.email, inline=True)
        embed.add_embed_field(name="Job Id", value=str(job.id), inline=True)
        embed.add_embed_field(name="Document Name", value=job.document_name, inline=True)
        embed.add_embed_field(name="Language", value=job.language, inline=True)
        embed.add_embed_field(name="Question Type", value=job.question_type, inline=True)

        # Show 0 questions generated for failures
        questions_count = len(qa_data.get('questions', [])) if qa_data else 0
        embed.add_embed_field(name="Questions Generated", value=str(questions_count), inline=True)

        processing_time = (job.completed_at - job.created_at).total_seconds() if job.completed_at else None
        embed.add_embed_field(name="Processing Time", value=f"{processing_time:.6f}s" if processing_time else "N/A", inline=True)
        embed.add_embed_field(name="Document Type", value=job.document_type or "unknown", inline=True)
        embed.add_embed_field(name="Is Question Paper", value=str(job.is_question_paper), inline=True)

        # Add error message
        embed.add_embed_field(name="Error Message", value=error_message[:1024], inline=False)

        # Add embed to webhook
        webhook.add_embed(embed)

        # Add JSON output as file if available (even for failures, might have partial data)
        if qa_data:
            json_content = json.dumps(qa_data, indent=2, ensure_ascii=False)
            webhook.add_file(file=json_content.encode('utf-8'), filename=f"failed_questions_job_{job.id}.json")

        # Add uploaded document as file if available
        if job.document_file:
            try:
                from django.core.files.storage import default_storage
                if default_storage.exists(job.document_file.name):
                    with default_storage.open(job.document_file.name, 'rb') as f:
                        file_content = f.read()
                        webhook.add_file(file=file_content, filename=job.document_name)
            except Exception as file_error:
                logging.warning(f"Could not attach document file: {file_error}")

        # Execute webhook
        response = webhook.execute()

        if response.status_code in [200, 204]:
            return {"success": True, "message": "Discord webhook sent successfully."}
        else:
            logging.error(f"Discord webhook failed with status {response.status_code}: {response.text}")
            return {"success": False, "message": f"Failed to send Discord webhook: {response.status_code}"}

    except Exception as e:
        logging.exception("Exception while sending Discord webhook:")
        return {"success": False, "message": f"Discord webhook error: {str(e)}"}


def send_normal_signin_webhook(user, webhook_url=os.getenv("SIGNIN_WEBHOOK_URL")):
    """
    Send a webhook for normal email/password sign in.

    Args:
        user: Django User instance
        webhook_url: Discord webhook URL (default: placeholder)

    Returns:
        dict: Contains 'success' (bool) and 'message' (str).
    """
    payload = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.get_full_name(),
        "last_login": user.last_login,
        "login_method": "email_password",
        "login_time": datetime.now(),
    }

    return send_webhook("normal_signin", payload, webhook_url)


def send_google_signin_webhook(user, webhook_url=os.getenv("SIGNIN_WEBHOOK_URL")):
    """
    Send a webhook for Google OAuth sign in.

    Args:
        user: Django User instance
        webhook_url: Discord webhook URL (default: placeholder)

    Returns:
        dict: Contains 'success' (bool) and 'message' (str).
    """
    payload = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.get_full_name(),
        "last_login": user.last_login,
        "login_method": "google_oauth",
        "login_time": datetime.now(),
    }

    return send_webhook("google_signin", payload, webhook_url)