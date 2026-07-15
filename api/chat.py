from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from datetime import datetime
from db import db, User, Group, ShoutboxMessage, TemporaryDrop

# Define the isolated authorization blueprint node
chat_bp = Blueprint('chat_bp', __name__)

# ============================================================
# 1. VIEW ROUTE: Renders the Workspace & Initial History
# ============================================================
@chat_bp.route('/chat/<int:group_id>')
def chat(group_id):
    # Ensure user is logged in
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth_bp.login'))  # Adjust this to point to your login route
    
    # Fetch the group or return a 404
    group = Group.query.get_or_404(group_id)
    
    # 1. Fetch active temporary drops for the group
    drops = TemporaryDrop.query.filter_by(group_id=group_id).all()
    
    # 2. Grab the last 50 shoutbox logs in ascending order (newest at the bottom)
    messages = ShoutboxMessage.query.filter_by(group_id=group_id)\
        .order_by(ShoutboxMessage.sent_at.asc())\
        .limit(50)\
        .all()
    
    # 3. Determine if the current logged-in user is the workspace creator
    is_creator = (group.creator_id == user_id)
    
    # 4. Resolve group settings (Convert composite config key/value rows to a clean dictionary)
    # This aligns with settings.group_name, settings.theme_selection, etc. in your group.html
    raw_configs = group.configs
    settings = {cfg.setting_key: cfg.setting_value for cfg in raw_configs}
    
    # Helper context function: Calculate remaining minutes on a file's lifespan
    def lifespan_remaining_mins(expires_at):
        if not expires_at:
            return 0
        delta = expires_at - datetime.utcnow()
        return max(0, int(delta.total_seconds() / 60))

    return render_template(
        'group.html',
        group_id=group.id,
        settings=settings,
        drops=drops,
        is_creator=is_creator,
        messages=messages,
        lifespan_remaining_mins=lifespan_remaining_mins
    )


# ============================================================
# 2. API ENDPOINT: Store Message (POST)
# ============================================================
@chat_bp.route('/chat/<int:group_id>/send', methods=['POST'])
def send_message(group_id):
    # Ensure user session is validated
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Grab JSON payload
    data = request.get_json() or {}
    message_text = data.get('message_text', '').strip()
    
    # Validate payload is not blank
    if not message_text:
        return jsonify({'error': 'Message text cannot be empty'}), 400
        
    # Verify group exists
    group = Group.query.get_or_404(group_id)
    
    # Store message in DB
    new_message = ShoutboxMessage(
        group_id=group.id,
        user_id=user_id,
        message_text=message_text,
        sent_at=datetime.utcnow()
    )
    
    db.session.add(new_message)
    db.session.commit()
    
    # Return saved message parameters back to the client
    return jsonify({
        'success': True,
        'message': {
            'username': new_message.user.display_username,
            'user_emoji': new_message.user.profile_icon,
            'message_text': new_message.message_text,
            'sent_at': new_message.sent_at.strftime('%I:%M %p')
        }
    })


# ============================================================
# 3. API ENDPOINT: Read Messages (GET)
# ============================================================
@chat_bp.route('/chat/<int:group_id>/messages', methods=['GET'])
def get_messages(group_id):
    # Ensure user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    # Query last 50 logs matching group_id
    messages = ShoutboxMessage.query.filter_by(group_id=group_id)\
        .order_by(ShoutboxMessage.sent_at.asc())\
        .limit(50)\
        .all()
        
    # Package into clean JSON list
    messages_data = [{
        'username': msg.user.display_username if msg.user else "Anonymous",
        'user_emoji': msg.user.profile_icon if msg.user else "👾",
        'message_text': msg.message_text,
        'sent_at': msg.sent_at.strftime('%I:%M %p')
    } for msg in messages]
    
    return jsonify({'messages': messages_data})