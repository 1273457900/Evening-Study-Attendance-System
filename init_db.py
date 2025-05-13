#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库初始化和更新脚本
用于确保数据库结构与当前模型匹配
"""

import os
import sys
from datetime import datetime
from app import app, db
from models import User, AttendanceRecord, LeaveRecord, ClassroomAdmin

def init_db():
    """初始化或更新数据库结构"""
    print("开始初始化数据库...")
    
    with app.app_context():
        # 创建所有表 (如果不存在)
        db.create_all()
        
        # 创建管理员账号 (如果不存在)
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                name='管理员',
                role='teacher'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("已创建管理员账号")
        
        # 更新暂离记录的班级和姓名字段
        update_leave_records()
        
        print("数据库初始化完成")

def update_leave_records():
    """更新暂离记录，添加班级和姓名字段"""
    print("开始更新暂离记录...")
    
    # 查找所有没有姓名或班级的暂离记录
    leave_records = LeaveRecord.query.filter(
        (LeaveRecord.student_name.is_(None)) | 
        (LeaveRecord.class_name.is_(None))
    ).all()
    
    updated_count = 0
    for record in leave_records:
        # 根据学生ID查找用户信息
        student = User.query.get(record.student_id)
        if student:
            # 更新暂离记录中的姓名和班级
            record.student_name = student.name
            record.class_name = student.class_name
            updated_count += 1
    
    if updated_count > 0:
        db.session.commit()
        print(f"已更新 {updated_count} 条暂离记录的姓名和班级信息")
    else:
        print("没有需要更新的暂离记录")

if __name__ == '__main__':
    init_db() 