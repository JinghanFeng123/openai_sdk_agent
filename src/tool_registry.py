import os
import importlib
import inspect
from typing import Dict, List, Any, Callable


class ToolRegistry:
    """工具注册表，自动扫描并注册工具"""
    
    def __init__(self):
        self._schemas: List[Dict[str, Any]] = []
        self._handlers: Dict[str, Callable] = {}
    
    def register(self, name: str, schema: Dict[str, Any], handler: Callable):
        """注册单个工具"""
        self._schemas.append(schema)
        self._handlers[name] = handler
    
    def get_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具 schema（用于传给 API）"""
        return self._schemas
    
    def get_handler(self, name: str) -> Callable:
        """根据工具名获取处理函数"""
        return self._handlers.get(name)
    
    def execute(self, name: str, args: Dict[str, Any]) -> str:
        """执行工具调用"""
        handler = self.get_handler(name)
        if not handler:
            return f"未知工具: {name}"
        try:
            return handler(**args)
        except Exception as e:
            return f"工具执行错误: {str(e)}"
    
    def auto_discover(self, tools_dir: str):
        """
        自动扫描目录，导入所有工具模块并注册
        
        每个工具模块需要导出：
        - tools: list[dict] - 工具 schema 列表
        - 与 schema 中 name 对应的处理函数
        """
        if not os.path.isdir(tools_dir):
            raise ValueError(f"工具目录不存在: {tools_dir}")
        
        # 获取包路径
        package_name = self._dir_to_module_path(tools_dir)
        
        # 扫描目录中的所有 .py 文件
        for filename in os.listdir(tools_dir):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = filename[:-3]  # 去掉 .py
                full_module_name = f"{package_name}.{module_name}"
                
                try:
                    # 动态导入模块
                    module = importlib.import_module(full_module_name)
                    
                    # 检查是否导出了 tools 列表
                    if not hasattr(module, 'tools'):
                        continue
                    
                    tools_list = module.tools
                    if not isinstance(tools_list, list):
                        continue
                    
                    # 注册每个工具
                    for tool_schema in tools_list:
                        func_name = tool_schema.get("function", {}).get("name")
                        if not func_name:
                            continue
                        
                        # 查找对应的处理函数
                        handler = getattr(module, func_name, None)
                        if not handler or not callable(handler):
                            continue
                        
                        # 注册
                        self.register(func_name, tool_schema, handler)
                        
                except Exception as e:
                    print(f"⚠️ 加载工具模块失败 {module_name}: {e}")
    
    @staticmethod
    def _dir_to_module_path(dir_path: str) -> str:
        """将目录路径转换为 Python 模块路径"""
        # 简化处理：从 src 开始计算相对路径
        abs_path = os.path.abspath(dir_path)
        
        # 向上查找直到找到 src 目录
        current = abs_path
        while current and not current.endswith('src'):
            parent = os.path.dirname(current)
            if parent == current:  # 到达根目录
                break
            current = parent
        
        if current.endswith('src'):
            # 从 src 开始的相对路径
            rel_path = os.path.relpath(abs_path, current)
            # 转换为模块路径
            return rel_path.replace(os.sep, '.')
        
        # 兜底：使用完整路径
        return abs_path.replace(os.sep, '.')


# 全局注册表单例
registry = ToolRegistry()


def load_tools(tools_impl_dir: str) -> ToolRegistry:
    """加载所有工具的便捷函数"""
    registry.auto_discover(tools_impl_dir)
    return registry
