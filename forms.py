from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, BooleanField
from wtforms.validators import DataRequired, Length, ValidationError
from datetime import datetime

class LoginForm(FlaskForm):
    """登录表单"""
    username = StringField('用户名/学号', validators=[DataRequired(message='请输入用户名'), Length(min=2, max=50)])
    password = PasswordField('密码', validators=[DataRequired(message='请输入密码')])
    submit = SubmitField('登录')

class ImportStudentsForm(FlaskForm):
    """导入学生名单表单"""
    file = FileField('Excel文件', validators=[
        FileRequired(message='请选择Excel文件'),
        FileAllowed(['xlsx', 'xls'], message='仅支持Excel文件')
    ])
    submit = SubmitField('导入')

class ExportAttendanceForm(FlaskForm):
    """导出考勤记录表单"""
    start_date = DateField('开始日期', validators=[DataRequired(message='请选择开始日期')])
    end_date = DateField('结束日期', validators=[DataRequired(message='请选择结束日期')])
    class_name = SelectField('班级', choices=[('', '全部班级')], validate_choice=False)
    export_photos = BooleanField('同时导出照片', default=True)
    submit = SubmitField('导出')
    
    def validate_end_date(self, field):
        """验证结束日期必须大于等于开始日期"""
        if field.data < self.start_date.data:
            raise ValidationError('结束日期必须大于等于开始日期')
        
        # 限制导出范围不超过6个月
        delta = field.data - self.start_date.data
        if delta.days > 180:
            raise ValidationError('导出时间范围不能超过6个月') 