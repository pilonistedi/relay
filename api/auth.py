from flask import Blueprint, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import random
from db import db, User

# Define the isolated authorization blueprint node
auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/auth', methods=['POST'])
def auth():
    data = request.get_json()
    
    if not data or 'action' not in data:
        return jsonify({'success': False, 'message': 'Malformed payload stream.'}), 400
        
    action = data['action']

    # --------------------------------------------------------
    # SIGNUP ROUTE
    # --------------------------------------------------------
    if action == 'signup':
        email = data.get('email', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')

        # Gate validations
        if not email or not username or not password:
            return jsonify({'success': False, 'message': 'All system validation fields are required.'}), 200
        if password != confirm_password:
            return jsonify({'success': False, 'message': 'Password verification mismatch.'}), 200
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password safety threshold not met (min 6 chars).'}), 200

        try:
            # Check if email or username already exists in your table mappings
            existing_user = User.query.filter((User.email == email) | (User.display_username == username)).first()
            if existing_user:
                msg = 'This email is already registered.' if existing_user.email == email else 'This username is already active.'
                return jsonify({'success': False, 'message': msg}), 200

            # Secure hashing using PBKDF2 algorithm matching VARCHAR(255) size bounds
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            
            # Select random default icon for profile metadata
            icons = ['👾', '🚀', '🔮', '🛡️', '⚡', '🧠']
            default_icon = random.choice(icons)

            # Insert raw profile parameters into MySQL via SQLAlchemy
            new_user = User(email=email, display_username=username, password_hash=hashed_password, profile_icon=default_icon)
            db.session.add(new_user)
            db.session.commit()

            # Assign system state session data
            session['user_id'] = new_user.id
            session['display_username'] = new_user.display_username
            session['profile_icon'] = new_user.profile_icon

            return jsonify({'success': True, 'message': 'Identity profile structured successfully.'}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Database processing failure: {str(e)}'}), 500

    # --------------------------------------------------------
    # LOGIN ROUTE
    # --------------------------------------------------------
    elif action == 'login':
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'success': False, 'message': 'All credential fields must be populated.'}), 200

        try:
            # Query user matching unique user identity string
            user = User.query.filter_by(display_username=username).first()

            # Hash decryption check verification
            if user and check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                session['display_username'] = user.display_username
                session['profile_icon'] = user.profile_icon
                
                return jsonify({'success': True, 'message': 'Authentication parameters accepted.'}), 200
            else:
                return jsonify({'success': False, 'message': 'Invalid username or password credentials specified.'}), 200

        except Exception as e:
            return jsonify({'success': False, 'message': f'Server sequence error: {str(e)}'}), 500

    return jsonify({'success': False, 'message': 'Invalid execution action route requests.'}), 400

@auth_bp.route("/logout")
def logout():
    session.pop('user_id', None)
    session.pop('display_username', None)
    session.pop('profile_icon', None)
    return redirect(url_for('index'))