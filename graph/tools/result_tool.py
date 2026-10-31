import logging
from dataclasses import dataclass
from typing import Optional
from langchain_core.tools import tool
from services.domain.result_service import ResultService

logger = logging.getLogger(__name__)


@dataclass
class SaveResultOutput:
    success: bool
    message: Optional[str] = None


@tool
def save_result_tool(
    phone_number: str,
    branch_name: str,
    patient_name: Optional[str] = None,
    comes_from: str = "unknown",
) -> SaveResultOutput:
    """
    Saves a laboratory test result inquiry request into the database once both
    the patient's registered phone number and the branch name are provided.

    Args:
        phone_number: Contact or registration phone number of the patient.
        branch_name: Name of the lab branch where the test was performed.
        patient_name: Name of the patient (optional).
        comes_from: Originating platform/channel (e.g., WhatsApp, Facebook).
    """
    try:
        service = ResultService()
        result = service.save_result_request(
            phone_number=phone_number,
            branch_name=branch_name,
            patient_name=patient_name,
            comes_from=comes_from,
        )

        if result.success:
            logger.info("[RESULT TOOL] Result request saved successfully for phone: %s", phone_number)
            return SaveResultOutput(success=True, message=result.message)

        logger.error("[RESULT TOOL] Failed to save result request: %s", result.message)
        return SaveResultOutput(success=False, message=result.message)

    except Exception:
        logger.exception("[RESULT TOOL] Unexpected error while saving result request")
        return SaveResultOutput(
            success=False,
            message="An unexpected error occurred while saving the result request.",
        )