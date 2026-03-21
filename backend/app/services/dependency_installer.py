"""依赖安装服务 - 逐个下发依赖包，实时观察安装进度"""
import asyncio
import time
from typing import List, Optional
from app.services.task_manager import task_manager

class DependencyInstaller:
    """依赖逐个安装管理器"""
    
    def __init__(self):
        # 当前正在安装的队列：{worker_id: current_task_id}
        self.installing: dict = {}
        # 待安装队列：{worker_id: [package1, package2, ...]}
        self.queues: dict = {}
        # 安装历史：{worker_id: [{package, status, source, timestamp}]}
        self.history: dict = {}
    
    def add_packages(self, worker_id: str, packages: List[str], prefix: str = "install"):
        """添加待安装包到队列"""
        if worker_id not in self.queues:
            self.queues[worker_id] = []
            self.history[worker_id] = []
        
        for pkg in packages:
            task_id = f"{prefix}_{pkg.replace('-', '_').replace('.', '_')}_{int(time.time() * 1000)}"
            self.queues[worker_id].append({
                "package": pkg,
                "task_id": task_id
            })
        
        print(f"📦 添加 {len(packages)} 个包到 {worker_id} 的安装队列")
        return len(packages)
    
    async def start_installation(self, worker_id: str):
        """开始安装队列中的包 (逐个)"""
        if worker_id not in self.queues or not self.queues[worker_id]:
            print(f"⚠️ {worker_id} 没有待安装的包")
            return
        
        if worker_id in self.installing:
            print(f"⚠️ {worker_id} 已经在安装中")
            return
        
        self.installing[worker_id] = None
        
        print(f"🚀 开始为 {worker_id} 逐个安装包")
        
        while self.queues[worker_id]:
            # 取出下一个包
            pkg_info = self.queues[worker_id].pop(0)
            package = pkg_info["package"]
            task_id = pkg_info["task_id"]
            
            self.installing[worker_id] = task_id
            
            # 创建任务
            task_manager.create_task(
                task_id=task_id,
                task_type="install_single",
                worker_id=worker_id,
                data={"package": package}
            )
            
            # 发送安装指令
            await self._send_install_command(worker_id, package, task_id)
            
            # 等待完成 (带超时)
            success = await self._wait_for_completion(task_id, timeout=300)
            
            # 记录历史
            self.history[worker_id].append({
                "package": package,
                "task_id": task_id,
                "status": "completed" if success else "failed",
                "timestamp": time.time()
            })
            
            if not success:
                print(f"❌ {package} 安装失败，停止后续安装")
                # 可以选择重试或调整策略
                # 这里选择停止，让用户决定下一步
                break
            
            print(f"✅ {package} 安装完成，继续下一个")
            
            # 短暂间隔，避免连续安装
            await asyncio.sleep(0.5)
        
        self.installing.pop(worker_id, None)
        print(f"🎉 {worker_id} 安装队列完成")
    
    async def _send_install_command(self, worker_id: str, package: str, task_id: str):
        """发送安装指令到 Worker"""
        if worker_id not in task_manager.workers:
            print(f"❌ Worker {worker_id} 不在线")
            return False
        
        ws = task_manager.workers[worker_id]
        message = {
            "type": "install_single",
            "data": {"package": package},
            "task_id": task_id
        }
        
        try:
            await ws.send_json(message)
            print(f"📤 发送安装指令：{package} → {worker_id}")
            return True
        except Exception as e:
            print(f"❌ 发送失败：{e}")
            return False
    
    async def _wait_for_completion(self, task_id: str, timeout: int = 300) -> bool:
        """等待任务完成"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            task = task_manager.get_task(task_id)
            
            if not task:
                await asyncio.sleep(0.5)
                continue
            
            if task["status"] == "completed":
                return True
            
            if task["status"] == "failed":
                print(f"❌ 任务失败：{task_id} - {task.get('error', 'unknown')}")
                return False
            
            await asyncio.sleep(0.5)
        
        # 超时
        task_manager.fail_task(task_id, f"安装超时 ({timeout}秒)")
        return False
    
    def get_queue_status(self, worker_id: str) -> dict:
        """获取队列状态"""
        return {
            "worker_id": worker_id,
            "installing": self.installing.get(worker_id),
            "pending": len(self.queues.get(worker_id, [])),
            "queue": self.queues.get(worker_id, []),
            "history": self.history.get(worker_id, [])[-10:]  # 最近 10 个
        }
    
    def get_history(self, worker_id: str, limit: int = 50) -> list:
        """获取安装历史"""
        history = self.history.get(worker_id, [])
        return history[-limit:]
    
    def clear_queue(self, worker_id: str):
        """清空安装队列"""
        if worker_id in self.queues:
            packages = self.queues[worker_id]
            self.queues[worker_id] = []
            print(f"🧹 清空 {worker_id} 的 {len(packages)} 个待安装包")
            return len(packages)
        return 0


# 全局实例
dependency_installer = DependencyInstaller()
