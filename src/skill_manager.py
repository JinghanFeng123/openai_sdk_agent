import os
import frontmatter
from typing import List, Dict, Any, Optional


class Skill:
    """单个 skill 的数据结构"""
    
    def __init__(self, name: str, description: str, trigger_keywords: List[str], prompt: str):
        self.name = name
        self.description = description
        self.trigger_keywords = trigger_keywords
        self.prompt = prompt
    
    def matches(self, user_input: str) -> bool:
        """检查用户输入是否匹配该 skill"""
        user_lower = user_input.lower()
        return any(kw.lower() in user_lower for kw in self.trigger_keywords)


class SkillManager:
    """Skill 管理器，负责加载和匹配 skill"""
    
    def __init__(self):
        self._skills: Dict[str, Skill] = {}
    
    def load_skills(self, skills_dir: str):
        """从目录加载所有 skill 文件"""
        if not os.path.isdir(skills_dir):
            print(f"⚠️ Skills 目录不存在: {skills_dir}")
            return
        
        for filename in os.listdir(skills_dir):
            if filename.endswith('.md'):
                filepath = os.path.join(skills_dir, filename)
                try:
                    self._load_skill_file(filepath)
                except Exception as e:
                    print(f"⚠️ 加载 skill 失败 {filename}: {e}")
    
    def _load_skill_file(self, filepath: str):
        """加载单个 skill Markdown 文件（使用 YAML frontmatter）"""
        with open(filepath, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        # 从 frontmatter 提取元数据
        name = post.get('name')
        if not name:
            print(f"⚠️ Skill 文件缺少 name 字段: {filepath}")
            return
        
        description = post.get('description', '')
        trigger_keywords = post.get('trigger_keywords', [])
        
        # Markdown 正文作为 prompt
        prompt = post.content.strip()
        
        skill = Skill(
            name=name,
            description=description,
            trigger_keywords=trigger_keywords,
            prompt=prompt
        )
        self._skills[skill.name] = skill
    
    def match_skill(self, user_input: str) -> Optional[Skill]:
        """根据用户输入匹配 skill"""
        for skill in self._skills.values():
            if skill.matches(user_input):
                return skill
        return None
    
    def get_all_skills_info(self) -> str:
        """获取所有 skill 的描述信息（用于 system prompt）"""
        if not self._skills:
            return ""
        
        lines = ["可用的 skills："]
        for skill in self._skills.values():
            lines.append(f"- {skill.name}: {skill.description}")
        
        return "\n".join(lines)
    
    def get_skill_count(self) -> int:
        """返回已加载的 skill 数量"""
        return len(self._skills)


# 全局单例
skill_manager = SkillManager()
