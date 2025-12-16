from langchain.chat_models import init_chat_model
from typing import List
from langgraph.graph import StateGraph, START, END

from English_Story.state import *
from English_Story.prompts import *


llm = init_chat_model(model_provider="deepseek", model="deepseek-chat", temperature=1.1)

def concept_developer(state: NovelState):
    print("---🧠 Executing: Concept Developer ---")
    prompt = CONCEPT_DEVELOPER_PROMPT.format(user_prompt=state['messages'][-1].content, 
                                             human_feedback = state.get('human_analyst_feedback', ''))
    structured_llm = llm.with_structured_output(ConceptOutput)
    result = structured_llm.invoke(prompt)
    print(f"   - Genre: {result.genre}")
    print(f"   - Core value: {result.core_value}")
    print(f"   - Logline: {result.logline}")
    
    return {'genre': result.genre, 'target_audience': result.target_audience,
           'core_value': result.core_value, 'logline': result.logline}

def world_builder(state: NovelState):
    print("---🌍 Executing: World Builder ---")
    prompt = WORLD_BUILDER_PROMPT.format(logline=state['logline'], genre=state['genre'],
                                         target_audience = state['target_audience'], 
                                         core_value = state['core_value'])
    structured_llm = llm.with_structured_output(WorldSetting)
    response = structured_llm.invoke(prompt)
    print("   - Generated world setting.")
    return {'world_setting': response}

def character_designer(state: NovelState):
    print("---👥 Executing: Character Designer ---")
    prompt = CHARACTER_DESIGNER_PROMPT.format(logline=state['logline'], 
                                              core_value = state['core_value'],
                                              world_setting=state['world_setting'])
    structured_llm = llm.with_structured_output(CharacterListOutput)
    result = structured_llm.invoke(prompt)
    print(f"   - Designed {len(result.characters)} chracters!")
    return {'characters': result.characters}

def plot_structurer(state: NovelState):
    print("---📈 Executing: Plot Structurer ---")
    character_list = [f"- {name}: {char}" for name, char in ((c.name, c) for c in state['characters'])]
    character_summaries = "\n".join(character_list)
    prompt = PLOT_STRUCTURER_PROMPT.format(logline=state['logline'], 
                                           core_value = state['core_value'],
                                           character_summaries=character_summaries)
    structured_llm = llm.with_structured_output(PlotStructureOutput) 
    result = structured_llm.invoke(prompt)
    print(f"   - Planed plot structure.")
    
    return {'plot_structure': result.plots}

def human_feedback(state: NovelState):
    """ No-op node that should be interrupted on """
    pass
    
def should_continue(state: NovelState):
    """ Return the next node to execute """

    # Check if human feedback
    human_feedback=state.get('human_feedback', None)
    if human_feedback.lower() != 'approve':
        return "concept_developer"
    
    # Otherwise end
    return "world_builder"

def chapter_outliner(state: NovelState):
    print("---📖 Executing: Chapter Outliner ---")
    plot_structure_summary = "\n".join([f"- {p.name}: {p.description}" for p in state['plot_structure']])
    character_list = [f"- {name}: {char}" for name, char in ((c.name, c) for c in state['characters'])]
    character_summaries = "\n".join(character_list)
    prompt = CHAPTER_OUTLINER_PROMPT.format(logline = state['logline'], world_setting = state['world_setting'],
                                            character_summaries = character_summaries,
                                            plot_structure_summary=plot_structure_summary)
    structured_llm = llm.with_structured_output(ChapterOutput)
    result = structured_llm.invoke(prompt)
    print(f"   - Created {len(result.chapters)} Chapters!")

    return {'chapter_outline': result.chapters}

def to_readable_str(data: List) -> str:
    """
    turn List[SceneOutput] into readable string
    """
    if data: 
        lines = []
        for out in data:
            # 1. chapter title
            lines.append(f"Chapter {out.chapter_id}: {out.title}")
            # 2. each scene
            for sc in out.scenes:
                lines.append(f"  Scene {sc.scene_id}：{','.join(sc.characters)}")
                lines.append(f"    {sc.outline}")
                lines.append("")
        return "\n".join(lines)
    else:
        return ''

def scene_outliner(state: NovelState):
    print("---🎬 Executing: Scene Outliner ---")
    character_list = [f"- {name}: {char}" for name, char in ((c.name, c) for c in state['characters'])]
    character_summaries = "\n".join(character_list)
    world_setting_summary = state['world_setting']
    
    res = []
    structured_llm = llm.with_structured_output(SceneOutput)
    for chapter in state['chapter_outline']:
        print(f"   - Creating scenes for '{chapter.chapter_id}' ...")
        prompt = SCENE_OUTLINER_PROMPT.format(
            chapter_id=chapter.chapter_id,
            chapter_title=chapter.title,
            chapter_summary=chapter.outline,
            logline = state['logline'], 
            character_summaries=character_summaries,
            world_setting_summary=world_setting_summary,
            written_scene_outline=to_readable_str(res)
        )
        result = structured_llm.invoke(prompt)
        result.chapter_id = chapter.chapter_id
        result.title = chapter.title
        for i, scene in enumerate(result.scenes):
            scene.scene_id = i + 1
            scene.status = "pending"
        
        res.append(result)
    print("---✅ All chapters were created scenes. ---")
    return {'scene_outline': res}

def scene_selector(state: WritingState):
    """
    logical node：select the next scene to write
    """
    print("---🎬 Executing: Scene Selector ---")
    
    for chapter in state['scene_outline']:
        for scene in chapter.scenes:
            if scene.status == "pending":
                print(f"   - Selected scene: [Chapter {chapter.chapter_id}, Scene {scene.scene_id}]")
                return {'current_chapter_id': chapter.chapter_id, 'current_scene_id': scene.scene_id, 'revision_count': 0}

    print("---✅ All scenes done, and exit writing loop. ---")
    return {'is_finished': True}

def writer(state: WritingState):
    """
    LLM node：write scenes
    """
    print(f"---✍️  Executing: Writer (Revise Count: {state.get('revision_count','')}) ---")
    
    current_chapter = next(ch for ch in state['scene_outline'] if ch.chapter_id == state['current_chapter_id'])
    current_scene = next(sc for sc in current_chapter.scenes if sc.scene_id == state['current_scene_id'])
    
    character_list = [f"- {name}: {char}" for name, char in ((c.name, c) for c in state['characters'])]
    character_summaries = "\n".join(character_list)

    novel_summary = state.get('novel_summary', '')
    last_scene_content = state.get('last_scene_content', '')

    prompt = WRITER_PROMPT.format(
            genre=state['genre'],
            current_chapter_id=state['current_chapter_id'],
            current_scene_id=state['current_scene_id'],
            current_scene_summary=current_scene.outline,
            current_scene_characters=current_scene.characters,
            logline = state['logline'], 
            characters=character_summaries,
            world_setting=state['world_setting'],
            novel_summary = novel_summary,
            last_scene_content = last_scene_content
        )

    if state.get('revision_count', 0) > 0:
        review_feedback = state.get('review_feedback', '')
        draft = state.get('draft_content', '')
        prompt += f"\n\nThis is the draft you wrote previously: {draft}\n\n**Editor's feedback**:\n{review_feedback}\n\nPlease revise the draft in accordance with the feedback above."
    
    response = llm.invoke(prompt)
    draft_content = response.content.strip()
    
    print(f"   - Generated draft (length: {len(draft_content)}).")
    return {'draft_content': draft_content}


def editor(state: WritingState):
    """
    LLM node：evaluate scene drafts
    """
    print("---👀 Executing: Editor ---")

    if state['revision_count'] >= 3:
        print(f"   - Warning: The maximum number of revisions has been reached ({state['revision_count']}), and the draft is approved automatically.")
        next_action = "approve"
        review_feedback = f"(Auto-approved) The number of revisions has reached {state['revision_count']}. To avoid an infinite loop, this draft has been forcibly accepted. Minor flaws may still exist, but the overall quality is acceptable."
        return {'next_action': next_action, 'review_feedback': review_feedback}
    
    current_chapter = next(ch for ch in state['scene_outline'] if ch.chapter_id == state['current_chapter_id'])
    current_scene = next(sc for sc in current_chapter.scenes if sc.scene_id == state['current_scene_id'])

    character_list = [f"- {name}: {char}" for name, char in ((c.name, c) for c in state['characters'])]
    character_summaries = "\n".join(character_list)

    novel_summary = state.get('novel_summary', '')
    last_scene_content = state.get('last_scene_content', '')
    
    prompt = EDITOR_PROMPT.format(
            genre=state['genre'],
            draft_content = state['draft_content'],
            scene_outline=current_scene.outline,
            logline = state['logline'], 
            characters=character_summaries,
            world_setting=state['world_setting'],
            novel_summary = novel_summary,
            last_scene_content = last_scene_content
        )
    structured_llm = llm.with_structured_output(EditorOutput)
    result = structured_llm.invoke(prompt)
    print(f"   - Editor decided: {result.decision}")
    print(f"   - Editor feedback: {result.feedback[:100]}...")
    return {'next_action': result.decision, 'review_feedback': result.feedback}

def reviser(state: WritingState):
    """
    logical node：count revision times
    """
    print("---🔄 Executing: Reviser ---")
    count = state['revision_count']
    count += 1
    print(f"   - Revision count updated to: {count}")
    return {'revision_count': count}

def content_approver(state: WritingState):
    """
    logical node：write the draft into the final text
    """
    print("---✅ Executing: Content Approver ---")
    
    scene_outline = state['scene_outline']
    ch_id = state['current_chapter_id']
    sc_id = state['current_scene_id']
    for chapter in scene_outline:
        if chapter.chapter_id == ch_id:
            for scene in chapter.scenes:
                if scene.scene_id == sc_id:
                    scene.content = state['draft_content']
                    scene.status = "written"
                    
                    final_scene_text = f"## [Chapter {chapter.chapter_id}] {chapter.title}\n\n### Scene {scene.scene_id}: \n\n{scene.content}\n"
                    
                    print(f"   - Chapter {chapter.chapter_id} Scene {scene.scene_id}' was added to the full text.")
                    novel_summary = state.get('novel_summary', '')
                    prompt = SUMMARY_PROMPT.format(scene_content = scene.content)
                    response = llm.invoke(prompt)
                    scene_summary = f"Summary of Chapter {ch_id} Secne {sc_id}: {response.content.strip()}"
                    print("   - Upated novel summary!")
                    return {'scene_outline': scene_outline, 'final_novel_text': final_scene_text,
                            'last_scene_content': state['draft_content'][-500:], 
                            'novel_summary': novel_summary+"\n\n"+scene_summary}
    
    raise ValueError("Could not find the current scene to finalize the draft!")

def final_namer(state: NovelState):
    """
    LLM node：brainstorm an enticing title for the finished novel
    """
    print("---🏷️  Executing: Final Namer ---")
    
    novel_preview = state['final_novel_text'][:1000] + "..." + state['final_novel_text'][-1000:]
    
    structured_llm = llm.with_structured_output(NovelTitleOutput)
    prompt = NAMER_PROMPT.format(user_prompt = state['messages'][-1].content, genre = state['genre'],
                                core_value = state['core_value'], logline = state['logline'],
                                novel_summary = state['novel_summary'], novel_preview = novel_preview)
    result = structured_llm.invoke(prompt)
    
    print(f"   - Novel title: 《{result.title}》")
    print(f"   - Rationale: {result.rationale}")
    return {'novel_title': result.title}

# create sub graph
subgraph_builder = StateGraph(WritingState)

subgraph_builder.add_node("scene_selector", scene_selector)
subgraph_builder.add_node("writer", writer)
subgraph_builder.add_node("editor", editor)
subgraph_builder.add_node("reviser", reviser)
subgraph_builder.add_node("content_approver", content_approver)
    
subgraph_builder.set_entry_point("scene_selector")
    
## add conditional edges
subgraph_builder.add_conditional_edges(
    "scene_selector",
    lambda state: "end_writing" if state.get('is_finished', None) else "write_scene",
    {
        "write_scene": "writer",
        "end_writing": END
    }
)
    
subgraph_builder.add_conditional_edges(
    "editor",
    lambda state: state['next_action'],
    {
        "revise": "reviser",
        "approve": "content_approver"
    }
)
    
## add normal edges
subgraph_builder.add_edge("writer", "editor")
subgraph_builder.add_edge("reviser", "writer")
subgraph_builder.add_edge("content_approver", "scene_selector")

# create graph
builder = StateGraph(NovelState)

builder.add_node("concept_developer",concept_developer)
builder.add_node("human_feedback", human_feedback)
builder.add_node("world_builder", world_builder)
builder.add_node("character_designer", character_designer)
builder.add_node("plot_structurer", plot_structurer)
builder.add_node("chapter_outliner", chapter_outliner)
builder.add_node("scene_outliner", scene_outliner)
builder.add_node("writing_subgraph", subgraph_builder.compile().with_config({"recursion_limit": 1000}))
builder.add_node("final_namer", final_namer)

builder.add_edge(START, "concept_developer")
builder.add_edge("concept_developer", "human_feedback")
builder.add_conditional_edges("human_feedback", should_continue, ["concept_developer", "world_builder"])
builder.add_edge("world_builder", "character_designer")
builder.add_edge("character_designer", "plot_structurer")
builder.add_edge("plot_structurer", "chapter_outliner")
builder.add_edge("chapter_outliner", "scene_outliner")
builder.add_edge("scene_outliner", "writing_subgraph")
builder.add_edge("writing_subgraph", "final_namer")
builder.add_edge("final_namer", END)

graph = builder.compile(interrupt_before=['human_feedback']).with_config({"recursion_limit": 1300})