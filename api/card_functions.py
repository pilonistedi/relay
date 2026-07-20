import os
from flask import jsonify, session, current_app, Blueprint
from db import db, TemporaryDrop, Group

# Define the isolated authorization blueprint node
card_functions_bp = Blueprint('card_functions_bp', __name__)

@card_functions_bp.route("/group/<int:group_id>/drop/<int:drop_id>/delete", methods=["POST"])
def delete_drop(group_id, drop_id):
    # 1. Enforce Authentication Guard
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized. Please log in first."}), 401

    # 2. Fetch the target drop or return 404
    drop = TemporaryDrop.query.filter_by(id=drop_id, group_id=group_id).first_or_404()

    # 3. Security Policy Authorization Check
    # A user can delete their own drop, OR the group creator can delete any drop in their group
    group = Group.query.get_or_404(group_id)
    is_owner = (drop.user_id == user_id)
    is_group_creator = (group.creator_id == user_id)

    if not (is_owner or is_group_creator):
        return jsonify({"error": "Forbidden. You do not have permission to delete this drop."}), 403

    # 4. Permanently Purge the Physical File from Local Storage
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], drop.stored_name)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            # Log the storage warning, but don't halt database cleanup if filesystem unlinking hits a snag
            print(f"Filesystem unlinking warning: {e}")

    # 5. Remove the Row Record from the Database
    try:
        db.session.delete(drop)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to drop database row reference: {str(e)}"}), 500

    # 6. Dispatch Success Code back to AJAX Front-end UI
    return jsonify({
        "success": True,
        "message": "Temporary drop deleted permanently.",
        "drop_id": drop_id
    }), 200