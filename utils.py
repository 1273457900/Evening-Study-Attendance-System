import os
import pandas as pd
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from datetime import datetime
from models import User, AttendanceRecord, db, ClassroomAdmin, LeaveRecord
from werkzeug.security import generate_password_hash
from flask import current_app
from openpyxl.drawing.image import Image
import io
from PIL import Image as PILImage, ImageDraw, ImageFont
import textwrap

def generate_template():
    """生成Excel模板"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "学生名单模板"
    
    # 设置标题行
    headers = ["班级", "学号", "姓名", "初始密码", "教室位置"]
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
        ws.cell(row=1, column=col).font = Font(bold=True)
        ws.cell(row=1, column=col).alignment = Alignment(horizontal='center')
        ws.cell(row=1, column=col).fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
    
    # 添加一些示例数据
    example_data = [
        ["高一(1)班", "20230101", "张三", "password123", "G503"],
        ["高一(1)班", "20230102", "李四", "password123", "G503"],
        ["高一(2)班", "20230201", "王五", "password123", "G504"]
    ]
    
    for row, data in enumerate(example_data, 2):
        for col, value in enumerate(data, 1):
            ws.cell(row=row, column=col, value=value)
    
    # 调整列宽
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 15
    
    # 添加说明
    ws.cell(row=len(example_data) + 3, column=1, value="说明：")
    ws.cell(row=len(example_data) + 3, column=1).font = Font(bold=True)
    ws.cell(row=len(example_data) + 4, column=1, value="1. 班级: 请填写学生所在班级")
    ws.cell(row=len(example_data) + 5, column=1, value="2. 学号: 请填写学生学号，将作为登录用户名")
    ws.cell(row=len(example_data) + 6, column=1, value="3. 姓名: 请填写学生姓名")
    ws.cell(row=len(example_data) + 7, column=1, value="4. 初始密码: 学生首次登录的密码")
    ws.cell(row=len(example_data) + 8, column=1, value="5. 教室位置: 学生所在教室编号（如G503），用于关联到教室管理员")
    
    return wb

def import_students_from_excel(file_path):
    """从Excel文件导入学生名单"""
    try:
        df = pd.read_excel(file_path)
        
        # 验证数据格式
        required_columns = ["班级", "学号", "姓名", "初始密码"]
        for col in required_columns:
            if col not in df.columns:
                return False, f"Excel文件格式错误，缺少'{col}'列"
        
        # 开始导入学生数据
        imported_count = 0
        updated_count = 0
        for _, row in df.iterrows():
            class_name = str(row["班级"])
            student_id = str(row["学号"])
            name = str(row["姓名"])
            password = str(row["初始密码"])
            
            # 获取教室位置（如果有）
            classroom_location = str(row["教室位置"]) if "教室位置" in row and not pd.isna(row["教室位置"]) else None
            
            # 检查是否已存在该学生
            existing_user = User.query.filter_by(username=student_id).first()
            
            if existing_user:
                # 更新已存在的学生信息
                existing_user.name = name
                existing_user.class_name = class_name
                if classroom_location:
                    existing_user.classroom_location = classroom_location
                    # 查找对应教室的管理员并关联
                    admin = ClassroomAdmin.query.filter_by(classroom_name=classroom_location.upper()).first()
                    if admin:
                        existing_user.classroom_id = admin.id
                if password and password.strip():
                    existing_user.set_password(password)
                updated_count += 1
            else:
                # 创建新学生
                new_user = User(
                    username=student_id,
                    name=name,
                    class_name=class_name,
                    role="student",
                    classroom_location=classroom_location
                )
                # 查找对应教室的管理员并关联
                if classroom_location:
                    admin = ClassroomAdmin.query.filter_by(classroom_name=classroom_location.upper()).first()
                    if admin:
                        new_user.classroom_id = admin.id
                new_user.set_password(password)
                db.session.add(new_user)
                imported_count += 1
        
        db.session.commit()
        return True, f"成功导入{imported_count}名新学生，更新{updated_count}名已有学生信息"
    
    except Exception as e:
        db.session.rollback()
        return False, f"导入失败: {str(e)}"

def export_attendance_records(start_date, end_date, class_name=None, export_photos=True):
    """导出考勤记录到Excel，并根据选项导出相关照片"""
    try:
        # 查询考勤记录
        query = db.session.query(
            User.username, 
            db.func.coalesce(AttendanceRecord.student_name, User.name).label('name'), 
            db.func.coalesce(AttendanceRecord.class_name, User.class_name).label('class_name'),
            AttendanceRecord.date, 
            AttendanceRecord.sign_in_time,
            AttendanceRecord.leave_time,
            AttendanceRecord.return_time,
            AttendanceRecord.id.label('attendance_id'),
            User.id.label('student_id'),
            AttendanceRecord.sign_in_photo,
            AttendanceRecord.leave_photo,
            AttendanceRecord.return_photo
        ).join(
            AttendanceRecord, User.id == AttendanceRecord.student_id
        ).filter(
            AttendanceRecord.date.between(start_date, end_date),
            User.role == "student"
        )
        
        # 如果指定了班级，添加筛选条件
        if class_name:
            query = query.filter(User.class_name == class_name)
            
        # 按日期和班级排序
        records = query.order_by(AttendanceRecord.date, User.class_name, User.username).all()
        
        if not records:
            return None
        
        # 生成导出基础文件名（用于Excel和照片文件夹）
        if class_name:
            base_filename = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}-{class_name}-考勤记录"
        else:
            base_filename = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}-全部班级-考勤记录"
        
        # 导出路径
        export_base_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'exports')
        export_excel_path = os.path.join(export_base_dir, f"{base_filename}.xlsx")
        export_photos_dir = os.path.join(export_base_dir, f"{base_filename}_照片")
        
        # 确保导出目录存在
        os.makedirs(export_base_dir, exist_ok=True)
        
        # 如果需要导出照片，创建照片目录
        if export_photos:
            os.makedirs(export_photos_dir, exist_ok=True)
            
        # 创建Excel文件
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "考勤记录"
        
        # 设置表头 - 根据是否导出照片决定是否包含照片列
        base_headers = ["日期", "班级", "学号", "姓名", "签到时间", "暂离时间", "返回时间", "今日暂离次数", "今日暂离分钟数"]
        headers = base_headers.copy()
        
        # 添加照片列标题
        if export_photos:
            headers.append("签到照片")
            headers.append("暂离/返回照片")
            
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # 调整列宽
        for col in range(1, len(base_headers) + 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 15
        
        # 如果导出照片，设置照片列的宽度和行高
        if export_photos:
            # 照片列宽度设置宽一些
            ws.column_dimensions[openpyxl.utils.get_column_letter(len(base_headers) + 1)].width = 20
            ws.column_dimensions[openpyxl.utils.get_column_letter(len(base_headers) + 2)].width = 25
            
        # 写入数据并导出照片
        row = 2
        for record in records:
            student_folder_name = ""
            photo_paths = []
            
            # 如果需要导出照片，处理照片缓存
            if export_photos:
                # 为每个学生创建照片文件夹
                date_str = record.date.strftime('%Y%m%d')
                student_folder_name = f"{date_str}_{record.class_name}_{record.username}_{record.name}"
                student_photo_dir = os.path.join(export_photos_dir, student_folder_name)
                os.makedirs(student_photo_dir, exist_ok=True)
                
                # 设置行高（照片行需要更高一些）
                ws.row_dimensions[row].height = 100
            
            # 查询该学生的所有暂离记录
            leave_records = LeaveRecord.query.filter(
                LeaveRecord.student_id == record.student_id,
                LeaveRecord.attendance_id == record.attendance_id
            ).order_by(LeaveRecord.leave_time).all()
            
            # 计算暂离次数和分钟数
            leave_count = len(leave_records)
            total_minutes = 0
            
            # 处理暂离记录
            leave_return_photos = []
            for i, leave in enumerate(leave_records, 1):
                # 计算暂离时长
                if leave.leave_time and leave.return_time:
                    duration = (leave.return_time - leave.leave_time).total_seconds() / 60
                    total_minutes += duration
                
                # 如果需要导出照片，收集暂离和返回照片
                if export_photos:
                    # 处理暂离照片
                    if leave.leave_photo:
                        src_path = os.path.join(current_app.config['UPLOAD_FOLDER'], leave.leave_photo)
                        if os.path.exists(src_path):
                            # 保存照片文件到文件夹
                            dest_filename = f"暂离{i}_{leave.leave_time.strftime('%H%M%S')}.png" if leave.leave_time else f"暂离{i}.png"
                            dest_path = os.path.join(student_photo_dir, dest_filename)
                            try:
                                import shutil
                                shutil.copy2(src_path, dest_path)
                            except Exception as e:
                                current_app.logger.error(f"复制暂离照片失败: {str(e)}")
                            
                            # 添加到要在Excel中显示的照片集合
                            leave_return_photos.append({
                                'src_path': src_path,
                                'type': 'leave',
                                'index': i,
                                'time': leave.leave_time
                            })
                    
                    # 处理返回照片
                    if leave.return_photo:
                        src_path = os.path.join(current_app.config['UPLOAD_FOLDER'], leave.return_photo)
                        if os.path.exists(src_path):
                            # 保存照片文件到文件夹
                            dest_filename = f"返回{i}_{leave.return_time.strftime('%H%M%S')}.png" if leave.return_time else f"返回{i}.png"
                            dest_path = os.path.join(student_photo_dir, dest_filename)
                            try:
                                import shutil
                                shutil.copy2(src_path, dest_path)
                            except Exception as e:
                                current_app.logger.error(f"复制返回照片失败: {str(e)}")
                            
                            # 添加到要在Excel中显示的照片集合
                            leave_return_photos.append({
                                'src_path': src_path,
                                'type': 'return',
                                'index': i,
                                'time': leave.return_time
                            })
            
            # 填充数据
            ws.cell(row=row, column=1).value = record.date.strftime('%Y-%m-%d')
            ws.cell(row=row, column=2).value = record.class_name
            ws.cell(row=row, column=3).value = record.username
            ws.cell(row=row, column=4).value = record.name
            ws.cell(row=row, column=5).value = record.sign_in_time.strftime('%H:%M:%S') if record.sign_in_time else "未签到"
            ws.cell(row=row, column=6).value = record.leave_time.strftime('%H:%M:%S') if record.leave_time else "-"
            ws.cell(row=row, column=7).value = record.return_time.strftime('%H:%M:%S') if record.return_time else "-"
            ws.cell(row=row, column=8).value = leave_count
            ws.cell(row=row, column=9).value = round(total_minutes)
            
            # 如果导出照片，插入照片到Excel单元格
            if export_photos:
                # 处理签到照片
                if record.sign_in_photo:
                    sign_in_path = os.path.join(current_app.config['UPLOAD_FOLDER'], record.sign_in_photo)
                    if os.path.exists(sign_in_path):
                        # 保存照片文件到文件夹
                        dest_filename = f"签到_{record.sign_in_time.strftime('%H%M%S')}.png" if record.sign_in_time else "签到.png"
                        dest_path = os.path.join(student_photo_dir, dest_filename)
                        try:
                            import shutil
                            shutil.copy2(sign_in_path, dest_path)
                        except Exception as e:
                            current_app.logger.error(f"复制签到照片失败: {str(e)}")
                        
                        try:
                            # 使用PIL调整图片大小（照片在拍摄时已添加水印）
                            img = PILImage.open(sign_in_path)
                            
                            # 调整大小用于嵌入Excel，使用高质量调整
                            width_height = max(150, int(min(img.width, img.height) / 4))  # 更大的尺寸
                            img_resized = img.resize((width_height, width_height), PILImage.LANCZOS)
                            
                            # 保存调整后的图片到临时文件，使用高质量设置
                            temp_path = os.path.join(student_photo_dir, "temp_sign_in.png")
                            img_resized.save(temp_path, quality=100, optimize=True)
                            
                            # 将图片插入到Excel
                            img = Image(temp_path)
                            cell_address = f"{openpyxl.utils.get_column_letter(len(base_headers) + 1)}{row}"
                            ws.add_image(img, cell_address)
                        except Exception as e:
                            current_app.logger.error(f"插入签到照片失败: {str(e)}")
                            ws.cell(row=row, column=len(base_headers) + 1).value = "照片处理失败"
                
                # 处理暂离/返回照片组合
                if leave_return_photos:
                    try:
                        # 创建组合图片（最多显示3个暂离记录的照片）
                        max_display = min(3, len(leave_return_photos))
                        displayed_photos = leave_return_photos[:max_display]
                        
                        # 计算组合图片大小
                        photo_size = 150  # 单个照片尺寸
                        combined_width = photo_size * max_display
                        combined_height = photo_size
                        
                        # 创建空白画布
                        combined_img = PILImage.new('RGB', (combined_width, combined_height), color=(255, 255, 255))
                        
                        # 添加每张照片到画布
                        for idx, photo_info in enumerate(displayed_photos):
                            try:
                                # 照片在拍摄时已添加水印，只需调整大小
                                img = PILImage.open(photo_info['src_path'])
                                img_resized = img.resize((photo_size, photo_size), PILImage.LANCZOS)
                                combined_img.paste(img_resized, (idx * photo_size, 0))
                                
                                # 添加标签（暂离/返回）
                                draw = ImageDraw.Draw(combined_img)
                                label = f"{photo_info['type']}_{photo_info['index']}"
                                # 尝试获取默认字体，如果失败则忽略文字绘制
                                try:
                                    # 在Windows上可能需要系统字体路径
                                    font = ImageFont.truetype("arial.ttf", 14)
                                    draw.text((idx * photo_size + 5, 5), label, fill="white", font=font)
                                except:
                                    pass  # 字体加载失败时忽略文字绘制
                            except Exception as e:
                                current_app.logger.error(f"处理单个照片失败: {str(e)}")
                                continue
                        
                        # 保存组合图片
                        temp_path = os.path.join(student_photo_dir, "temp_combined.png")
                        combined_img.save(temp_path, quality=95, optimize=True)
                        
                        # 将组合图片插入到Excel
                        img = Image(temp_path)
                        cell_address = f"{openpyxl.utils.get_column_letter(len(base_headers) + 2)}{row}"
                        ws.add_image(img, cell_address)
                        
                        # 如果有更多照片未显示，在单元格中添加说明
                        if len(leave_return_photos) > max_display:
                            cell = ws.cell(row=row, column=len(base_headers) + 2)
                            cell.comment = openpyxl.comments.Comment(
                                f"还有{len(leave_return_photos) - max_display}张照片未显示，请查看照片文件夹", "系统"
                            )
                    except Exception as e:
                        current_app.logger.error(f"创建暂离/返回照片组合失败: {str(e)}")
                        ws.cell(row=row, column=len(base_headers) + 2).value = "照片处理失败"
                        
            row += 1
        
        # 保存Excel文件
        wb.save(export_excel_path)
        
        # 返回导出文件夹名称（包含Excel和照片文件夹的共同父文件夹）
        return f"{base_filename}.xlsx"
    except Exception as e:
        current_app.logger.error(f"导出考勤记录失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return None

def generate_admin_template():
    """生成教室管理员账号导入模板"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "教室管理员账号"
    
    # 设置表头
    headers = ['教室名称', '登录账号', '初始密码', '备注']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="E6E6E6", end_color="E6E6E6", fill_type="solid")
        cell.alignment = Alignment(horizontal='center')
    
    # 设置示例数据
    example_data = [
        ['G503', 'g503', '123456', '示例数据，导入时请删除'],
        ['G504', 'g504', '123456', '密码不填则默认为123456'],
        ['G505', 'g505_admin', '123456', '账号可自定义，不必与教室名称完全一致'],
    ]
    
    for row_idx, row_data in enumerate(example_data, 2):
        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = value
            cell.alignment = Alignment(horizontal='center')
    
    # 添加说明
    notes_row = len(example_data) + 3
    ws.cell(row=notes_row, column=1, value="说明：").font = Font(bold=True)
    ws.cell(row=notes_row+1, column=1, value="1. 教室名称: 请填写教室的标准名称，如G503")
    ws.cell(row=notes_row+2, column=1, value="2. 登录账号: 可以是教室名称的小写或其他自定义账号")
    ws.cell(row=notes_row+3, column=1, value="3. 初始密码: 不填则默认为123456")
    ws.cell(row=notes_row+4, column=1, value="4. 学生将根据'教室位置'字段关联到对应教室管理员")
    ws.cell(row=notes_row+5, column=1, value="5. 请确保教室名称与学生导入模板中的'教室位置'字段匹配")
    
    # 调整列宽
    for col in ['A', 'B', 'C', 'D']:
        ws.column_dimensions[col].width = 20
    
    return wb

def import_admin_accounts(file_path):
    """从Excel文件导入教室管理员账号"""
    try:
        df = pd.read_excel(file_path)
        required_columns = ['教室名称', '登录账号']
        
        # 检查必要列是否存在
        if not all(col in df.columns for col in required_columns):
            return False, "Excel文件格式错误，请使用正确的模板"
        
        success_count = 0
        error_messages = []
        
        for index, row in df.iterrows():
            try:
                # 跳过空行
                if pd.isna(row['教室名称']) or pd.isna(row['登录账号']):
                    continue
                    
                classroom_name = str(row['教室名称']).strip().upper()
                username = str(row['登录账号']).strip().lower()
                password = str(row['初始密码']).strip() if not pd.isna(row['初始密码']) else '123456'
                
                # 检查账号是否已存在
                existing_admin = ClassroomAdmin.query.filter_by(username=username).first()
                if existing_admin:
                    error_messages.append(f"账号 {username} 已存在")
                    continue
                
                # 创建新账号
                admin = ClassroomAdmin(
                    username=username,
                    classroom_name=classroom_name,
                )
                admin.set_password(password)  # 此方法会同时设置密码哈希和明文
                db.session.add(admin)
                db.session.commit()  # 先提交以获取admin.id
                
                # 关联已有学生
                students = User.query.filter_by(classroom_location=classroom_name).all()
                for student in students:
                    student.classroom_id = admin.id
                
                success_count += 1
                
            except Exception as e:
                error_messages.append(f"第 {index+2} 行导入失败：{str(e)}")
        
        db.session.commit()
        
        # 生成结果消息
        message = f"成功导入 {success_count} 个账号。"
        if error_messages:
            message += f"\n导入错误：\n" + "\n".join(error_messages)
        
        return True, message
        
    except Exception as e:
        return False, f"导入失败：{str(e)}"

def export_admin_accounts():
    """导出教室管理员账号列表"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "教室管理员账号"
    
    # 设置表头
    headers = ['教室名称', '登录账号', '密码', '状态', '创建时间', '最后登录时间']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="E6E6E6", end_color="E6E6E6", fill_type="solid")
        cell.alignment = Alignment(horizontal='center')
    
    # 获取所有账号
    admins = ClassroomAdmin.query.order_by(ClassroomAdmin.classroom_name).all()
    
    # 写入数据
    for row_idx, admin in enumerate(admins, 2):
        ws.cell(row=row_idx, column=1, value=admin.classroom_name)
        ws.cell(row=row_idx, column=2, value=admin.username)
        ws.cell(row=row_idx, column=3, value=admin.password_text or '******')
        ws.cell(row=row_idx, column=4, value='启用' if admin.is_active else '禁用')
        ws.cell(row=row_idx, column=5, value=admin.created_at.strftime('%Y-%m-%d %H:%M:%S'))
        ws.cell(row=row_idx, column=6, value=admin.last_login.strftime('%Y-%m-%d %H:%M:%S') if admin.last_login else '未登录')
    
    # 调整列宽
    for col in ['A', 'B', 'C', 'D', 'E', 'F']:
        ws.column_dimensions[col].width = 20
    
    return wb

def add_timestamp_watermark(img, timestamp_text, position='bottom', no_background=False):
    """给图片添加时间水印
    
    Args:
        img: PIL Image对象
        timestamp_text: 时间文本
        position: 水印位置，可选 'top', 'bottom', 'topleft', 'topright', 'bottomleft', 'bottomright'
        no_background: 是否不添加背景底纹
    
    Returns:
        添加水印后的PIL Image对象
    """
    # 创建可编辑的图像副本
    img_with_watermark = img.copy()
    draw = ImageDraw.Draw(img_with_watermark)
    
    # 字体大小根据图片尺寸调整
    font_size = max(int(min(img.width, img.height) / 10), 20)  # 最小字体大小提高到20
    
    # 尝试加载适合中文显示的字体
    font = None
    try:
        # 尝试Windows常见中文字体
        windows_fonts = ['simhei.ttf', 'simsun.ttc', 'msyh.ttc', 'simkai.ttf']
        for font_name in windows_fonts:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except:
                continue
            
        # 如果Windows字体都失败，尝试常见Linux中文字体
        if font is None:
            linux_fonts = [
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
            ]
            for font_path in linux_fonts:
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except:
                    continue
    except:
        pass
    
    # 如果无法加载系统字体，使用默认字体
    if font is None:
        try:
            font = ImageFont.load_default()
            # 默认字体不支持中文，记录警告
            current_app.logger.warning("无法加载支持中文的字体，水印可能无法正确显示中文")
        except:
            # 如果出错，跳过绘制水印
            current_app.logger.error("无法加载任何字体，跳过水印添加")
            return img
    
    # 计算文本大小，用于定位
    # 使用textwrap分行处理
    lines = timestamp_text.split('\n')
    
    # 如果使用默认字体，尝试测量文本长度
    try:
        line_widths = [draw.textlength(line, font=font) for line in lines]
        max_line_width = max(line_widths)
    except:
        # 如果无法测量，使用估计值
        max_line_width = max(len(line) * font_size * 0.6 for line in lines)
    
    line_height = font_size + 6  # 增加行间距以提高可读性
    text_height = line_height * len(lines)
    
    # 添加半透明背景以提高可读性
    margin = 15  # 增加文本周围的边距以提高可读性
    
    # 根据position参数确定水印位置
    if position == 'top':
        rect_x0 = (img.width - max_line_width) // 2 - margin
        rect_y0 = margin
    elif position == 'bottom':
        rect_x0 = (img.width - max_line_width) // 2 - margin
        rect_y0 = img.height - text_height - 2 * margin
    elif position == 'topleft':
        rect_x0 = margin
        rect_y0 = margin
    elif position == 'topright':
        rect_x0 = img.width - max_line_width - 2 * margin
        rect_y0 = margin
    elif position == 'bottomleft':
        rect_x0 = margin
        rect_y0 = img.height - text_height - 2 * margin
    elif position == 'bottomright':
        rect_x0 = img.width - max_line_width - 2 * margin
        rect_y0 = img.height - text_height - 2 * margin
    else:  # 默认为底部
        rect_x0 = (img.width - max_line_width) // 2 - margin
        rect_y0 = img.height - text_height - 2 * margin
    
    rect_x1 = rect_x0 + max_line_width + 2 * margin
    rect_y1 = rect_y0 + text_height + margin
    
    # 绘制半透明背景，除非no_background=True
    if not no_background:
        draw.rectangle([rect_x0, rect_y0, rect_x1, rect_y1], fill=(0, 0, 0, 180))
    
    # 绘制文本
    y = rect_y0 + margin // 2
    for line in lines:
        # 水平居中对齐每一行文本
        x = rect_x0 + margin
        if position in ['top', 'bottom']:
            try:
                x = rect_x0 + (rect_x1 - rect_x0 - draw.textlength(line, font=font)) // 2
            except:
                x = rect_x0 + margin  # 如果无法测量，使用边距
        
        # 为文字添加描边效果，增强可读性
        # 描边颜色：如果不使用背景，则使用黑色描边；如果使用背景，则使用黑色描边
        stroke_color = (0, 0, 0)
        
        # 描边效果：描边宽度增加到4个像素，确保在任何背景下都清晰可见
        for offset_x in range(-2, 3):
            for offset_y in range(-2, 3):
                # 跳过中心点，中心点将被实际文字覆盖
                if offset_x == 0 and offset_y == 0:
                    continue
                # 计算距离，只绘制距离中心2个像素以内的点
                if abs(offset_x) + abs(offset_y) <= 3:
                    draw.text((x + offset_x, y + offset_y), line, fill=stroke_color, font=font)
        
        # 绘制文字本身
        draw.text((x, y), line, fill=(255, 255, 255), font=font)
        y += line_height
    
    return img_with_watermark 