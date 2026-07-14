from flask import Blueprint, request, jsonify, session, current_app
from db import db, User, Group, TemporaryDrop, GroupConfig  # Ensure correct models are imported
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

# 1. Define the blueprint correctly
upload_bp = Blueprint('upload_bp', __name__)

# 2. Assign the route decorator to upload_bp instead of group_handler_bp
@upload_bp.route("/group/<int:group_id>/upload", methods=["POST"])
def upload_asset(group_id):
    # Enforce Authentication Guard
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized. Please log in first."}), 401

    # Fetch user data
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User account context not found."}), 404

    # Extract and Validate File Content
    if 'file' not in request.files:
        return jsonify({"error": "No file payload detected."}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Selected filename is empty."}), 400

    # Pull Dynamic Lifespan Limit from Group Settings
    config_rows = GroupConfig.query.filter_by(group_id=group_id).all()
    settings = {row.setting_key: row.setting_value for row in config_rows}
    lifespan_mins = int(settings.get('lifespan_minutes', 45))
    
    # Precise timing limits
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=lifespan_mins)

    # Handle Unique Constraint Policy (Strict 1 Card Per User per Group)
    existing_drop = TemporaryDrop.query.filter_by(group_id=group_id, user_id=user_id).first()

    original_name = file.filename
    secured_name = secure_filename(original_name)
    
    # Append timestamp string to stored filename to prevent filesystem collisions
    stored_name = f"{user_id}_{int(now.timestamp())}_{secured_name}"
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_name)

    # Read the data stream size cleanly in bytes without blowing out RAM bounds
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0) # Reset stream pointer back to start before saving

    if existing_drop:
        # PATH A: PERMANENT REPLACEMENT POLICY
        old_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], existing_drop.stored_name)
        if os.path.exists(old_file_path):
            try:
                os.remove(old_file_path)
            except OSError as e:
                print(f"File unlinking warning: {e}")

        # Overwrite structural row properties
        existing_drop.original_name = original_name
        existing_drop.stored_name = stored_name
        existing_drop.file_size = file_size
        existing_drop.created_at = now
        existing_drop.expires_at = expires_at
        
        if 'theme_color_gradient' in settings:
            existing_drop.card_color = settings['theme_color_gradient']

        action_performed = "replaced"
    else:
        # PATH B: FRESH CARD PROVISION ALLOCATION
        theme_color = settings.get('theme_color_gradient', 'from-blue-600 to-blue-900')
        
        existing_drop = TemporaryDrop(
            group_id=group_id,
            user_id=user_id,
            original_name=original_name,
            stored_name=stored_name,
            file_size=file_size,
            card_color=theme_color,
            user_emoji=user.profile_icon,
            created_at=now,
            expires_at=expires_at
        )
        db.session.add(existing_drop)
        action_performed = "created"

    # Flush Changes and Save to Storage Engine
    try:
        file.save(save_path)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed writing to backend database layout: {str(e)}"}), 500

    # Dispatch Clean Response back to AJAX Frontend Listeners
    return jsonify({
        "success": True,
        "action": action_performed,
        "drop_id": existing_drop.id,
        "original_name": original_name,
        "uploaded_by": user.display_username,
        "user_emoji": existing_drop.user_emoji,
        "card_color": existing_drop.card_color,
        "expires_in_mins": lifespan_mins
    }), 200