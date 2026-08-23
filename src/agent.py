import os
from openai import OpenAI
from dotenv import load_dotenv
from tool_registry import ToolRegistry

# 加载环境变量
load_dotenv()

# 初始化 OpenAI client
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)

# 自动发现并加载所有工具
tools_impl_dir = os.path.join(os.path.dirname(__file__), "tools", "tools_impl")
registry = ToolRegistry()
registry.auto_discover(tools_impl_dir)

# 获取所有工具 schema
tools = registry.get_schemas()

print(f"✅ 已加载 {len(tools)} 个工具:")
for tool in tools:
    print(f"  - {tool['function']['name']}")

# 消息历史
messages = [
    {
        "role": "system",
        "content": "你是一个智能助手，可以使用各种工具帮助用户完成任务。"
    }
]

def chat_loop():
    """主对话循环"""
    print("\n🤖 智能助手已启动（输入 'exit' 退出）")
    
    while True:
        user_input = input("\n用户: ").strip()
        
        if user_input.lower() in ['exit', 'quit', '退出']:
            print("👋 再见！")
            break
        
        if not user_input:
            continue
        
        messages.append({"role": "user", "content": user_input})
        
        print(f"\n🤖 [思考中] 当前对话历史: {len(messages)} 条消息")
        
        # 工具调用循环（可能多次）
        while True:
            try:
                response = client.chat.completions.create(
                    model="qwen-max",
                    messages=messages,
                    tools=tools if tools else None,
                    stream=True
                )
                
                # 收集流式响应
                full_content = ""
                tool_calls_data = {}
                
                for chunk in response:
                    if not chunk.choices:
                        continue
                    
                    delta = chunk.choices[0].delta
                    
                    # 收集文本内容
                    if delta.content:
                        full_content += delta.content
                        print(delta.content, end="", flush=True)
                    
                    # 收集工具调用
                    if delta.tool_calls:
                        for tool_call in delta.tool_calls:
                            idx = tool_call.index
                            
                            if idx not in tool_calls_data:
                                tool_calls_data[idx] = {
                                    "id": None,
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""}
                                }
                            
                            if tool_call.id:
                                tool_calls_data[idx]["id"] = tool_call.id
                            
                            if tool_call.function:
                                if tool_call.function.name:
                                    tool_calls_data[idx]["function"]["name"] += tool_call.function.name
                                if tool_call.function.arguments:
                                    tool_calls_data[idx]["function"]["arguments"] += tool_call.function.arguments
                
                print()  # 换行
                
                # 如果没有工具调用，说明是最终回复
                if not tool_calls_data:
                    messages.append({
                        "role": "assistant",
                        "content": full_content
                    })
                    break
                
                # 有工具调用，构造 assistant 消息
                tool_calls_list = []
                for idx in sorted(tool_calls_data.keys()):
                    tool_calls_list.append(tool_calls_data[idx])
                
                assistant_message = {
                    "role": "assistant",
                    "content": full_content if full_content else None,
                    "tool_calls": tool_calls_list
                }
                messages.append(assistant_message)
                
                # 执行每个工具调用
                print(f"\n🔧 [工具调用] 检测到 {len(tool_calls_list)} 个工具调用")
                
                for i, tool_call in enumerate(tool_calls_list, 1):
                    func_name = tool_call["function"]["name"]
                    args_str = tool_call["function"]["arguments"]
                    
                    print(f"\n📌 [{i}/{len(tool_calls_list)}] 调用工具: {func_name}")
                    print(f"   参数: {args_str}")
                    
                    # 解析参数
                    try:
                        import json
                        args = json.loads(args_str) if args_str else {}
                    except json.JSONDecodeError:
                        args = {}
                        print(f"   ⚠️ 参数解析失败，使用空参数")
                    
                    # 使用 registry 执行工具
                    print(f"   💻 执行中...")
                    result = registry.execute(func_name, args)
                    print(f"   ✅ 执行结果: {result[:200]}..." if len(result) > 200 else f"   ✅ 执行结果: {result}")
                    
                    # 将结果添加到消息历史
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": result
                    })
                
                # 继续循环，让模型处理工具结果
                
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
                break

if __name__ == "__main__":
    chat_loop()
