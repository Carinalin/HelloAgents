from typing import List, Literal, NotRequired, Annotated
from pydantic import BaseModel, Field
from langchain.agents import AgentState

class ConceptOutput(BaseModel):
    genre: str = Field(description="小说类型")
    target_audience: str = Field(description="目标读者")
    core_value: str = Field(description="小说的核心价值与主题思想")
    logline: str = Field(description="一句话故事梗概")

class Character(BaseModel):
    """小说中角色的结构化介绍。"""
    character_id: int = Field(..., description="特定角色的唯一ID。")
    name: str = Field(..., description="角色姓名")
    role: Literal["protagonist", "antagonist", "supporting", "minor"] = Field(..., description="角色类型")
    description: str = Field(..., description="角色的外貌、性格、背景等详细描述")
    motivation: str = Field(..., description="角色的核心动机和目标")
    arc: str = Field(..., description="角色的人物弧光，即其在故事中的成长与变化")

class CharacterListOutput(BaseModel):
    characters: List[Character] = Field(description="角色列表")

class WorldSetting(BaseModel):
    """小说世界和环境的结构化定义。"""
    time: str = Field(..., description="小说的具体时间段，可以是任何时间。")
    place: str = Field(None, description="故事的地理或虚构位置。")
    rules_of_the_world: str = Field(..., description="世界的基本法则、系统或传说。这可能包括魔法系统、技术水平、社会等级或物理定律。")
    culture_and_society: str = Field(..., description="关于主导文化、社会规范、语言和传统的详细信息。")
    unique_features: str = Field(None, description="这个世界最独特、最吸引人的地方是什么？有什么悬而未决的矛盾或秘密吗？")

class PlotPoint(BaseModel):
    name: str = Field(..., description="情节点的名称，如'激励事件'")
    description: str = Field(..., description="该情节点的详细描述")

class PlotStructureOutput(BaseModel):
    plots: List[PlotPoint] = Field(description="情节结构")

class Scene(BaseModel):
    """用于描述特定小说场景的结构化项目。"""
    scene_id: int = Field(..., description="特定场景的唯一ID。")
    characters: List[str] = Field(..., description="出现在此场景中的角色名称列表。")
    outline: str = Field(..., description="总结场景的主要情节和作用。")
    status: Literal["pending", "written"] = Field(..., description="场景是否已书写完成")
    content: str = Field(None, description="场景的具体内容")

class SceneOutput(BaseModel):
    chapter_id: int = Field(..., description="写作小说的章节ID。")
    title: str = Field(..., description="本章简洁且吸引人的标题。")
    scenes: List[Scene] = Field(description="特定章节的全部情节")

class Chapter(BaseModel):
    """用于描述特定小说章节的结构化项目。"""
    chapter_id: int = Field(..., description="写作小说的章节ID。")
    title: str = Field(..., description="本章简洁且吸引人的标题。")
    outline: str = Field(..., description="总结本章的主要情节和作用。")

class ChapterOutput(BaseModel):
    chapters: List[Chapter] = Field(description="章节大纲列表")
    
def text_reducer(left: str | None, right: str | None) -> str: 
    """合并两个字符串，右侧优先。
    用作 agent state 中的 final_novel_text 的 reducer function。
    参数：
        left: 左侧字符串（现章节的文本）
        right: 右侧字符串（新章节的文本）
    返回：
        两个换行符分隔的合并字符串
    """
    if left is None:
        return right
    elif right is None:
        return left
    else:
        return left + '\n\n' + right

class NovelState(AgentState):
    """
    继承自 LangGraph 的 AgentState，并添加了与小说写作相关的元素
    """
    # === User Input & Basic Settings ===
    human_feedback: NotRequired[str]
    genre: NotRequired[str]
    target_audience: NotRequired[str]
    core_value: NotRequired[str]
    logline: NotRequired[str]
    
    # === Core Creative Elements ===
    characters: NotRequired[list[Character]]
    world_setting: NotRequired[WorldSetting]
    plot_structure: NotRequired[list[PlotPoint]]

    # === Novel Outline ===
    chapter_outline: NotRequired[list[Chapter]]
    scene_outline: NotRequired[list[SceneOutput]]
    
    # === Final Product ===
    final_novel_text: Annotated[NotRequired[str], text_reducer]
    novel_summary: NotRequired[str]
    novel_title: NotRequired[str]
    
    # === Flow Control ===
    is_finished: NotRequired[bool]

class WritingState(AgentState):
    """
    继承自 LangGraph 的 AgentState 并添加了关于章节写作的元素。
    """
    # === Background Elements ===
    genre: NotRequired[str]
    core_value: NotRequired[str]
    logline: NotRequired[str]
    characters: NotRequired[list[Character]]
    world_setting: NotRequired[WorldSetting]
    
    # === Novel Outline ===
    chapter_outline: NotRequired[list[Chapter]]
    scene_outline: NotRequired[list[SceneOutput]]

    # ===the last content of the last chapter===
    last_scene_content: NotRequired[str]
    novel_summary: NotRequired[str]

    # === Content Generation ===
    current_chapter_id: NotRequired[int]
    current_scene_id: NotRequired[int]

    # === Review & Revision ===
    draft_content: NotRequired[str]
    next_action: Literal["approve", "revise"]
    review_feedback: NotRequired[str]
    revision_count: NotRequired[int]

    # ===chapter content===
    final_novel_text: Annotated[NotRequired[str], text_reducer]
    is_finished: NotRequired[bool]

class EditorOutput(BaseModel):
    decision: Literal["approve", "revise"] = Field(..., description="是否通过该场景的草稿")
    feedback: str = Field(None, description="编辑对草稿的详细反馈意见")

class NovelTitleOutput(BaseModel):
    """
    用于存储最终生成的小说书名及其创意说明。
    """
    title: str = Field(description="为小说取的一个有吸引力的、简洁的标题。")
    rationale: str = Field(description="解释为什么选择这个标题，它如何与小说的主题、情节或角色产生关联。")
