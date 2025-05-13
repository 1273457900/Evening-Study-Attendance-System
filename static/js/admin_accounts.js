// 模态框实例
let adminModal;
let resetPasswordModal;

// 页面加载完成后初始化
$(document).ready(function() {
    // 初始化模态框 - 使用jQuery方式(Bootstrap 4)
    adminModal = $('#adminModal');
    resetPasswordModal = $('#resetPasswordModal');
    
    // 监听教室名称输入，自动生成账号
    $('#classroomName').on('input', function() {
        const username = $(this).val().toLowerCase().replace(/\s+/g, '');
        const usernameInput = $('#username');
        
        // 只有在用户未手动修改账号时才自动更新
        if(!usernameInput.data('userModified') || usernameInput.data('userModified') === 'false') {
            usernameInput.val(username);
        }
    });
    
    // 监听账号输入，标记为用户修改
    $('#username').on('input', function() {
        $(this).data('userModified', 'true');
    });
});

// 显示添加管理员模态框
function showAddAdminModal() {
    // 重置表单
    $('#modalTitle').text('添加教室管理员');
    $('#adminForm')[0].reset();
    $('#adminId').val('');
    $('#passwordGroup').show();
    
    // 重置用户修改标记
    $('#username').data('userModified', 'false');
    
    // 显示模态框
    adminModal.modal('show');
}

// 显示编辑管理员模态框
function showEditAdminModal(id, classroomName, username) {
    // 设置表单数据
    $('#modalTitle').text('编辑教室管理员');
    $('#adminId').val(id);
    $('#classroomName').val(classroomName);
    $('#username').val(username).data('userModified', 'true');
    $('#passwordGroup').hide();
    
    // 显示模态框
    adminModal.modal('show');
}

// 显示重置密码模态框
function showResetPasswordModal(id) {
    // 设置表单数据
    $('#resetAdminId').val(id);
    $('#resetPasswordForm')[0].reset();
    
    // 显示模态框
    resetPasswordModal.modal('show');
}

// 保存管理员信息
async function saveAdmin() {
    try {
        const formData = $('#adminForm').serializeArray();
        const data = {};
        
        // 转换表单数据为对象
        $.each(formData, function() {
            data[this.name] = this.value;
        });
        
        const adminId = data.admin_id;
        
        // 处理表单数据
        const payload = {
            classroom_name: data.classroom_name,
            username: data.username,
        };
        
        // 详细日志 - 所有表单数据
        console.log('原始表单数据:', formData);
        console.log('处理后的数据对象:', data);
        
        // 表单验证
        if (!payload.classroom_name || !payload.classroom_name.trim()) {
            throw new Error('请输入教室名称');
        }
        
        if (!payload.username || !payload.username.trim()) {
            throw new Error('请输入登录账号');
        }
        
        // 仅在新建时包含密码
        if (!adminId) {
            payload.password = data.password || '';
        }
        
        let url = '/api/admin/accounts';
        let method = 'POST';
        
        if (adminId) {
            url = `/api/admin/accounts/${adminId}`;
            method = 'PUT';
        }
        
        console.log(`正在发送${method}请求到: ${url}`);
        console.log('请求数据:', JSON.stringify(payload));
        
        // 获取CSRF令牌 (如果页面中有)
        const csrfToken = $('meta[name="csrf-token"]').attr('content');
        const headers = {
            'Content-Type': 'application/json',
        };
        
        // 如果存在CSRF令牌，添加到请求头
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
            console.log('已添加CSRF令牌到请求头');
        } else {
            console.warn('未找到CSRF令牌');
        }
        
        const response = await fetch(url, {
            method: method,
            headers: headers,
            body: JSON.stringify(payload),
            credentials: 'same-origin'  // 确保发送Cookie，包括CSRF令牌
        });
        
        console.log(`响应状态: ${response.status} ${response.statusText}`);
        console.log('响应头:', Object.fromEntries([...response.headers]));
        
        // 尝试解析响应数据，即使状态码不是200
        const responseText = await response.text();
        console.log(`响应数据原始文本: ${responseText}`);
        
        let result;
        try {
            if (responseText) {
                result = JSON.parse(responseText);
                console.log('解析后的响应数据:', result);
            } else {
                console.warn('响应内容为空');
                result = {};
            }
        } catch (e) {
            console.error(`无法解析响应JSON: ${e.message}`);
            result = { error: '响应格式错误或服务器内部错误' };
        }
        
        // 处理警告消息但仍然继续处理
        if (result.warning) {
            console.warn('服务器警告:', result.warning);
            showToast('warning', result.warning);
        }
        
        if (!response.ok) {
            throw new Error(result.error || `操作失败，HTTP状态码: ${response.status}`);
        }
        
        // 显示成功消息
        showToast('success', adminId ? '更新成功' : '添加成功');
        
        // 关闭模态框并刷新页面
        adminModal.modal('hide');
        setTimeout(() => location.reload(), 1000);
        
    } catch (error) {
        console.error('保存失败:', error);
        showToast('error', error.message);
    }
}

// 重置密码
async function resetPassword() {
    try {
        const formData = $('#resetPasswordForm').serializeArray();
        const data = {};
        
        // 转换表单数据为对象
        $.each(formData, function() {
            data[this.name] = this.value;
        });
        
        if (!data.admin_id) {
            throw new Error('未指定管理员账号');
        }
        
        const response = await fetch('/api/admin/accounts/reset-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.error || '重置密码失败');
        }
        
        // 显示成功消息
        showToast('success', '密码重置成功');
        
        // 关闭模态框
        resetPasswordModal.modal('hide');
        
    } catch (error) {
        console.error('重置密码失败:', error);
        showToast('error', error.message);
    }
}

// 切换账号状态
async function toggleAccountStatus(id, currentStatus) {
    if (!id) {
        showToast('error', '账号ID未指定');
        return;
    }
    
    if (!confirm(`确定要${currentStatus ? '禁用' : '启用'}该账号吗？`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/accounts/${id}/toggle-status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ is_active: !currentStatus })
        });
        
        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.error || '操作失败');
        }
        
        // 显示成功消息
        showToast('success', `账号${currentStatus ? '禁用' : '启用'}成功`);
        
        // 刷新页面
        setTimeout(() => location.reload(), 1000);
        
    } catch (error) {
        console.error('状态切换失败:', error);
        showToast('error', error.message);
    }
}

// 删除管理员账号
async function deleteAdmin(id, classroomName) {
    if (!id) {
        showToast('error', '账号ID未指定');
        return;
    }
    
    // 二次确认，提醒用户这是不可逆操作
    if (!confirm(`确定要删除教室 ${classroomName} 的管理员账号吗？\n\n此操作不可恢复，同时会解除该教室的所有学生关联。`)) {
        return;
    }
    
    try {
        // 获取CSRF令牌 (如果页面中有)
        const csrfToken = $('meta[name="csrf-token"]').attr('content');
        const headers = {
            'Content-Type': 'application/json',
        };
        
        // 如果存在CSRF令牌，添加到请求头
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
            console.log('已添加CSRF令牌到请求头');
        }
        
        const response = await fetch(`/api/admin/accounts/${id}`, {
            method: 'DELETE',
            headers: headers,
            credentials: 'same-origin'
        });
        
        console.log(`响应状态: ${response.status} ${response.statusText}`);
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || '删除失败');
        }
        
        // 显示成功消息
        showToast('success', result.message || '账号删除成功');
        console.log(`删除成功，影响的学生数: ${result.affected_students || 0}`);
        
        // 刷新页面
        setTimeout(() => location.reload(), 1000);
        
    } catch (error) {
        console.error('删除失败:', error);
        showToast('error', error.message);
    }
}

// 显示提示消息
function showToast(type, message) {
    // 判断是否存在toastr库
    if (typeof toastr !== 'undefined') {
        // 使用toastr显示消息
        switch (type) {
            case 'success':
                toastr.success(message);
                break;
            case 'error':
                toastr.error(message);
                break;
            case 'warning':
                toastr.warning(message);
                break;
            default:
                toastr.info(message);
                break;
        }
    } else {
        // 简单实现，使用alert
        let prefix = '';
        switch (type) {
            case 'error':
                prefix = '错误: ';
                break;
            case 'warning':
                prefix = '警告: ';
                break;
            case 'success':
                prefix = '成功: ';
                break;
        }
        alert(prefix + message);
    }
} 