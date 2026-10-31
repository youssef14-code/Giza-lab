import logging
from dataclasses import dataclass
from typing import Optional
from models.models import ResultRequest, Status, db

logger = logging.getLogger(__name__)

@dataclass
class ResultSaveResult:
    success: bool
    result_request: Optional[ResultRequest] = None
    message: str = ""

class ResultService:
    def __init__(self, request_id=None):
        self.request_id = request_id

    def save_result_request(self, phone_number: str, branch_name: str, patient_name: str = None, comes_from: str = "unknown") -> ResultSaveResult:
        """حفظ طلب نتيجة جديد قادم من البوت."""
        try:
            req = ResultRequest(
                phone_number=phone_number.strip(),
                branch_name=branch_name.strip(),
                patient_name=patient_name.strip() if patient_name else None,
                comes_from=comes_from or "unknown",
                status=Status.PENDING
            )
            db.session.add(req)
            db.session.commit()
            return ResultSaveResult(success=True, result_request=req, message="تم تسجيل طلب النتيجة بنجاح")
        except Exception as e:
            db.session.rollback()
            logger.exception("Failed to save result request: %s", e)
            return ResultSaveResult(success=False, message="حدث خطأ أثناء حفظ الطلب")

    def get_all_results(self, page=1, per_page=10, search=None, status=None):
        """جلب كل طلبات النتائج مع Pagination وبحث."""
        query = ResultRequest.query
        if search:
            query = query.filter(
                db.or_(
                    ResultRequest.phone_number.ilike(f'%{search}%'),
                    ResultRequest.branch_name.ilike(f'%{search}%'),
                    ResultRequest.patient_name.ilike(f'%{search}%')
                )
            )
        if status:
            try:
                query = query.filter(ResultRequest.status == Status(status))
            except ValueError:
                pass

        query = query.order_by(ResultRequest.created_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False), "تم العثور على النتائج"

    def update_status(self, request_id: int, new_status: Status):
        """تحديث حالة الطلب (مثلاً: تم إرسال النتيجة)."""
        req = db.session.get(ResultRequest, request_id)
        if not req:
            return False, "الطلب غير موجود"
        try:
            req.status = new_status
            db.session.commit()
            return True, "تم تحديث حالة الطلب بنجاح"
        except Exception as e:
            db.session.rollback()
            logger.exception("Error updating result request status: %s", e)
            return False, "حدث خطأ أثناء تحديث الحالة"