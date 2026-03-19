"""文件分块接收服务"""
import os
import json
import base64
from pathlib import Path
from datetime import datetime

class FileReceiver:
    """接收 Worker 上传的文件分块"""
    
    def __init__(self, upload_dir="/tmp/uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        # 任务文件信息：{task_id: {"chunks": {}, "total": 0, "file_path": ""}}
        self.tasks = {}
    
    def receive_chunk(self, task_id, chunk_id, total_chunks, data):
        """接收文件分块"""
        if task_id not in self.tasks:
            self.tasks[task_id] = {
                "chunks": {},
                "total": total_chunks,
                "file_path": str(self.upload_dir / f"{task_id}.bin")
            }
        
        task = self.tasks[task_id]
        task["chunks"][chunk_id] = data
        
        print(f"📥 接收分块：{task_id} [{chunk_id+1}/{total_chunks}]")
        
        # 检查是否接收完成
        if len(task["chunks"]) == total_chunks:
            return self.assemble_file(task_id)
        
        return None
    
    def assemble_file(self, task_id):
        """组装完整文件"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        
        try:
            # 按顺序组装分块
            with open(task["file_path"], 'wb') as f:
                for chunk_id in range(task["total"]):
                    if chunk_id not in task["chunks"]:
                        print(f"❌ 缺少分块：{chunk_id}")
                        return None
                    
                    chunk_data = base64.b64decode(task["chunks"][chunk_id])
                    f.write(chunk_data)
            
            file_size = os.path.getsize(task["file_path"])
            print(f"✅ 文件组装完成：{task['file_path']} ({file_size/1024/1024:.2f}MB)")
            
            # 清理内存
            del self.tasks[task_id]
            
            return task["file_path"]
        except Exception as e:
            print(f"❌ 文件组装失败：{e}")
            return None

# 全局实例
file_receiver = FileReceiver()
