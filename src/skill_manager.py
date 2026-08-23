import os
from typing import Dict, List, Optional

import frontmatter
import yaml


class Skill:
    """单个 skill 的数据结构"""

    def __init__(
        self,
        name: str,
        description: str,
        trigger_keywords: List[str],
        prompt: str,
        enabled: bool = True,
        file: Optional[str] = None,
    ):
        self.name = name
        self.description = description
        self.trigger_keywords = trigger_keywords or []
        self.prompt = prompt
        self.enabled = enabled
        self.file = file

    def matches(self, user_input: str) -> bool:
        """检查用户输入是否匹配该 skill"""
        user_lower = user_input.lower()
        return any(kw.lower() in user_lower for kw in self.trigger_keywords)


class SkillManager:
    """Skill 管理器：负责从注册表加载、查询和匹配 skill

    优先读取 skills 目录下的 skills.yaml 注册表；
    若注册表不存在，则回退到旧的「扫描全部 .md + YAML frontmatter」方式。
    """

    CONFIG_FILENAME = "skills.yaml"

    def __init__(self):
        self._skills: Dict[str, Skill] = {}

    # ---------- 加载 ----------

    def load_skills(self, skills_dir: str):
        """从目录加载所有 skill（优先读取 skills.yaml 注册表）"""
        if not os.path.isdir(skills_dir):
            print(f"⚠️ Skills 目录不存在: {skills_dir}")
            return

        config_path = os.path.join(skills_dir, self.CONFIG_FILENAME)
        if os.path.isfile(config_path):
            self._load_from_config(config_path, skills_dir)
        else:
            # 兼容：没有注册表时，扫描目录中的 Markdown（YAML frontmatter）文件
            self._load_from_markdown(skills_dir)

    def _load_from_config(self, config_path: str, skills_dir: str):
        """从 skills.yaml 注册表加载 skill"""
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        for item in config.get("skills", []):
            try:
                self._load_skill_from_entry(item, skills_dir)
            except Exception as e:
                print(f"⚠️ 加载 skill 失败 {item.get('name')}: {e}")

    def _load_skill_from_entry(self, item: dict, skills_dir: str):
        """加载注册表中的单个 skill 条目"""
        name = item.get("name")
        if not name:
            print("⚠️ skills.yaml 中存在缺少 name 的条目，已跳过")
            return

        if not item.get("enabled", True):
            print(f"⏭️ 跳过已禁用的 skill: {name}")
            return

        file_name = item.get("file", f"{name}.md")
        filepath = os.path.join(skills_dir, file_name)
        if not os.path.isfile(filepath):
            print(f"⚠️ skill {name} 的提示词文件不存在: {filepath}")
            return

        prompt = self._read_prompt(filepath)
        skill = Skill(
            name=name,
            description=item.get("description", ""),
            trigger_keywords=item.get("trigger_keywords", []),
            prompt=prompt,
            enabled=True,
            file=file_name,
        )
        self._skills[name] = skill

    def _load_from_markdown(self, skills_dir: str):
        """旧方式：扫描目录下所有 .md 文件，从 YAML frontmatter 读取元数据"""
        for filename in os.listdir(skills_dir):
            if not filename.endswith(".md"):
                continue
            filepath = os.path.join(skills_dir, filename)
            try:
                self._load_skill_from_markdown(filepath, filename)
            except Exception as e:
                print(f"⚠️ 加载 skill 失败 {filename}: {e}")

    def _load_skill_from_markdown(self, filepath: str, filename: str):
        post = frontmatter.load(filepath)
        name = post.get("name")
        if not name:
            print(f"⚠️ Skill 文件缺少 name 字段: {filepath}")
            return

        skill = Skill(
            name=name,
            description=post.get("description", ""),
            trigger_keywords=post.get("trigger_keywords", []),
            prompt=post.content.strip(),
            enabled=True,
            file=filename,
        )
        self._skills[name] = skill

    @staticmethod
    def _read_prompt(filepath: str) -> str:
        """读取提示词正文：兼容带/不带 YAML frontmatter 的 Markdown 文件"""
        return frontmatter.load(filepath).content.strip()

    # ---------- 查询 ----------

    def match_skill(self, user_input: str) -> Optional[Skill]:
        """根据用户输入匹配第一个命中的 skill"""
        for skill in self._skills.values():
            if skill.matches(user_input):
                return skill
        return None

    def get_all_skills(self) -> List[Skill]:
        """返回所有已加载的 skill"""
        return list(self._skills.values())

    def get_skill(self, name: str) -> Optional[Skill]:
        """按名称获取 skill"""
        return self._skills.get(name)

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
