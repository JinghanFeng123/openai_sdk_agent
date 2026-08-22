import subprocess


# Bash 工具的实际执行函数
def execute_bash(command: str) -> str:
    try:
        # 执行命令，捕获标准输出和错误输出
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout + result.stderr
    except Exception as e:
        return f"执行出错: {str(e)}"
