import json
from openai import OpenAI
import os
from tools.tools_impl.bash_tool import execute_bash
from tools.tools_impl.web_search_tool import web_search

# 确保你的环境变量中配置了正确的 Key
YOUR_API_KEY = os.environ["DASHSCOPE_API_KEY"]

# 核心修改点：添加 base_url 指向阿里云 DashScope 的兼容接口地址
client = OpenAI(
    api_key=YOUR_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 从 JSON 配置文件加载工具 schema
with open(os.path.join(os.path.dirname(__file__), "tools", "tools_config.json"), "r", encoding="utf-8") as f:
    tools = json.load(f)["tools"]

system_prompt: str = """
                    你是可以使用power shell进行文件操作和使用工具进行网络信息查询的agent助手
                """
messages = [{"role": "system", "content": system_prompt}]

# Agent 核心循环
def agent_loop(tools=tools):
    while True:
        # 读取用户输入
        user_input = input("\n用户: ").strip()
        
        # 退出机制
        if user_input.lower() in ["exit", "quit", "退出"]:
            print("再见！")
            break
        
        # 跳过空输入
        if not user_input:
            continue
        
        # 追加用户消息到历史
        messages.append({"role": "user", "content": user_input})
        
        # 内层循环：处理工具调用
        while True:
            # 将消息和工具发送给大模型
            response = client.chat.completions.create(
                model="qwen-max",
                messages=messages,
                tools=tools,
                stream=True,  # 启用流式输出
            )
            
            # 收集流式响应
            content_chunks = []
            tool_calls_data = {}
            
            for chunk in response:
                delta = chunk.choices[0].delta
                
                # 收集文本内容
                if delta.content:
                    content_chunks.append(delta.content)
                    print(delta.content, end="", flush=True)
                
                # 收集工具调用信息
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        idx = tool_call.index
                        if idx not in tool_calls_data:
                            tool_calls_data[idx] = {
                                "id": None,
                                "function": {"name": "", "arguments": ""}
                            }
                        if tool_call.id:
                            tool_calls_data[idx]["id"] = tool_call.id
                        if tool_call.function:
                            if tool_call.function.name:
                                tool_calls_data[idx]["function"]["name"] += tool_call.function.name
                            if tool_call.function.arguments:
                                tool_calls_data[idx]["function"]["arguments"] += tool_call.function.arguments
            
            # 如果没有工具调用，说明是最终回复，已经流式打印完毕
            if not tool_calls_data:
                full_content = "".join(content_chunks)
                messages.append({"role": "assistant", "content": full_content})
                break
            
            # 有工具调用，换行后执行
            print()
            
            # 构造完整的 assistant 消息（包含工具调用）
            assistant_message = {
                "role": "assistant",
                "content": "".join(content_chunks) if content_chunks else None,
                "tool_calls": [
                    {
                        "id": data["id"],
                        "type": "function",
                        "function": {
                            "name": data["function"]["name"],
                            "arguments": data["function"]["arguments"]
                        }
                    }
                    for data in tool_calls_data.values()
                ]
            }
            messages.append(assistant_message)
            
            # 执行每个工具调用
            for data in tool_calls_data.values():
                func_name = data["function"]["name"]
                args = json.loads(data["function"]["arguments"])
                
                if func_name == "execute_bash":
                    print(f"[执行命令]: {args['command']}")
                    result = execute_bash(args['command'])
                elif func_name == "search_tool":
                    print(f"[联网搜索]: {args['target']}")
                    result = web_search(args['target'])
                else:
                    result = f"未知工具: {func_name}"
                
                print(f"[执行结果]: {str(result)[:200]}...")
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": data["id"],
                    "content": result
                })

# 启动对话
if __name__ == "__main__":
    print("Agent 已启动，输入 'exit' 退出")
    agent_loop(tools)
