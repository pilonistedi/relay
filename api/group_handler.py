from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
import random
from db import db, User, Group, GroupConfig, TemporaryDrop
import string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask import current_app
# Manage Groups
group_handler_bp = Blueprint('group_handler_bp', __name__)

# --- The Translated PHP Theme Map (Python Dictionary Variant) ---
THEME_MAP = {
    'blue': {
        'hover_border': 'hover:border-blue-500/40',
        'glow_shadow': 'hover:shadow-[0_0_25px_rgba(59,130,246,0.12)]',
        'badge_text': 'text-blue-400',
        'badge_bg': 'bg-blue-500/20 border-blue-500/20',
        'btn_bg': 'bg-blue-500 hover:bg-blue-400 text-neutral-950'
    },
    'cyan': {
        'hover_border': 'hover:border-cyan-500/40',
        'glow_shadow': 'hover:shadow-[0_0_25px_rgba(6,182,212,0.12)]',
        'badge_text': 'text-cyan-400',
        'badge_bg': 'bg-cyan-500/20 border-cyan-500/20',
        'btn_bg': 'bg-cyan-500 hover:bg-cyan-400 text-neutral-950'
    },
    'purple': {
        'hover_border': 'hover:border-purple-500/40',
        'glow_shadow': 'hover:shadow-[0_0_25px_rgba(168,85,247,0.12)]',
        'badge_text': 'text-purple-400',
        'badge_bg': 'bg-purple-500/20 border-purple-500/20',
        'btn_bg': 'bg-purple-500 hover:bg-purple-400 text-neutral-950'
    },
    'emerald': {
        'hover_border': 'hover:border-emerald-500/40',
        'glow_shadow': 'hover:shadow-[0_0_25px_rgba(16,185,129,0.12)]',
        'badge_text': 'text-emerald-400',
        'badge_bg': 'bg-emerald-500/20 border-emerald-500/20',
        'btn_bg': 'bg-emerald-500 hover:bg-emerald-400 text-neutral-950'
    },
    'amber': {
        'hover_border': 'hover:border-amber-500/40',
        'glow_shadow': 'hover:shadow-[0_0_25px_rgba(245,158,11,0.12)]',
        'badge_text': 'text-amber-400',
        'badge_bg': 'bg-amber-500/20 border-amber-500/20',
        'btn_bg': 'bg-amber-500 hover:bg-amber-400 text-neutral-950'
    },
    'rose': {
        'hover_border': 'hover:border-rose-500/40',
        'glow_shadow': 'hover:shadow-[0_0_25px_rgba(244,63,94,0.12)]',
        'badge_text': 'text-rose-400',
        'badge_bg': 'bg-rose-500/20 border-rose-500/20',
        'btn_bg': 'bg-rose-500 hover:bg-rose-400 text-neutral-950'
    }
}

def generate_invite_code(length=8):
    """Generates a secure random alphanumeric invite string."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


@group_handler_bp.route("/create_group", methods=["POST"])
def create_group():
    creator_id = session.get('user_id')
    
    # 1. Enforce Authentication Guard for API requests safely
    if not creator_id:
        return jsonify({
            "success": False, 
            "redirect_to": url_for('auth') # Point to global app factory auth route
        }), 401

    # Gather raw inputs from form fields
    group_name = request.form.get("group_name", "Unnamed Hub")
    security_engine = request.form.get("security_engine", "Open Hub Access")
    lifespan = request.form.get("lifespan", "45") 
    description = request.form.get("description", "")
    
    # Capture the active palette choice from the hidden input field
    selected_palette_class = request.form.get("selected_palette", "bg-blue-50/60")
    theme_key = selected_palette_class.split('-')[1] if '-' in selected_palette_class else 'blue'
    if theme_key not in THEME_MAP:
        theme_key = 'blue'

    # 2. Build the Core Group Entity Row
    invite_code = generate_invite_code()
    new_group = Group(
        creator_id=creator_id,
        invite_code=invite_code,
        group_name=group_name,
        created_at=datetime.utcnow()
    )
    
    try:
        db.session.add(new_group)
        db.session.flush() 

        # 3. Dynamic Identity Configuration
        icons = ['👾', '🚀', '🔮', '🛡️', '⚡', '🧠']
        chosen_icon = random.choice(icons)

        configs_to_create = {
            'group_name': group_name,
            'security_engine': security_engine,
            'lifespan_minutes': lifespan,
            'description': description,
            'identity_icon': chosen_icon,
            'theme_color_key': theme_key
        }

        theme_styles = THEME_MAP[theme_key]
        for style_key, class_string in theme_styles.items():
            configs_to_create[f"theme_{style_key}"] = class_string

        # FIXED: Mapped to match HTML input name="backdrop_spec"
        if 'backdrop_spec' in request.files:
            file = request.files['backdrop_spec']

            if file and file.filename:
                filename = secure_filename(file.filename)

                upload_folder = os.path.join(
                    current_app.static_folder,
                    "images"
                )

                os.makedirs(upload_folder, exist_ok=True)

                file.save(os.path.join(upload_folder, filename))

                configs_to_create['has_custom_backdrop'] = "true"
                configs_to_create['backdrop_filename'] = filename

        # 4. Save entire configuration suite tracking to database
        for key, value in configs_to_create.items():
            config_entry = GroupConfig(
                group_id=new_group.id,
                setting_key=key,
                setting_value=str(value)
            )
            db.session.add(config_entry)

        db.session.commit()
        
        # FIXED: Returning uniform data structure with boolean "success": True
        return jsonify({
            "success": True, 
            "group_id": new_group.id, 
            "invite_code": invite_code
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@group_handler_bp.route("/group/<int:group_id>")
def group(group_id):
    # 1. Enforce Authentication Guard
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth'))

    # 2. Fetch the group or return a 404 if it doesn't exist
    group = Group.query.get_or_404(group_id)

    # 3. Retrieve all configuration rows for this specific workspace
    config_rows = GroupConfig.query.filter_by(group_id=group.id).all()

    # 4. Collapse the EAV (Entity-Attribute-Value) rows into a clean dictionary
    settings = {row.setting_key: row.setting_value for row in config_rows}

    # 5. Inject baseline safe fallbacks if configuration records are absent
    defaults = {
        'group_name': group.group_name or 'Unnamed Hub',
        'security_engine': 'Open Hub Access',
        'lifespan_minutes': '45',
        'description': '',
        'identity_icon': '🚀',
        'theme_color_key': 'sky', 
        
        # Comprehensive theme mapping injected into templates
        'theme_hover_border': 'hover:border-sky-500/40',
        'theme_glow_shadow': 'hover:shadow-[0_0_25px_rgba(59,130,246,0.12)]',
        'theme_badge_text': 'text-sky-400',
        'theme_badge_bg': 'bg-sky-500/20 border-sky-500/20',
        'theme_btn_bg': 'bg-sky-500 hover:bg-sky-400 text-neutral-950',
        
        # New structural additions to isolate custom styles for dynamic UI elements
        'theme_accent_text': 'text-sky-400',
        'theme_accent_border': 'border-sky-500/20',
        'theme_interactive_bg': 'bg-sky-600/10 hover:bg-sky-600/20',
        'theme_interactive_hover_border': 'hover:border-sky-500/40 group-hover:border-sky-500/40',
        'theme_interactive_hover_text': 'hover:text-sky-300 group-hover:text-sky-400',
        'theme_focus_ring': 'focus:border-sky-500 focus:ring-sky-500/10 focus:ring-2',
        'theme_selection': 'selection:bg-sky-500 selection:text-neutral-950',
        
        'backdrop_filename': 'default_backdrop.jpg' 
    }

    for key, default_value in defaults.items():
        if key not in settings or not settings[key]:
            settings[key] = default_value

    # Process gradients natively
    if 'theme_color_key' in settings and settings['theme_color_key'] in THEME_MAP:
        color = settings['theme_color_key']
        settings['theme_color_gradient'] = f"from-{color}-500 to-{color}-600"
        settings['theme_pulse_dot'] = f"bg-{color}-500"
    else:
        settings['theme_color_gradient'] = "from-sky-500 to-indigo-600"
        settings['theme_pulse_dot'] = "bg-sky-500"

    current_user_id = session.get('user_id')

    is_creator = False
    if current_user_id and hasattr(group, 'creator_id'):
        is_creator = (group.creator_id == current_user_id)
    elif current_user_id and hasattr(group, 'user_id'):
        is_creator = (group.user_id == current_user_id)

    drops = TemporaryDrop.query.filter_by(group_id=group_id).order_by(TemporaryDrop.created_at.desc()).all()

    # 6. Render the workspace template passing down the compiled settings
    is_locked = False
    return render_template("group.html", settings=settings, group=group, drops=drops, is_creator=is_creator, group_id=group_id, is_locked=is_locked)

@group_handler_bp.route('/join/<int:group_id>', methods=['POST'])
def join_group(group_id):
    pass