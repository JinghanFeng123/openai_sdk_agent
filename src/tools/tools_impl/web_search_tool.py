from tavily import TavilyClient
import json
import os


WEB_SEARCH_API_KEY = os.environ.get("TAVIL_API_KEY")

# 工具 schema 定义
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_tool",
            "description": "进行联网搜索并返回搜索结果",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "要联网搜索的对象"}
                },
                "required": ["target"]
            }
        }
    }
]


# 联网搜索工具的实际执行函数
def search_tool(target: str) -> str:
    try:
        client = TavilyClient(WEB_SEARCH_API_KEY)
        response = client.search(
            query=target,
            maxResults=3,
            search_depth="advanced",
            include_answer="basic"
        )
        formatted_json_str = json.dumps(response, ensure_ascii=False, indent=2)
        return formatted_json_str
    except Exception as e:
        return f"执行出错: {str(e)}"


if __name__ == "__main__":
    print(search_tool("https://www.tiktok.com/@israelarguetaa"))
