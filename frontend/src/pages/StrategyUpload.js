/** 策略上传页面 */

import React, { useState } from 'react';
import { Card, Upload, Button, Input, message, Progress, Steps } from 'antd';
import { UploadOutlined, CloudUploadOutlined } from '@ant-design/icons';
import axios from 'axios';

const { TextArea } = Input;

function StrategyUpload() {
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [currentStage, setCurrentStage] = useState(0);
    const [strategyName, setStrategyName] = useState('');
    const [description, setDescription] = useState('');
    const [fileList, setFileList] = useState([]);

    const uploadProps = {
        onRemove: (file) => {
            setFileList([]);
        },
        beforeUpload: (file) => {
            setFileList([file]);
            return false; // 阻止自动上传
        },
        fileList,
        accept: '.zip'
    };

    const handleUpload = async () => {
        if (!strategyName) {
            message.error('请输入策略名称');
            return;
        }
        if (fileList.length === 0) {
            message.error('请选择策略包文件');
            return;
        }

        setUploading(true);
        setProgress(0);
        setCurrentStage(0);

        try {
            const formData = new FormData();
            formData.append('file', fileList[0]);
            formData.append('name', strategyName);
            formData.append('description', description);

            // 阶段 1: 上传
            setCurrentStage(0);
            setProgress(30);
            
            const uploadRes = await axios.post('/api/strategy/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            if (uploadRes.data.success) {
                // 阶段 2: 验证
                setCurrentStage(1);
                setProgress(60);
                
                const strategyId = uploadRes.data.data.strategy_id;
                
                // 阶段 3: 执行 Pipeline
                setCurrentStage(2);
                setProgress(90);
                
                message.success('策略上传成功！');
                setProgress(100);
                setUploading(false);
                
                // 重置表单
                setStrategyName('');
                setDescription('');
                setFileList([]);
            }
        } catch (error) {
            message.error('上传失败：' + error.message);
            setUploading(false);
        }
    };

    return (
        <div>
            <h2><CloudUploadOutlined /> 策略上传</h2>

            <Card title="上传策略包" style={{ marginBottom: 24 }}>
                <div style={{ marginBottom: 16 }}>
                    <Input
                        placeholder="策略名称 (例如：neo/v4_rsi_vol)"
                        value={strategyName}
                        onChange={(e) => setStrategyName(e.target.value)}
                        style={{ marginBottom: 16 }}
                    />
                    <TextArea
                        placeholder="策略描述 (可选)"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        rows={4}
                        style={{ marginBottom: 16 }}
                    />
                    <Upload {...uploadProps}>
                        <Button icon={<UploadOutlined />}>选择策略包 (.zip)</Button>
                    </Upload>
                </div>

                <Button
                    type="primary"
                    onClick={handleUpload}
                    loading={uploading}
                    disabled={fileList.length === 0 || !strategyName}
                >
                    上传并执行 Pipeline
                </Button>
            </Card>

            {uploading && (
                <Card title="执行进度">
                    <Steps
                        current={currentStage}
                        items={[
                            { title: '上传策略包', description: '上传 ZIP 文件' },
                            { title: '验证策略', description: '检查文件结构' },
                            { title: '执行 Pipeline', description: '训练 → 回测 → 调优' }
                        ]}
                        style={{ marginBottom: 24 }}
                    />
                    <Progress percent={progress} />
                </Card>
            )}

            <Card title="策略包要求">
                <h4>必需文件:</h4>
                <ul>
                    <li>config.json - 策略配置</li>
                </ul>
                <h4>可选文件 (Pipeline 脚本):</h4>
                <ul>
                    <li>train.py - 自定义训练脚本</li>
                    <li>backtest.py - 自定义回测脚本</li>
                    <li>optimize.py - 自定义调优脚本</li>
                </ul>
                <h4>可选目录:</h4>
                <ul>
                    <li>data/ - 自定义数据</li>
                    <li>features/ - 自定义特征工程</li>
                    <li>models/ - 预训练模型</li>
                </ul>
            </Card>
        </div>
    );
}

export default StrategyUpload;
