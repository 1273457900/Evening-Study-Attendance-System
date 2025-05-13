"""
重置数据库脚本
用于在模型发生变化后重新创建数据库结构
"""
from app import app, db, User, ClassroomAdmin
from datetime import datetime

def reset_database():
    with app.app_context():
        print("正在重置数据库...")
        db.drop_all()  # 删除所有表
        db.create_all()  # 重新创建所有表
        
        # 创建管理员账号
        admin = User(
            username='admin',
            name='管理员',
            role='teacher'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # 创建示例教室管理员账号
        classroom_admin1 = ClassroomAdmin(
            username='g503',
            classroom_name='G503'
        )
        classroom_admin1.set_password('123456')
        db.session.add(classroom_admin1)
        
        classroom_admin2 = ClassroomAdmin(
            username='g504',
            classroom_name='G504'
        )
        classroom_admin2.set_password('123456')
        db.session.add(classroom_admin2)
        
        # 添加示例学生
        # G503教室的学生
        students_g503 = [
            {'username': '20230101', 'name': '张三', 'class_name': '高一(1)班'},
            {'username': '20230102', 'name': '李四', 'class_name': '高一(1)班'},
            {'username': '20230103', 'name': '王五', 'class_name': '高一(2)班'},
        ]
        
        # G504教室的学生
        students_g504 = [
            {'username': '20230201', 'name': '赵六', 'class_name': '高一(3)班'},
            {'username': '20230202', 'name': '钱七', 'class_name': '高一(3)班'},
            {'username': '20230203', 'name': '孙八', 'class_name': '高一(4)班'},
        ]
        
        # 提交以获取教室管理员的ID
        db.session.flush()
        
        # 添加G503教室的学生
        for student_data in students_g503:
            student = User(
                username=student_data['username'],
                name=student_data['name'],
                class_name=student_data['class_name'],
                role='student',
                classroom_location='G503',
                classroom_id=classroom_admin1.id  # 关联到G503教室管理员
            )
            student.set_password('123456')  # 默认密码
            db.session.add(student)
        
        # 添加G504教室的学生
        for student_data in students_g504:
            student = User(
                username=student_data['username'],
                name=student_data['name'],
                class_name=student_data['class_name'],
                role='student',
                classroom_location='G504',
                classroom_id=classroom_admin2.id  # 关联到G504教室管理员
            )
            student.set_password('123456')  # 默认密码
            db.session.add(student)
        
        db.session.commit()
        print("数据库重置完成！")
        print("管理员账号: admin / admin123")
        print("教室管理员账号1: g503 / 123456")
        print("教室管理员账号2: g504 / 123456")
        print("学生账号: 200301xx / 123456")

if __name__ == "__main__":
    reset_database() 