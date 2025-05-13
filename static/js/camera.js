document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const captureBtn = document.getElementById('capture-btn');
    const downloadBtn = document.getElementById('download-btn');
    const watermark = document.getElementById('watermark');
    const watermarkText = document.getElementById('watermark-text');
    const watermarkTime = document.getElementById('watermark-time');
    const watermarkInput = document.getElementById('watermark-input');
    const watermarkPosition = document.getElementById('watermark-position');
    const watermarkColor = document.getElementById('watermark-color');
    
    // 设置画布尺寸（初始值，稍后会根据视频尺寸调整）
    const context = canvas.getContext('2d');
    let stream = null;
    
    // 更新水印时间的函数
    function updateWatermarkTime() {
        const now = new Date();
        const formattedDate = now.getFullYear() + '/' + 
                            ('0' + (now.getMonth() + 1)).slice(-2) + '/' + 
                            ('0' + now.getDate()).slice(-2) + ' ' +
                            ('0' + now.getHours()).slice(-2) + ':' + 
                            ('0' + now.getMinutes()).slice(-2) + ':' + 
                            ('0' + now.getSeconds()).slice(-2);
        watermarkTime.textContent = formattedDate;
    }
    
    // 每秒更新一次水印时间
    updateWatermarkTime();
    setInterval(updateWatermarkTime, 1000);
    
    // 检查是否支持MediaDevices API
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('您的浏览器不支持访问摄像头，请尝试使用Chrome、Firefox或Safari最新版本');
        return;
    }
    
    // 访问摄像头
    async function setupCamera() {
        try {
            // 尝试使用环境摄像头（通常是后置摄像头）和用户摄像头（前置摄像头）
            const constraints = {
                video: { 
                    facingMode: { ideal: 'environment' }, // 优先使用后置摄像头
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                },
                audio: false
            };
            
            stream = await navigator.mediaDevices.getUserMedia(constraints);
            video.srcObject = stream;
            
            return new Promise((resolve) => {
                video.onloadedmetadata = () => {
                    // 设置Canvas大小与视频一致
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    resolve();
                };
            });
        } catch (error) {
            console.error('访问摄像头失败:', error);
            
            // 如果后置摄像头访问失败，尝试使用前置摄像头
            try {
                const constraints = {
                    video: { 
                        facingMode: 'user',
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    },
                    audio: false
                };
                
                stream = await navigator.mediaDevices.getUserMedia(constraints);
                video.srcObject = stream;
                
                return new Promise((resolve) => {
                    video.onloadedmetadata = () => {
                        canvas.width = video.videoWidth;
                        canvas.height = video.videoHeight;
                        resolve();
                    };
                });
            } catch (secondError) {
                console.error('前置摄像头也无法访问:', secondError);
                alert('无法访问摄像头。请确保您已授予摄像头权限，并且您的设备有可用的摄像头。');
            }
        }
    }
    
    // 应用水印位置
    function applyWatermarkPosition() {
        // 移除所有位置类
        watermark.classList.remove('top-left', 'top-right', 'bottom-left', 'bottom-right', 'center');
        // 添加选择的位置类
        watermark.classList.add(watermarkPosition.value);
    }
    
    // 应用水印颜色
    function applyWatermarkColor() {
        watermark.style.color = watermarkColor.value;
    }
    
    // 拍照功能
    function capturePhoto() {
        if (!stream) return;
        
        // 绘制视频帧到Canvas
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // 添加水印到图像
        const watermarkContent = watermarkInput.value + ' ' + watermarkTime.textContent;
        context.font = '16px Arial';
        context.fillStyle = watermarkColor.value;
        
        // 根据水印位置绘制
        const position = watermarkPosition.value;
        const padding = 20;
        const textWidth = context.measureText(watermarkContent).width;
        
        let x, y;
        
        switch (position) {
            case 'top-left':
                x = padding;
                y = padding + 16; // 16px是字体大小
                break;
            case 'top-right':
                x = canvas.width - textWidth - padding;
                y = padding + 16;
                break;
            case 'bottom-left':
                x = padding;
                y = canvas.height - padding;
                break;
            case 'bottom-right':
                x = canvas.width - textWidth - padding;
                y = canvas.height - padding;
                break;
            case 'center':
                x = (canvas.width - textWidth) / 2;
                y = canvas.height / 2;
                break;
        }
        
        // 添加半透明背景使水印更清晰
        context.fillStyle = 'rgba(0, 0, 0, 0.3)';
        context.fillRect(x - 5, y - 16, textWidth + 10, 22);
        
        // 绘制文本
        context.fillStyle = watermarkColor.value;
        context.fillText(watermarkContent, x, y);
        
        // 启用下载按钮
        downloadBtn.disabled = false;
    }
    
    // 下载照片
    function downloadPhoto() {
        if (!canvas.toDataURL) return;
        
        const dataURL = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        
        link.href = dataURL;
        link.download = `photo-${timestamp}.png`;
        link.click();
    }
    
    // 添加摄像头切换功能
    let frontCamera = false;
    function toggleCamera() {
        if (stream) {
            // 停止当前摄像头
            stream.getTracks().forEach(track => track.stop());
            
            // 切换摄像头
            frontCamera = !frontCamera;
            
            // 根据选择的摄像头设置constraints
            const constraints = {
                video: {
                    facingMode: frontCamera ? 'user' : 'environment',
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                },
                audio: false
            };
            
            // 重新获取摄像头
            navigator.mediaDevices.getUserMedia(constraints)
                .then(newStream => {
                    stream = newStream;
                    video.srcObject = stream;
                })
                .catch(error => {
                    console.error('切换摄像头失败:', error);
                    alert('切换摄像头失败，请确保您的设备有多个可用的摄像头。');
                    // 切换回原来的设置
                    frontCamera = !frontCamera;
                });
        }
    }
    
    // 添加摄像头切换按钮
    const toggleBtn = document.createElement('button');
    toggleBtn.id = 'toggle-camera';
    toggleBtn.textContent = '切换摄像头';
    toggleBtn.addEventListener('click', toggleCamera);
    
    // 将按钮添加到控制区域
    const controls = document.querySelector('.controls');
    controls.appendChild(toggleBtn);
    
    // 事件监听器
    watermarkInput.addEventListener('input', function() {
        watermarkText.textContent = this.value;
    });
    
    watermarkPosition.addEventListener('change', applyWatermarkPosition);
    watermarkColor.addEventListener('input', applyWatermarkColor);
    captureBtn.addEventListener('click', capturePhoto);
    downloadBtn.addEventListener('click', downloadPhoto);
    
    // 初始化
    setupCamera().then(() => {
        // 初始应用水印位置和颜色
        applyWatermarkPosition();
        applyWatermarkColor();
        // 初始禁用下载按钮，直到拍照后启用
        downloadBtn.disabled = true;
    });
}); 