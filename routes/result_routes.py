from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required
from models.models import Status
from services.domain.result_service import ResultService

results_bp = Blueprint('results', __name__, url_prefix='/results')

@results_bp.route('/')
@login_required
def list_results():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '')

    service = ResultService()
    pagination, _ = service.get_all_results(page=page, search=search, status=status)
    return render_template('results/list.html', pagination=pagination, results=pagination.items,
                           search=search, status=status, Status=Status)

@results_bp.route('/<int:request_id>/status', methods=['POST'])
@login_required
def update_status(request_id):
    new_status_str = request.form.get('status_val')
    try:
        new_status = Status(new_status_str)
    except ValueError:
        flash("حالة غير صحيحة", "danger")
        return redirect(url_for('results.list_results'))

    service = ResultService()
    success, msg = service.update_status(request_id, new_status)
    flash(msg, "success" if success else "danger")
    return redirect(request.referrer or url_for('results.list_results'))