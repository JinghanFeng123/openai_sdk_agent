from typing import Literal

Status = Literal["pending", "in_progress", "completed"]

STATUS_ICONS = {
    "pending": "⬜",
    "in_progress": "🔄",
    "completed": "✅",
}

# 工具 schema 定义
tools = [
    {
        "type": "function",
        "function": {
            "name": "todo_write",
            "description": "创建待办事项清单。当需要执行复杂任务时，先将任务拆解为多个子任务，生成清单展示给用户。",
            "parameters": {
                "type": "object",
                "properties": {
                    "todos": {
                        "type": "array",
                        "description": "待办事项列表，每个事项包含 id、content 和 status",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer", "description": "任务 ID（自动生成，可以不填）"},
                                "content": {"type": "string", "description": "任务内容描述"},
                                "status": {
                                    "type": "string",
                                    "enum": ["pending", "in_progress", "completed"],
                                    "description": "任务状态：pending（待办）、in_progress（进行中）、completed（已完成）"
                                }
                            },
                            "required": ["content"]
                        }
                    }
                },
                "required": ["todos"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "todo_update",
            "description": "更新待办事项的状态",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {"type": "integer", "description": "要更新的任务 ID"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "completed"],
                        "description": "新的任务状态"
                    }
                },
                "required": ["todo_id", "status"]
            }
        }
    }
]


class TodoManager:
    """纯内存的 to——do 状态管理器"""

    def __init__(self):
        self._todos: list[dict] = []
        self._next_id: int = 1

    def create_todos(self, todos: list[dict]) -> str:
        """创建或覆盖任务清单，为每项分配自增 id"""
        self._todos = []
        self._next_id = 1

        for todo in todos:
            self._todos.append({
                "id": self._next_id,
                "content": todo.get("content", "未命名任务"),
                "status": todo.get("status", "pending"),
            })
            self._next_id += 1

        return self.format_todos()

    def update_status(self, todo_id: int, status: Status) -> str:
        """更新指定任务的状态"""
        for todo in self._todos:
            if todo["id"] == todo_id:
                old = todo["status"]
                todo["status"] = status
                return f"任务 #{todo_id} 状态已更新: {old} → {status}\n\n{self.format_todos()}"
        return f"未找到 id 为 {todo_id} 的任务"

    def get_todos(self) -> list[dict]:
        """返回当前任务清单的副本"""
        return list(self._todos)

    def get_next_pending(self) -> dict | None:
        """获取下一个 pending 状态的任务"""
        for todo in self._todos:
            if todo["status"] == "pending":
                return todo
        return None

    def format_todos(self) -> str:
        """格式化输出任务清单"""
        if not self._todos:
            return "📋 任务清单为空"

        lines = ["📋 任务清单：\n"]
        for todo in self._todos:
            icon = STATUS_ICONS.get(todo["status"], "⬜")
            lines.append(f"  {icon} #{todo['id']} {todo['content']}")

        # 统计
        pending = sum(1 for t in self._todos if t["status"] == "pending")
        in_progress = sum(1 for t in self._todos if t["status"] == "in_progress")
        completed = sum(1 for t in self._todos if t["status"] == "completed")
        lines.append(f"\n  共 {len(self._todos)} 项 | ⬜ {pending} 待办 | 🔄 {in_progress} 进行中 | ✅ {completed} 已完成")

        return "\n".join(lines)


# 全局单例，供 agent 和各工具函数共享状态
todo_manager = TodoManager()


def todo_write(todos: list[dict]) -> str:
    """创建待办事项清单（委托给 TodoManager）"""
    return todo_manager.create_todos(todos)


def todo_update(todo_id: int, status: Status) -> str:
    """更新指定任务的状态（委托给 TodoManager）"""
    return todo_manager.update_status(todo_id, status)
