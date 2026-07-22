from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

# ============================================================
# 1. UNIVERSAL USER PROFILES
# ============================================================
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    display_username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_icon = db.Column(db.String(10), default='👾')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships for back-referencing if needed
    groups_created = db.relationship('Group', backref='creator', cascade='all, delete-orphan', lazy=True)
    drops = db.relationship('TemporaryDrop', backref='user', cascade='all, delete-orphan', lazy=True)
    messages = db.relationship('ShoutboxMessage', backref='user', cascade='all, delete-orphan', lazy=True)

class UserConfig(db.Model):
    __tablename__ = 'user_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    setting_key = db.Column(db.String(64), nullable=False)
    setting_value = db.Column(db.Text, nullable=True)
    
    # Optional performance optimization index to speed up dictionary building
    __table_args__ = (
        db.Index('idx_user_setting', 'user_id', 'setting_key', unique=True),
    )

    def __repr__(self):
        return f"<UserConfig user_id={self.user_id} key='{self.setting_key}'>"


# ============================================================
# 2. MASTER GROUPS DIRECTORY
# ============================================================
class Group(db.Model):
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    invite_code = db.Column(db.String(20), nullable=False, unique=True)
    group_name = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Cascade configuration rules
    configs = db.relationship('GroupConfig', backref='group', cascade='all, delete-orphan', lazy=True)
    drops = db.relationship('TemporaryDrop', backref='group', cascade='all, delete-orphan', lazy=True)
    messages = db.relationship('ShoutboxMessage', backref='group', cascade='all, delete-orphan', lazy=True)

class StarredGroup(db.Model):
    __tablename__ = 'starred_groups'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False)
    starred_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'group_id', name='uq_user_starred_group'),
    )


# ============================================================
# 3. GROUP CONFIGURATIONS (Scoped by Group ID)
# ============================================================
class GroupConfig(db.Model):
    __tablename__ = 'group_config'
    
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id', ondelete='CASCADE'), primary_key=True)
    setting_key = db.Column(db.String(50), primary_key=True)  # Composite primary key setup
    setting_value = db.Column(db.String(255), nullable=False)


# ============================================================
# 4. SCOPED DYNAMIC FILES (TEMPORARY DROPS)
# ============================================================
class TemporaryDrop(db.Model):
    __tablename__ = 'temporary_drops'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    card_color = db.Column(db.String(100), default='from-blue-600 to-blue-900')
    user_emoji = db.Column(db.String(10), default='👾')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    # Magic unique constraint: 1 active file per user per group
    __table_args__ = (
        db.UniqueConstraint('group_id', 'user_id', name='uq_group_user_drop'),
    )

    @property
    def formatted_size(self):
        if not self.file_size:
            return "-- MB"
            
        size = float(self.file_size)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


# ============================================================
# 5. GROUP-ISOLATED CHAT LOGS
# ============================================================
class ShoutboxMessage(db.Model):
    __tablename__ = 'shoutbox_messages'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    message_text = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)