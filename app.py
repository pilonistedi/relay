from flask import Flask, render_template, session, redirect, url_for
from flask_cors import CORS
from db import db, Group, GroupConfig
from api.auth import auth_bp
from api.group_handler import group_handler_bp
from api.upload import upload_bp
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
        return render_template('feed.html', groups=groups)
    
    @app.route("/auth")
    def auth():
        return render_template('auth.html')

    return app

if __name__ == '__main__':
    app = create_app()
    # Runs locally on port 5000
    app.run(debug=True, port=5000)