import os
from functools import wraps
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from db import db, Group, TemporaryDrop, User

admin_bp = Blueprint('admin_bp', __name__)

def admin_required(f):
    """Session guard to ensure only authenticated admins can access routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_bp.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def format_file_size(size_in_bytes):
    """Utility to convert raw bytes into human-readable strings."""
    if not size_in_bytes:
        return "0 KB"
    size_in_kb = size_in_bytes / 1024
    if size_in_kb < 1024:
        return f"{size_in_kb:.1f} KB"
    size_in_mb = size_in_kb / 1024
    if size_in_mb < 1024:
        return f"{size_in_mb:.1f} MB"
    size_in_gb = size_in_mb / 1024
    return f"{size_in_gb:.2f} GB"

@admin_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get('is_admin'):
        return redirect(url_for('admin_bp.admin_dashboard'))

    if request.method == "POST":
        admin_passkey = request.form.get("admin_passkey")
        MASTER_ADMIN_KEY = current_app.config.get('ADMIN_PASSKEY', 'relay-admin-secret-key')

        if admin_passkey == MASTER_ADMIN_KEY:
            session['is_admin'] = True
            return redirect(url_for('admin_bp.admin_dashboard'))
        else:
            flash("Invalid Admin Passkey. Access Denied.", "error")

    return render_template("admin_login.html")

@admin_bp.route("/admin/logout")
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('admin_bp.admin_login'))

@admin_bp.route("/admin")
@admin_required
def admin_dashboard():
    groups = Group.query.all()
    
    group_stats = []
    total_system_files = 0
    total_system_bytes = 0

    for group in groups:
        drops = TemporaryDrop.query.filter_by(group_id=group.id).all()
        file_count = len(drops)
        
        group_byte_size = 0
        for drop in drops:
            if hasattr(drop, 'file_size') and drop.file_size:
                group_byte_size += drop.file_size
            else:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], drop.stored_name)
                if os.path.exists(file_path):
                    group_byte_size += os.path.getsize(file_path)

        total_system_files += file_count
        total_system_bytes += group_byte_size

        group_stats.append({
            "id": group.id,
            "name": group.group_name,
            "security_engine": getattr(group, 'security_engine', 'open'),
            "file_count": file_count,
            "raw_bytes": group_byte_size,
            "formatted_size": format_file_size(group_byte_size),
            "invite_code": getattr(group, 'invite_code', '')
        })

    # Sort groups by raw storage size descending
    sorted_groups = sorted(group_stats, key=lambda x: x['raw_bytes'], reverse=True)

    # Dataset 1: Top 10 heavy storage consumers (Default Chart)
    top_10 = sorted_groups[:10]
    top_chart_labels = [g['name'] for g in top_10]
    top_chart_storage = [round(g['raw_bytes'] / (1024 * 1024), 2) for g in top_10]
    top_chart_files = [g['file_count'] for g in top_10]

    # Dataset 2: All groups (For full horizontal scroll mode)
    all_chart_labels = [g['name'] for g in sorted_groups]
    all_chart_storage = [round(g['raw_bytes'] / (1024 * 1024), 2) for g in sorted_groups]
    all_chart_files = [g['file_count'] for g in sorted_groups]

    return render_template(
        "admin.html",
        group_stats=sorted_groups,
        total_groups=len(groups),
        total_files=total_system_files,
        total_storage=format_file_size(total_system_bytes),
        # Top 10 payload
        top_labels=top_chart_labels,
        top_storage=top_chart_storage,
        top_files=top_chart_files,
        # Full payload
        all_labels=all_chart_labels,
        all_storage=all_chart_storage,
        all_files=all_chart_files
    )