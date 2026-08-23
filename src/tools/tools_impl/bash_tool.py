import subprocess


# 工具 schema 定义
tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_bash",
            "description": "在本地终端执行一条 bash 命令并返回输出结果",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的 bash 命令"}
                },
                "required": ["command"]
            }
        }
    }
]


# Bash 工具的实际执行函数
def execute_bash(command: str) -> str:
    try:
        # 执行命令，捕获标准输出和错误输出
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout + result.stderr
    except Exception as e:
        return f"执行出错: {str(e)}"
