from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from skill_manager import Skill


@dataclass
class ToolResult:
    """一次工具调用的执行记录"""

    tool_call_id: str
    name: str
    arguments: Dict[str, Any]
    result: str
    ok: bool = True


@dataclass
class AgentState:
    """Agent 的运行时状态"""

    # 完整对话历史（首条为 system 消息）
    messages: List[Dict[str, Any]] = field(default_factory=list)

    # 当前激活的 skill
    current_skill: Optional[Skill] = None

    # 最近一次用户输入
    last_user_input: Optional[str] = None

    # 当前等待执行/已发起的工具调用（原始 tool_calls 列表）
    pending_tool_calls: List[Dict[str, Any]] = field(default_factory=list)

    # 最近一轮工具执行结果：tool_call_id -> ToolResult
    last_tool_results: Dict[str, ToolResult] = field(default_factory=dict)

    # 整个会话的所有工具调用记录
    tool_history: List[ToolResult] = field(default_factory=list)

    # 已完成的用户轮次计数
    turn_count: int = 0

    # ---------- 消息管理 ----------

    def add_message(self, role: str, content: Any = None, **kwargs) -> dict:
        """向对话历史追加一条消息，返回该消息 dict"""
        message: Dict[str, Any] = {"role": role}
        if content is not None:
            message["content"] = content
        message.update(kwargs)
        self.messages.append(message)
        return message

    def set_system_prompt(self, content: str) -> None:
        """设置/更新 system 提示词（始终保持在消息列表首位）"""
        if self.messages and self.messages[0].get("role") == "system":
            self.messages[0]["content"] = content
        else:
            self.messages.insert(0, {"role": "system", "content": content})

    # ---------- 轮次管理 ----------

    def begin_turn(self, user_input: str) -> None:
        """开始一轮新对话：记录用户输入，并清理上一轮的工具状态"""
        self.last_user_input = user_input
        self.pending_tool_calls = []
        self.last_tool_results = {}
        self.turn_count += 1

    # ---------- 工具调用管理 ----------

    def begin_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> None:
        """记录模型发起的工具调用（等待执行）"""
        self.pending_tool_calls = list(tool_calls)

    def end_tool_calls(self) -> None:
        """工具调用全部执行完毕，清理等待中的调用"""
        self.pending_tool_calls = []

    def record_tool_result(
        self,
        tool_call_id: str,
        name: str,
        arguments: Dict[str, Any],
        result: str,
        ok: bool = True,
    ) -> ToolResult:
        """记录一次工具执行结果，并同步写入对话历史（tool 消息）"""
        record = ToolResult(
            tool_call_id=tool_call_id,
            name=name,
            arguments=arguments,
            result=result,
            ok=ok,
        )
        self.last_tool_results[tool_call_id] = record
        self.tool_history.append(record)
        self.add_message("tool", content=result, tool_call_id=tool_call_id)
        return record
