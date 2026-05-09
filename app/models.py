from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

#from app import db  # Assuming db = SQLAlchemy() is initialized in your factory
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Enum for Roles
    role = db.Column(db.Enum('student', 'employer', 'admin', name='user_roles'), default='student')
    
    is_active = db.Column(db.Boolean, default=True)
    full_name = db.Column(db.String(255))
    age = db.Column(db.Integer)
    bio = db.Column(db.Text)
    
    # Enum for Jamaican Parishes
    parish = db.Column(db.Enum(
        'Kingston', 'St. Andrew', 'St. Thomas', 'Portland', 'St. Mary', 
        'St. Ann', 'Trelawny', 'St. James', 'Hanover', 'Westmoreland', 
        'St. Elizabeth', 'Manchester', 'Clarendon', 'St. Catherine', 
        name='jamaican_parishes'
    ))
    
    location_preferences = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    # Relationships
    skills = db.relationship('Skill', secondary='user_skills', backref=db.backref('users', lazy='dynamic'))

class UserSkill(db.Model):
    __tablename__ = 'user_skills'

    # Composite Primary Key 
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='CASCADE'), primary_key=True)


class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    job_source = db.Column(db.String(50), nullable=False)
    source_job_id = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(255))
    company = db.Column(db.String(255))
    city = db.Column(db.String(100))
    country = db.Column(db.String(50))
    is_remote = db.Column(db.Boolean)  # Maps from tinyint(1)
    apply_link = db.Column(db.Text)
    description = db.Column(db.Text)   # Maps from longtext
    
    # Salary Info
    salary_text = db.Column(db.String(255))
    salary_min = db.Column(db.Numeric(12, 2))
    salary_max = db.Column(db.Numeric(12, 2))
    salary_currency = db.Column(db.String(10))
    salary_period = db.Column(db.String(20))
    salary_source = db.Column(db.String(50))
    
    keywords = db.Column(db.Text)

    # Unique Constraint for source job
    __table_args__ = (
        db.UniqueConstraint('job_source', 'source_job_id', name='uniq_source_job'),
    )

    # Relationships (for easy access: my_job.skills, my_job.experience)
    skills = db.relationship('JobSkill', backref='job', cascade="all, delete-orphan")
    experience = db.relationship('JobExperience', backref='job', cascade="all, delete-orphan")
    certs = db.relationship('JobCert', backref='job', cascade="all, delete-orphan")
    degrees = db.relationship('JobDegree', backref='job', cascade="all, delete-orphan")
    bookmarks = db.relationship('Bookmark', backref='job', lazy=True)

    
    
class Bookmark(db.Model):
    __tablename__ = 'bookmarks'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    # Note: user_id is Integer, job_id is BigInteger to match your SQL dump
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.BigInteger, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)

    # Scores (using Numeric to represent Decimal precision=6, scale=4)
    match_score = db.Column(db.Numeric(6, 4))
    pref_score = db.Column(db.Numeric(6, 4))
    final_score = db.Column(db.Numeric(6, 4))
    # Timestamp
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Unique Constraint: Prevents a user from bookmarking the same job twice
    __table_args__ = (
        db.UniqueConstraint('user_id', 'job_id', name='uniq_user_job'),
    )

    def __repr__(self):
        return f"<Bookmark User:{self.user_id} Job:{self.job_id}>"


class JobCert(db.Model):
    __tablename__ = 'job_certs'

    # Composite Primary Key (job_id + cert)
    job_id = db.Column(db.BigInteger, db.ForeignKey('jobs.id', ondelete='CASCADE'), primary_key=True)
    cert = db.Column(db.String(100), primary_key=True, nullable=False)

    def __repr__(self):
        return f"<JobCert Job:{self.job_id} Cert:{self.cert}>"


class JobDegree(db.Model):
    __tablename__ = 'job_degrees'

    # Foreign Key + Part of Composite PK
    job_id = db.Column(db.BigInteger, db.ForeignKey('jobs.id', ondelete='CASCADE'), primary_key=True)
    
    # The Degree String + Part of Composite PK
    degree = db.Column(db.String(100), primary_key=True, nullable=False)

    def __repr__(self):
        return f"<JobDegree Job:{self.job_id} Degree:{self.degree}>"


class JobExperience(db.Model):
    __tablename__ = 'job_experience'
    job_id = db.Column(db.BigInteger, db.ForeignKey('jobs.id', ondelete='CASCADE'), primary_key=True)
    experience = db.Column(db.String(100), primary_key=True)

class JobSkill(db.Model):
    __tablename__ = 'job_skills'
    job_id = db.Column(db.BigInteger, db.ForeignKey('jobs.id', ondelete='CASCADE'), primary_key=True)
    skill = db.Column(db.String(100), primary_key=True)

class Resume(db.Model):
    __tablename__ = 'resumes'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    student_id = db.Column(db.BigInteger, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, default=1)
    filename = db.Column(db.String(255))
    raw_text = db.Column(db.Text, nullable=False)  # Maps from longtext
    keywords = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f"<Resume {self.filename}>"

class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<Skill {self.name}>"

class TokenBlocklist(db.Model):
    __tablename__ = 'token_blocklist'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    jti = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f"<TokenBlocklist {self.jti}>"
    
