import os
from datetime import datetime
from flask import jsonify, session, current_app, Blueprint
from db import db, TemporaryDrop, Group

card_functions_bp = Blueprint('card_functions_bp', __name__)

@card_functions_bp.route("/group/<int:group_id>/drop/<int:drop_id>/delete", methods=["POST"])
def delete_drop(group_id, drop_id):
    user_id = session.get('user_id') #[cite: 2]
    
    # Fetch the target drop[cite: 2]
    drop = TemporaryDrop.query.filter_by(id=drop_id, group_id=group_id).first_or_404() #[cite: 2]
    group = Group.query.get_or_404(group_id) #[cite: 2]

    # Check if lifespan has genuinely expired
    is_expired = drop.expires_at and datetime.utcnow() >= drop.expires_at

    # Authorization Check: User is owner, group creator, OR the drop is naturally expired[cite: 2]
    is_owner = (user_id and drop.user_id == user_id) #[cite: 2]
    is_group_creator = (user_id and group.creator_id == user_id) #[cite: 2]

    if not (is_owner or is_group_creator or is_expired):
        return jsonify({"error": "Forbidden. You do not have permission to delete this drop."}), 403 #[cite: 2]

    # Purge file system & database record[cite: 2]
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], drop.stored_name) #[cite: 2]
    if os.path.exists(file_path): #[cite: 2]
        try:
            os.remove(file_path) #[cite: 2]
        except OSError as e:
            print(f"Filesystem unlinking warning: {e}") #[cite: 2]

    try:
        db.session.delete(drop) #[cite: 2]
        db.session.commit() #[cite: 2]
    except Exception as e:
        db.session.rollback() #[cite: 2]
        return jsonify({"error": f"Failed to drop database row reference: {str(e)}"}), 500 #[cite: 2]

    return jsonify({
        "success": True,
        "message": "Temporary drop deleted permanently.", #[cite: 2]
        "drop_id": drop_id
    }), 200