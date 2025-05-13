from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """用户表，包括学生和教师"""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)  # 用户名/学号
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # 姓名
    class_name = db.Column(db.String(50), nullable=True)  # 班级
    classroom_location = db.Column(db.String(50), nullable=True)  # 教室位置，如G503
    role = db.Column(db.String(10), nullable=False)  # 角色：student 或 teacher
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom_admins.id'), nullable=True)  # 关联的教室ID
    
    attendance_records = db.relationship('AttendanceRecord', backref='student', lazy=True)
    leave_records = db.relationship('LeaveRecord', backref='student', lazy=True, 
                                   primaryjoin="User.id == LeaveRecord.student_id")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """返回唯一标识，格式为 'user_用户ID'"""
        return f'user_{self.id}'
    
    def __repr__(self):
        return f'<User {self.username}>'

class AttendanceRecord(db.Model):
    """考勤记录表"""
    __tablename__ = 'attendance_records'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 学生ID
    student_name = db.Column(db.String(50), nullable=True)  # 学生姓名
    class_name = db.Column(db.String(50), nullable=True)  # 班级
    date = db.Column(db.Date, nullable=False)  # 日期
    sign_in_time = db.Column(db.DateTime, nullable=True)  # 签到时间
    sign_in_photo = db.Column(db.String(255), nullable=True)  # 签到照片
    sign_out_time = db.Column(db.DateTime, nullable=True)  # 签出时间
    # 以下两个字段将被弃用，仅保留向后兼容性
    leave_time = db.Column(db.DateTime, nullable=True)  # 暂离时间
    leave_photo = db.Column(db.String(255), nullable=True)  # 暂离照片
    return_time = db.Column(db.DateTime, nullable=True)  # 返回时间
    return_photo = db.Column(db.String(255), nullable=True)  # 返回照片
    
    def __repr__(self):
        return f'<AttendanceRecord {self.id}>'

class LeaveRecord(db.Model):
    """暂离记录表"""
    __tablename__ = 'leave_records'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 学生ID
    student_name = db.Column(db.String(50), nullable=True)  # 学生姓名
    class_name = db.Column(db.String(50), nullable=True)  # 班级
    attendance_id = db.Column(db.Integer, db.ForeignKey('attendance_records.id'), nullable=False)  # 关联的考勤记录ID
    leave_time = db.Column(db.DateTime, nullable=False)  # 暂离时间
    leave_photo = db.Column(db.String(255), nullable=True)  # 暂离照片
    return_time = db.Column(db.DateTime, nullable=True)  # 返回时间
    return_photo = db.Column(db.String(255), nullable=True)  # 返回照片
    reason = db.Column(db.String(255), nullable=True)  # 暂离原因
    duration = db.Column(db.Integer, nullable=True)  # 暂离时长(秒)
    
    # 关联到考勤记录
    attendance = db.relationship('AttendanceRecord', backref='leave_records')
    
    def __repr__(self):
        return f'<LeaveRecord {self.id}>'
    
    @property
    def is_active(self):
        """判断是否是活跃的暂离记录（尚未返回）"""
        return self.leave_time is not None and self.return_time is None
    
    @property
    def formatted_duration(self):
        """格式化的暂离时长"""
        if self.duration is None:
            return "未返回"
        
        minutes, seconds = divmod(self.duration, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f"{hours}小时{minutes}分钟"
        else:
            return f"{minutes}分钟{seconds}秒"

class ClassroomAdmin(db.Model, UserMixin):
    __tablename__ = 'classroom_admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)  # 教室账号，如 g503
    classroom_name = db.Column(db.String(50), nullable=False)  # 教室名称，如 G503
    password_hash = db.Column(db.String(128))
    password_text = db.Column(db.String(50))  # 明文密码，用于显示
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # 添加角色标识，固定为'classroom_admin'
    role = 'classroom_admin'
    
    # 关联的学生
    students = db.relationship('User', backref='classroom', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.password_text = str(password)  # 确保密码以字符串形式保存
        
    def check_password(self, password):
        # 如果传入的密码是数字，转换为字符串
        if isinstance(password, (int, float)):
            password = str(int(password))
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """返回唯一标识，格式为 'admin_管理员ID'"""
        return f'admin_{self.id}'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'classroom_name': self.classroom_name,
            'password': self.password_text,  # 添加明文密码
            'is_active': self.is_active,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else None
        } 

class AbsenceRecord(db.Model):
    """请假记录表"""
    __tablename__ = 'absence_records'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 学生ID
    student_name = db.Column(db.String(50), nullable=True)  # 学生姓名
    class_name = db.Column(db.String(50), nullable=True)  # 班级
    date = db.Column(db.Date, nullable=False, default=datetime.now().date)  # 请假日期
    created_at = db.Column(db.DateTime, default=datetime.now)  # 创建时间
    absence_type = db.Column(db.String(50), nullable=False)  # 请假类型：事假、病假、社团、学生会等
    reason = db.Column(db.String(255), nullable=True)  # 请假原因
    approved_by = db.Column(db.String(50), nullable=True)  # 批准人/记录人
    
    # 关联到学生
    student = db.relationship('User', backref='absences', lazy=True)
    
    def __repr__(self):
        return f'<AbsenceRecord {self.id} - {self.student_name} - {self.absence_type}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'class_name': self.class_name,
            'date': self.date.strftime('%Y-%m-%d'),
            'absence_type': self.absence_type,
            'reason': self.reason,
            'approved_by': self.approved_by,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } 