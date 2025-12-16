from typing import List, Literal, NotRequired, Annotated
from pydantic import BaseModel, Field
from langchain.agents import AgentState

class ConceptOutput(BaseModel):
    genre: str = Field(description="The genre of the novel.")
    target_audience: str = Field(description="The target audience for the novel.")
    core_value: str = Field(description="The core value and thematic message of the novel.")
    logline: str = Field(description="A one-sentence story logline.")

class Character(BaseModel):
    """A structured introduction to a character in the novel."""
    character_id: int = Field(..., description="A unique ID for the specific character.")
    name: str = Field(..., description="The character's name.")
    role: Literal["protagonist", "antagonist", "supporting", "minor"] = Field(..., description="The character's role type.")
    description: str = Field(..., description="A detailed description of the character's appearance, personality, background, etc.")
    motivation: str = Field(..., description="The character's core motivation and goals.")
    arc: str = Field(..., description="The character's arc, describing their growth and change throughout the story.")

class CharacterListOutput(BaseModel):
    characters: List[Character] = Field(description="A list of characters.")

class WorldSetting(BaseModel):
    """A structured definition of the novel's world and environment."""
    time: str = Field(..., description="The specific time period of the novel; can be any time.")
    place: str = Field(None, description="The geographical or fictional location of the story.")
    rules_of_the_world: str = Field(..., description="The fundamental laws, systems, or lore of the world. This can include magic systems, technology levels, social hierarchies, or physical laws.")
    culture_and_society: str = Field(..., description="Details about the dominant culture, social norms, language, and traditions.")
    unique_features: str = Field(None, description="What is the most unique and fascinating aspect of this world? Are there any unresolved conflicts or secrets?")

class PlotPoint(BaseModel):
    name: str = Field(..., description="The name of the plot point, e.g., 'Inciting Incident'.")
    description: str = Field(..., description="A detailed description of this plot point.")

class PlotStructureOutput(BaseModel):
    plots: List[PlotPoint] = Field(description="The plot structure.")

class Scene(BaseModel):
    """A structured item for describing a specific novel scene."""
    scene_id: int = Field(..., description="A unique ID for the specific scene.")
    characters: List[str] = Field(..., description="A list of character names appearing in this scene.")
    outline: str = Field(..., description="A summary of the scene's main plot and purpose.")
    status: Literal["pending", "written"] = Field(..., description="Whether the scene has been written.")
    content: str = Field(None, description="The specific content of the scene.")

class SceneOutput(BaseModel):
    chapter_id: int = Field(..., description="The chapter ID of the novel being written.")
    title: str = Field(..., description="A concise and engaging title for this chapter.")
    scenes: List[Scene] = Field(description="All the scenes of a specific chapter.")

class Chapter(BaseModel):
    """A structured item for describing a specific novel chapter."""
    chapter_id: int = Field(..., description="The chapter ID of the novel being written.")
    title: str = Field(..., description="A concise and engaging title for this chapter.")
    outline: str = Field(..., description="A summary of the main plot and purpose of this chapter.")

class ChapterOutput(BaseModel):
    chapters: List[Chapter] = Field(description="A list of chapter outlines.")
    
def text_reducer(left: str | None, right: str | None) -> str: 
    """Merges two strings, with the right one taking precedence.
    Used as the reducer function for final_novel_text in the agent state.
    Args:
        left: The left string (text from the current chapter).
        right: The right string (text from the new chapter).
    Returns:
        The merged string, separated by two newlines.
    """
    if left is None:
        return right
    elif right is None:
        return left
    else:
        return left + '\n\n' + right

class NovelState(AgentState):
    """
    Inherits from LangGraph's AgentState and adds elements related to novel writing.
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
    Inherits from LangGraph's AgentState and adds elements for chapter writing.
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

    # === the last content of the last chapter ===
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

    # === chapter content ===
    final_novel_text: Annotated[NotRequired[str], text_reducer]
    is_finished: NotRequired[bool]

class EditorOutput(BaseModel):
    decision: Literal["approve", "revise"] = Field(..., description="Whether to approve the draft of the scene.")
    feedback: str = Field(None, description="The editor's detailed feedback on the draft.")

class NovelTitleOutput(BaseModel):
    """
    Used to store the final generated novel title and its creative rationale.
    """
    title: str = Field(description="An attractive and concise title for the novel.")
    rationale: str = Field(description="An explanation of why this title was chosen and how it relates to the novel's theme, plot, or characters.")
