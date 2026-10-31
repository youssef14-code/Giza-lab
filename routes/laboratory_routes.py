from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from services.domain.laboratory_service import LaboratoryService
from models.models import Branch, db

laboratory_bp = Blueprint('laboratory', __name__, url_prefix='/laboratories')

@laboratory_bp.route('/')
@login_required
def list_laboratories():
    lab_service = LaboratoryService()
    laboratories, _ = lab_service.get_all_laboratories()
    # جلب جميع الفروع مباشرة من جدول branches
    branches = Branch.query.order_by(Branch.id.asc()).all()
    return render_template('laboratory/list.html', laboratories=laboratories or [], branches=branches)

@laboratory_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_laboratory():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()

        lab_service = LaboratoryService()
        lab, msg = lab_service.create_laboratory(name, location, description)
        
        if lab:
            flash(msg, 'success')
            return redirect(url_for('laboratory.list_laboratories'))
        
        flash(msg, 'error') 

    return render_template('laboratory/create.html')

@laboratory_bp.route('/<int:lab_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_laboratory(lab_id):
    lab_service = LaboratoryService(lab_id=lab_id)
    lab, msg = lab_service.get_laboratory()
    if not lab:
        flash(msg, 'error')
        return redirect(url_for('laboratory.list_laboratories'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()

        updated_lab, update_msg = lab_service.update_laboratory(name=name, location=location, description=description)
        if updated_lab:
            flash(update_msg, 'success')
            return redirect(url_for('laboratory.list_laboratories'))
        
        flash(update_msg, 'error')

    return render_template('laboratory/edit.html', laboratory=lab)


# إضافة فرع جديد
@laboratory_bp.route('/branches/create', methods=['GET', 'POST'])
@login_required
def create_branch():
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        phone_number = request.form.get('phone_number')
        working_hours = request.form.get('working_hours')
        lab_service = LaboratoryService()
        branch, msg = lab_service.create_branch(name, address, phone_number, working_hours)
        if branch:
            flash(msg, 'success')
            return redirect(url_for('laboratory.list_laboratories'))
        flash(msg, 'error')
    return render_template('laboratory/branch_form.html', branch=None, is_edit=False)
# تعديل فرع
@laboratory_bp.route('/branches/<int:branch_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_branch(branch_id):
    branch = db.session.get(Branch, branch_id)
    if not branch:
        flash("الفرع غير موجود", "error")
        return redirect(url_for('laboratory.list_laboratories'))
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        phone_number = request.form.get('phone_number')
        working_hours = request.form.get('working_hours')
        lab_service = LaboratoryService()
        updated, msg = lab_service.update_branch(branch_id, name, address, phone_number, working_hours)
        if updated:
            flash(msg, 'success')
            return redirect(url_for('laboratory.list_laboratories'))
        flash(msg, 'error')
    return render_template('laboratory/branch_form.html', branch=branch, is_edit=True)
# حذف فرع
@laboratory_bp.route('/branches/<int:branch_id>/delete', methods=['POST'])
@login_required
def delete_branch(branch_id):
    lab_service = LaboratoryService()
    success, msg = lab_service.delete_branch(branch_id)
    flash(msg, 'success' if success else 'error')
    return redirect(url_for('laboratory.list_laboratories'))    