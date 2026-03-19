#!/usr/bin/env python3
"""
向 Worker 发送指令
用法：python send_instruction.py <command_type> [args...]
"""

import json
from pathlib import Path
from datetime import datetime

INSTRUCTIONS_FILE = Path("/root/.openclaw/workspace/projects/trading-system-release/worker/instructions.json")

def send_instruction(cmd_type, **kwargs):
    """发送指令到指令队列"""
    
    # 读取现有指令
    if INSTRUCTIONS_FILE.exists():
        with open(INSTRUCTIONS_FILE) as f:
            data = json.load(f)
    else:
        data = {"instructions": []}
    
    # 添加新指令
    instruction = {
        "id": f"cmd_{int(datetime.now().timestamp())}",
        "type": cmd_type,
        "timestamp": datetime.now().isoformat(),
        **kwargs
    }
    
    data["instructions"].append(instruction)
    data["updated_at"] = datetime.now().isoformat()
    
    # 保持最近 10 条指令
    data["instructions"] = data["instructions"][-10:]
    
    # 写入文件
    with open(INSTRUCTIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 指令已发送：{instruction['id']}")
    print(f"   类型：{cmd_type}")
    print(f"   内容：{kwargs}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法：python send_instruction.py <command_type> [args...]")
        print("")
        print("示例:")
        print("  python send_instruction.py install_packages packages='[\"torch\"]'")
        print("  python send_instruction.py assign_task task='{\"id\":\"task_001\",\"type\":\"train_intent\"}'")
        sys.exit(1)
    
    cmd_type = sys.argv[1]
    send_instruction(cmd_type)
