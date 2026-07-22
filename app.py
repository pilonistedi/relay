from flask import Flask, render_template, session, redirect, request, jsonify
from flask_cors import CORS
from db import db, Group, GroupConfig, User, StarredGroup
from api.auth import auth_bp
from api.group_handler import group_handler_bp
from api.upload import upload_bp
from api.chat import chat_bp
from api.card_functions import card_functions_bp
from api.admin import admin_bp
import os

def get_group_configs(target_group_id):

    # 1. Pull all rows for this specific group
    rows = GroupConfig.query.filter_by(group_id=target_group_id).all()
    
    # 2. Build a raw dictionary from the database rows
    raw_configs = {row.setting_key: row.setting_value for row in rows}
    
    # If the group doesn't exist or has no configs, return None or an empty dict
    if not raw_configs:
        return None

    # 3. Clean and parse data types (since database values are strings)
    return {
        'group_name': raw_configs.get('group_name', 'Unnamed Group'),
        'security_engine': raw_configs.get('security_engine', 'standard'),
        'lifespan_minutes': int(raw_configs.get('lifespan_minutes', 60)), # Cast to int
        'description': raw_configs.get('description', ''),
        'identity_icon': raw_configs.get('identity_icon', '👾'),
        'theme_color_key': raw_configs.get('theme_color_key', 'blue')
    }


def create_app():
    app = Flask(__name__)
    
    # Enable CORS so your frontend can communicate seamlessly across ports if needed
    CORS(app, supports_credentials=True)

    # --- GLOBAL SYSTEM CONFIGURATIONS ---
    app.secret_key = 'relay_super_secret_system_token_key'
    
    # Points to your local XAMPP MySQL server and the database container
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/relay_workspace'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Bind database to the application context
    db.init_app(app)

    UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Dynamic check: Ensure the directories exist on your machine, create them if missing
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # --- REGISTER MODULE BLUEPRINTS ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(group_handler_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(card_functions_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def utility_processor():
        def lifespan_remaining_mins(expires_at):
            if not expires_at:
                return 0
            from datetime import datetime
            # Calculate difference between expiration time and current UTC time
            diff = expires_at - datetime.utcnow()
            return max(0, int(diff.total_seconds() / 60))
        
        return dict(lifespan_remaining_mins=lifespan_remaining_mins)

    # --- DEFINE GLOBAL ROUTES INSIDE THE FACTORY ---
    @app.route('/')
    def index():
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth'))
        
        groups = Group.query.order_by(Group.created_at.desc()).all()
        email = db.session.query(User.email).filter(User.id == user_id).scalar().lower()
        
        starred_group_ids = set(
            row.group_id for row in StarredGroup.query.filter_by(user_id=user_id).all()
        )

        for group in groups:
            config_rows = GroupConfig.query.filter(
                GroupConfig.group_id == group.id,
                GroupConfig.setting_key.in_(['security_engine', 'identity_icon'])
            ).all()
            
            settings_dict = {row.setting_key: row.setting_value for row in config_rows}
            settings_dict.setdefault('security_engine', 'Open Hub Access')
            settings_dict.setdefault('identity_icon', '🚀')
            group.settings = settings_dict

            group.creator_name = (
                group.creator.display_username or group.creator.email.split('@')[0]
                if group.creator else "Unknown"
            )

            group.is_starred = group.id in starred_group_ids

        groups.sort(key=lambda g: g.is_starred, reverse=True)

        return render_template('feed.html', groups=groups, email=email)

    @app.route('/api/search_groups', methods=['GET'])
    def search_groups():
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify([])

        # Query groups matching the search string (case-insensitive)
        matched_groups = Group.query.filter(Group.group_name.ilike(f"%{query}%")).limit(6).all()

        results = []
        for g in matched_groups:
            # Fetch the icon setting if stored in GroupConfig
            icon_row = GroupConfig.query.filter_by(group_id=g.id, setting_key='identity_icon').first()
            icon = icon_row.setting_value if icon_row else '🚀'

            results.append({
                'id': g.id,
                'group_name': g.group_name,
                'icon': icon
            })

        return jsonify(results)
        
    @app.route("/auth")
    def auth():
        return render_template('auth.html')

    return app

if __name__ == '__main__':
    app = create_app()
    # Runs locally on port 5000
    app.run(debug=True, port=5000)