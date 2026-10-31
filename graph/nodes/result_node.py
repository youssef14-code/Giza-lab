import logging
from langchain_core.messages import HumanMessage, SystemMessage

from graph.prompts.result_prompt import RESULT_SYSTEM_PROMPT
from graph.state import AgentState
from graph.tools.result_tool import save_result_tool
from llm.llm import get_gemini
from schemas.result import ResultResponse
from services.messaging.client_service import ClientService
from utils.history_utils import get_chat_history
from utils.llm_utils import extract_token_usage
from utils.text_utils import get_platform_name

logger = logging.getLogger(__name__)


def result_node(state: AgentState) -> dict:
    """
    Handle laboratory test result inquiries using Gemini Tool Calling.

    Flow:
        Get Conversation Context
        → Load Chat History
        → Build System Prompt
        → Gemini Tool Calling (save_result_tool / ResultResponse)
        → Return State
    """
    page_id = state.get("page_id")
    sender_id = state.get("sender_id")
    platform_id = state.get("platform_id")
    user_message = state.get("user_message", "")
    current_summary = state.get("summary") or ""
    last_bot_message = state.get("last_bot_message") or ""

    # Load conversation context
    client_service = ClientService(
        platform_id=platform_id,
        page_id=page_id,
        sender_id=sender_id,
    )
    history, recent_history = get_chat_history(state, client_service)

    # Build prompt
    system_prompt = f"""
{RESULT_SYSTEM_PROMPT}

====================
ALREADY COLLECTED
====================
Summary:
{current_summary or "(None)"}

Last Bot Message:
{last_bot_message or "(None)"}

====================
RECENT CONVERSATION
====================
{recent_history or "(None)"}
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    try:
        llm = get_gemini().bind_tools(
            [save_result_tool, ResultResponse],
            tool_choice="any",
        )
        response = llm.invoke(messages)

        tool_calls = getattr(response, "tool_calls", [])
        if tool_calls:
            for tc in tool_calls:
                name = tc.get("name")
                args = tc.get("args", {})

                if name == "save_result_tool":
                    args["comes_from"] = get_platform_name(platform_id)
                    save_res = save_result_tool.invoke(args)

                    reply = (
                        "تم تسجيل طلبك بنجاح للاستعلام عن النتيجة! 📋✨\n"
                        f"🏥 فرع: {args.get('branch_name')}\n"
                        f"📱 رقم الهاتف: {args.get('phone_number')}\n\n"
                        "فريق معمل جيزة لاب هيراجع النتيجة ويبعتها لحضرتك في أقرب وقت. نتمنى لحضرتك دوام الصحة والعافية! 🌸"
                    )
                    return {
                        "response": reply,
                        "summary": f"Result inquiry requested for branch {args.get('branch_name')} and phone {args.get('phone_number')}",
                        "last_bot_message": reply,
                    }

                elif name == "ResultResponse":
                    reply = args.get("reply", "")
                    return {
                        "response": reply,
                        "summary": args.get("summary", current_summary),
                        "last_bot_message": reply,
                    }

        # Fallback text reply if no tool was called
        reply = response.content or "من فضلك يا فندم شاركنا برقم التليفون المسجل واسم الفرع لمساعدتك في استلام النتيجة."
        return {
            "response": reply,
            "summary": current_summary,
            "last_bot_message": reply,
        }

    except Exception:
        logger.exception("[RESULT NODE] LLM Error | sender_id=%s", sender_id)
        fallback = (
            "عذراً، حدث خطأ مؤقت أثناء معالجة طلب النتيجة ⚠️\n"
            "يمكنك التواصل مباشرة مع خدمة عملاء معمل جيزة لاب على الرقم:\n"
            "📞 **01006446508**"
        )
        return {
            "response": fallback,
            "summary": current_summary,
            "last_bot_message": fallback,
        }