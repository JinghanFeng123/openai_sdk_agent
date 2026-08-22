from tavily import TavilyClient
import json
import os


WEB_SEARCH_API_KEY = os.environ.get("TAIL_API_KEY")

# 联网搜索工具的实际执行函数
def web_search(target: str) -> str:
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
    print(web_search("https://www.tiktok.com/@israelarguetaa"))
