import os
import logging
import json
from datetime import datetime
import google.generativeai as genai

try:
    TEXT_MODEL = genai.GenerativeModel(model_name='gemini-2.5-flash-lite')
except Exception as e:
    logging.error(f"Could not initialize Gemini text model for Agent: {e}")
    TEXT_MODEL = None

LOGS_DIR = "logs"
ALERTS_DIR = "alerts"

def _generate_and_save_alert(brief, expected_count, actual_count):
    """
    Uses the Gemini AI to translate campaign failure data into a human-readable
    email and saves it locally.
    """
    if not TEXT_MODEL:
        logging.error("Cannot generate AI alert because the text model failed to initialize.")
        return

    logging.warning("Issue detected. Triggering AI Alerter...")
    os.makedirs(ALERTS_DIR, exist_ok=True)

    context = {
        "campaign_name": brief.campaign_name,
        "status": "FLAGGED_INSUFFICIENT_ASSETS",
        "severity": "Warning",
        "details": {
            "expected_variant_count": expected_count,
            "generated_variant_count": actual_count,
            "message": brief.message,
            "products": list(brief.products.keys())
        },
        "suggested_action": f"Review the campaign log at '{LOGS_DIR}/{brief.campaign_name.replace(' ', '_')}.log' for potential errors."
    }

    prompt = (
        "You are a production assistant AI for a busy marketing team. "
        "Based on the following structured JSON data report, write a simple, clear, and human-readable email alert. "
        "The email should be suitable for saving as a text file. Do not include the JSON in your response. "
        "Start the email with a clear subject line.\n\n"
        f"JSON REPORT:\n{json.dumps(context, indent=2)}"
    )

    try:
        response = TEXT_MODEL.generate_content(prompt)
        email_content = response.text
        safe_campaign_name = brief.campaign_name.replace(' ', '_')
        alert_filepath = os.path.join(ALERTS_DIR, f"ALERT_{safe_campaign_name}.txt")
        with open(alert_filepath, 'w') as f:
            f.write(email_content)
        
        logging.info(f"Successfully generated and saved alert to: {alert_filepath}")

    except Exception as e:
        logging.error(f"Failed to generate AI alert: {e}")


def run_post_process_checks(brief, generated_urls: list):
    """
    The main function for the agent. It logs campaign results and triggers
    alerts if there's a problem.
    """
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # Calculate expected vs. actual creative counts
    expected_count = len(brief.products) * 3  # 3 aspect ratios per product
    actual_count = len(generated_urls)
    
    # Create a safe filename for the log
    safe_campaign_name = brief.campaign_name.replace(' ', '_')
    log_filepath = os.path.join(LOGS_DIR, f"{safe_campaign_name}.log")

    # Prepare the log content
    log_content = (
        f"Campaign Generation Log\n"
        f"-------------------------\n"
        f"Campaign Name: {brief.campaign_name}\n"
        f"Timestamp (UTC): {datetime.utcnow().isoformat()}\n"
        f"Status: {'SUCCESS' if actual_count >= expected_count else 'FLAGGED INSUFFICIENT ASSETS'}\n\n"
        f"Metrics:\n"
        f"  - Expected Creatives: {expected_count}\n"
        f"  - Generated Creatives: {actual_count}\n\n"
        f"Brief Details:\n{json.dumps(brief.dict(), indent=2)}\n\n"
        f"Generated File URLs:\n"
    )
    for url in generated_urls:
        log_content += f"  - {url}\n"

    # Write the log file
    with open(log_filepath, 'w') as f:
        f.write(log_content)
    
    logging.info(f"Campaign results logged to: {log_filepath}")

    # If there's a mismatch, trigger the AI alerter
    if actual_count < expected_count:
        _generate_and_save_alert(brief, expected_count, actual_count)