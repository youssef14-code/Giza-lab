import logging

from sqlalchemy.exc import IntegrityError

from models.models import Lab, db
from models.models import Branch

logger = logging.getLogger(__name__)

class LaboratoryService:
    def __init__(self, lab_id=None, lab=None):
        """Wrap a single laboratory, given its ID or a pre-loaded instance."""
        self.lab_id = lab_id
        self._lab = lab

    @property
    def lab(self):
        """The laboratory, lazily loaded by ID on first access."""
        if self._lab is None and self.lab_id is not None:
            self._lab = db.session.get(Lab, self.lab_id)
        return self._lab

    def create_laboratory(self, name, location, description):
        """
        Create a laboratory.

        Name and location are stripped and required; names must be unique.
        Returns (lab, message); lab is None on failure.
        """
        try:
            name = (name or "").strip()
            location = (location or "").strip()

            if not name:
                return None, "اسم المعمل مطلوب"
            if not location:
                return None, "مكان المعمل مطلوب"

            existing_lab = Lab.query.filter_by(name=name).first()
            if existing_lab:
                return None, "Laboratory already exists"

            new_lab = Lab(name=name, location=location, description=description)
            db.session.add(new_lab)
            db.session.commit()
            self._lab = new_lab
            self.lab_id = new_lab.id
            return new_lab, "Laboratory created successfully"
        except IntegrityError:
            db.session.rollback()
            return None, "Laboratory already exists"
        except Exception:
            db.session.rollback()
            logger.exception("Failed to create laboratory")
            return None, "An unexpected error occurred while creating the laboratory"

    def get_laboratory(self, lab_id=None):
        """
        Get a laboratory by ID, using this instance's ID and cache as defaults.

        Returns (lab, message); lab is None if not found or on error.
        """
        target_id = lab_id or self.lab_id
        if not target_id and self._lab:
            return self._lab, "Laboratory retrieved successfully"
        if not target_id:
            return None, "Laboratory not found"

        if self._lab and self._lab.id == target_id:
            return self._lab, "Laboratory retrieved successfully"

        try:
            lab = db.session.get(Lab, target_id)
            if lab:
                if target_id == self.lab_id or self.lab_id is None:
                    self._lab = lab
                    self.lab_id = lab.id
                return lab, "Laboratory retrieved successfully"
            else:
                return None, "Laboratory not found"
        except Exception:
            logger.exception("Failed to retrieve laboratory %s", target_id)
            return None, "An unexpected error occurred while retrieving the laboratory"

    def get_all_laboratories(self):
        """List all laboratories. Returns (labs, message); labs is None on error."""
        try:
            labs = Lab.query.all()
            return labs, "All laboratories retrieved successfully"
        except Exception:
            logger.exception("Failed to retrieve laboratories")
            return None, "An unexpected error occurred while retrieving laboratories"

    def update_laboratory(self, name=None, location=None, description=None, lab_id=None):
        """
        Update a laboratory's name, location or description.

        Empty values are ignored, so a field cannot be cleared through this method.
        Renaming to a name used by another laboratory is rejected.
        Returns (lab, message); lab is None on failure.
        """
        try:
            target_id = lab_id or self.lab_id
            lab = None
            if self._lab and (not target_id or self._lab.id == target_id):
                lab = self._lab
            elif target_id:
                lab = db.session.get(Lab, target_id)

            if not lab:
                return None, "Laboratory not found"

            new_name = name.strip() if name else None
            if new_name and new_name != lab.name:
                duplicate = Lab.query.filter(
                    Lab.name == new_name, Lab.id != lab.id
                ).first()
                if duplicate:
                    return None, "Laboratory already exists"
                lab.name = new_name
            if location:
                lab.location = location
            if description:
                lab.description = description

            db.session.commit()
            self._lab = lab
            self.lab_id = lab.id
            return lab, "Laboratory updated successfully"
        except IntegrityError:
            db.session.rollback()
            return None, "Laboratory already exists"
        except Exception:
            db.session.rollback()
            logger.exception("Failed to update laboratory")
            return None, "An unexpected error occurred while updating the laboratory"

    def get_current_laboratory_id(self):
        """
        Return the current laboratory ID.

        The system is single-tenant, so when no ID is set on this instance,
        the first laboratory created is treated as the current one.
        """
        if self.lab_id is not None:
            return self.lab_id
        lab = Lab.query.order_by(Lab.id.asc()).first()
        if lab:
            self.lab_id = lab.id
            self._lab = lab
            return lab.id
        return None

    @staticmethod
    def get_first_laboratory():
        """Return the first laboratory created, or None."""
        try:
            return Lab.query.order_by(Lab.id.asc()).first()
        except Exception:
            logger.exception("Failed to fetch the first laboratory")
            return None

    @staticmethod
    def get_laboratories_ordered_by_name():
        """Return all laboratories sorted by name (empty list on error)."""
        try:
            return Lab.query.order_by(Lab.name.asc()).all()
        except Exception:
            logger.exception("Failed to fetch laboratories ordered by name")
            return []



    @staticmethod
    def get_current_lab_info():
        """
        Fetches primary laboratory name, location, and description for system prompts.
        """
        try:
            lab = Lab.query.order_by(Lab.id.asc()).first()
            if not lab:
                return (
                    "معمل جيزة لاب  للتحاليل الطبية",
                    "الإسكندرية",
                    "معمل متخصص في جميع التحاليل الطبية والكيميائية"
                )
            
            return (
                lab.name,
                (lab.location or "غير محدد"),
                (lab.description or "معمل متخصص في التحاليل الطبية")
            )
        except Exception:
            logger.exception("[LaboratoryService.get_current_lab_info] failed")
            return (
                "معمل جيزة لاب للتحاليل الطبية",
                "الإسكندرية",
                "معمل متخصص في التحاليل الطبية"
            )    


    # داخل كلاس LaboratoryService أضف هذه الدوال:
    def get_branches(self):
        lab_id = self.get_current_laboratory_id()
        if not lab_id:
            # Fallback لو الـ lab_id كان فاضي يجيب كل الفروع
            return Branch.query.order_by(Branch.id.asc()).all()
        return Branch.query.filter_by(laboratory_id=lab_id).order_by(Branch.id.asc()).all()
    def create_branch(self, name, address, phone_number, working_hours):
        lab_id = self.get_current_laboratory_id()
        if not lab_id:
            return None, "لم يتم العثور على المعمل الرئيسي"
        try:
            branch = Branch(
                laboratory_id=lab_id,
                name=name.strip(),
                address=address.strip(),
                phone_number=(phone_number or "").strip(),
                working_hours=(working_hours or "").strip()
            )
            db.session.add(branch)
            db.session.commit()
            return branch, "تم إضافة الفرع بنجاح"
        except Exception as e:
            db.session.rollback()
            return None, f"خطأ أثناء إضافة الفرع: {e}"
    def update_branch(self, branch_id, name, address, phone_number, working_hours):
        branch = db.session.get(Branch, branch_id)
        if not branch:
            return None, "الفرع غير موجود"
        try:
            branch.name = name.strip()
            branch.address = address.strip()
            branch.phone_number = (phone_number or "").strip()
            branch.working_hours = (working_hours or "").strip()
            db.session.commit()
            return branch, "تم تعديل الفرع بنجاح"
        except Exception as e:
            db.session.rollback()
            return None, f"خطأ أثناء تعديل الفرع: {e}"
    def delete_branch(self, branch_id):
        branch = db.session.get(Branch, branch_id)
        if not branch:
            return False, "الفرع غير موجود"
        try:
            db.session.delete(branch)
            db.session.commit()
            return True, "تم حذف الفرع بنجاح"
        except Exception as e:
            db.session.rollback()
            return False, f"خطأ أثناء حذف الفرع: {e}"