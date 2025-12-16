from langchain.chat_models import init_chat_model
from typing import List
from langgraph.graph import StateGraph, START, END

from Chinese_Story.state import *
from Chinese_Story.prompts import *


llm = init_chat_model(model_provider="deepseek", model="deepseek-chat", temperature=1.1)

# 概念发展者节点：
def concept_developer(state: NovelState):
    print("---🧠 执行: 概念开发者 ---")
    prompt = CONCEPT_DEVELOPER_PROMPT.format(user_prompt=state['messages'][-1].content, 
                                             human_feedback = state.get('human_analyst_feedback', ''))
    structured_llm = llm.with_structured_output(ConceptOutput)
    result = structured_llm.invoke(prompt)
    print(f"   - 类型: {result.genre}")
    print(f"   - 核心价值: {result.core_value}")
    print(f"   - 故事梗概: {result.logline}")
    
    return {'genre': result.genre, 'target_audience': result.target_audience,
           'core_value': result.core_value, 'logline': result.logline}

# 世界观设定节点：
def world_builder(state: NovelState):
    print("---🌍 执行: 世界观构建师 ---")
    prompt = WORLD_BUILDER_PROMPT.format(logline=state['logline'], genre=state['genre'],
                                         target_audience = state['target_audience'], 
                                         core_value = state['core_value'])
    structured_llm = llm.with_structured_output(WorldSetting)
    response = structured_llm.invoke(prompt)
    print("   - 世界观设定已生成。")
    return {'world_setting': response}

# 角色设计节点
def character_designer(state: NovelState):
    print("---👥 执行: 角色设计师 ---")
    prompt = CHARACTER_DESIGNER_PROMPT.format(logline=state['logline'], 
                                              core_value = state['core_value'],
                                              world_setting=state['world_setting'])
    structured_llm = llm.with_structured_output(CharacterListOutput)
    result = structured_llm.invoke(prompt)
    print(f"   - 已设计 {len(result.characters)} 个角色")
    return {'characters': result.characters}

# 情节架构设计节点
def plot_structurer(state: NovelState):
    print("---📈 执行: 情节架构师 ---")
    character_list = [f"- {name}: {char}" for name, char in ((c.name, c) for c in state['characters'])]
    character_summaries = "\n".join(character_list)
    prompt = PLOT_STRUCTURER_PROMPT.format(logline=state['logline'], 
                                           core_value = state['core_value'],
                                           character_summaries=character_summaries)
    structured_llm = llm.with_structured_output(PlotStructureOutput) 
    result = structured_llm.invoke(prompt)
    print(f"   - 已规划好情节架构。")
    
    return {'plot_structure': result.plots}

# 构建一个专门的 human feedback node / dummy node，然后在这个节点打断点，等待用户指示
def human_feedback(state: NovelState):
    """ No-op node that should be interrupted on """
    pass
    
#构建 contional edge func，有人类反馈则返回 concept_developer，无则 world_builder
def should_continue(state: NovelState):
    """ Return the next node to execute """

    # Check if human feedback
    human_feedback=state.get('human_feedback', None)
    if human_feedback.lower() != 'approve':
        return "concept_developer"
    
    # Otherwise end
    return "world_builder"

# 编写章节大纲节点
def chapter_outliner(state: NovelState):
    print("---📖 执行: 章节大纲师 ---")
    plot_structure_summary = "\n".join([f"- {p.name}: {p.description}" for p in state['plot_structure']])
    character_list = [f"- {name}: {char}" for name, char in ((c.name, c) for c in state['characters'])]
    character_summaries = "\n".join(character_list)
    prompt = CHAPTER_OUTLINER_PROMPT.format(logline = state['logline'], world_setting = state['world_setting'],
                                            character_summaries = character_summaries,
                                            plot_structure_summary=plot_structure_summary)
    structured_llm = llm.with_structured_output(ChapterOutput)
    result = structured_llm.invoke(prompt)
    print(f"   - 已创建 {len(result.chapters)} 个章节大纲。")

    return {'chapter_outline': result.chapters}

# 编写场景大纲节点
def to_readable_str(data: List) -> str:
    """
    把 List[SceneOutput] 转成可阅读的纯文本
    """
    if data: 
        lines = []
        for out in data:
            # 1. 章节标题
            lines.append(f"【第{out.chapter_id}章】{out.title}")
            # 2. 逐个场景
            for sc in out.scenes:
                lines.append(f"  场景{sc.scene_id}：{','.join(sc.characters)}")
                lines.append(f"    {sc.outline}")
                lines.append("")   # 空行分隔
        return "\n".join(lines)
    else:
        return ''

def scene_outliner(state: NovelState):
    print("---🎬 执行: 场景大纲师 ---")
    character_list = [f"- {name}: {char}" for name, char in ((c.name, c) for c in state['characters'])]
    character_summaries = "\n".join(character_list)
    world_setting_summary = state['world_setting']
    
    res = []
    structured_llm = llm.with_structured_output(SceneOutput)
    for chapter in state['chapter_outline']:
        print(f"   - 正在为章节 '{chapter.chapter_id}' 创建场景...")
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
        # 更新章节的场景列表，并确保chapter_id和scene_id正确
        result.chapter_id = chapter.chapter_id
        result.title = chapter.title
        for i, scene in enumerate(result.scenes):
            scene.scene_id = i + 1
            scene.status = "pending"
        
        res.append(result)
    print("---✅ 所有章节的场景大纲创建完成 ---")
    return {'scene_outline': res}

# 场景选择器节点
def scene_selector(state: WritingState):
    """
    逻辑节点：确定下一个要写的场景。
    """
    print("---🎬 执行: 场景调度器 ---")
    
    # 查找第一个状态为 'pending' 的场景
    for chapter in state['scene_outline']:
        for scene in chapter.scenes:
            if scene.status == "pending":
                print(f"   - 选中场景: [章节 {chapter.chapter_id}, 场景 {scene.scene_id}]")
                # 重置修订计数
                return {'current_chapter_id': chapter.chapter_id, 'current_scene_id': scene.scene_id, 'revision_count': 0}

    # 如果所有场景都已写完
    print("---✅ 所有场景已写完，退出写作循环 ---")
    return {'is_finished': True}

# 书写节点
def writer(state: WritingState):
    """
    LLM节点：执笔者，根据场景大纲写作。
    """
    print(f"---✍️  执行: 执笔者 (修订次数: {state.get('revision_count','')}) ---")
    
    # 获取当前场景信息
    current_chapter = next(ch for ch in state['scene_outline'] if ch.chapter_id == state['current_chapter_id'])
    current_scene = next(sc for sc in current_chapter.scenes if sc.scene_id == state['current_scene_id'])
    
    # 获取相关角色信息
    character_list = [f"- {name}: {char}" for name, char in ((c.name, c) for c in state['characters'])]
    character_summaries = "\n".join(character_list)

    # 获取小说总结和上一场景内容
    novel_summary = state.get('novel_summary', '')
    last_scene_content = state.get('last_scene_content', '')

    # 编辑提示词
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
    # 如果是修订，加入编辑意见
    if state.get('revision_count', 0) > 0:
        review_feedback = state.get('review_feedback', '')
        draft = state.get('draft_content', '')
        prompt += f"\n\n这是你之前写的草稿: {draft}\n\n**编辑修改意见**:\n{review_feedback}\n\n请根据以上意见，对草稿进行修改。"
    
    response = llm.invoke(prompt)
    draft_content = response.content.strip()
    # draft_content = "Good"
    
    print(f"   - 草稿已生成 (长度: {len(draft_content)})")
    return {'draft_content': draft_content}

# 编辑审核节点
def editor(state: WritingState):
    """
    LLM节点：编辑，审核草稿质量。
    """
    print("---👀 执行: 编辑 ---")

    # 检查修订次数
    if state['revision_count'] >= 3:
        print(f"   - 警告：修订次数已达上限 ({state['revision_count']})，强制通过。")
        next_action = "approve"
        review_feedback = f"（自动通过）修订次数已达 {state['revision_count']} 次。为避免无限循环，此稿被强制接受。可能仍存在细微瑕疵，但整体可以接受。"
        return {'next_action': next_action, 'review_feedback': review_feedback}
    
    # 获取当前场景信息
    current_chapter = next(ch for ch in state['scene_outline'] if ch.chapter_id == state['current_chapter_id'])
    current_scene = next(sc for sc in current_chapter.scenes if sc.scene_id == state['current_scene_id'])

    # 获取相关角色信息
    character_list = [f"- {name}: {char}" for name, char in ((c.name, c) for c in state['characters'])]
    character_summaries = "\n".join(character_list)

    # 获取小说总结和上一场景内容
    novel_summary = state.get('novel_summary', '')
    last_scene_content = state.get('last_scene_content', '')
    
    # 编辑提示词
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
    print(f"   - 编辑决定: {result.decision}")
    print(f"   - 反馈: {result.feedback[:100]}...")
    return {'next_action': result.decision, 'review_feedback': result.feedback}

# 记录修订次数节点
def reviser(state: WritingState):
    """
    逻辑节点：增加修订计数，并导向 writer 节点。
    """
    print("---🔄 执行: 修订者 ---")
    count = state['revision_count']
    count += 1
    print(f"   - 修订次数增至: {count}")
    return {'revision_count': count}

# 定稿节点
def content_approver(state: WritingState):
    """
    逻辑节点：定稿，将草稿内容写入最终文本。
    """
    print("---✅ 执行: 内容定稿员 ---")
    
    # 找到当前场景并更新其内容和状态
    scene_outline = state['scene_outline']
    ch_id = state['current_chapter_id']
    sc_id = state['current_scene_id']
    for chapter in scene_outline:
        if chapter.chapter_id == ch_id:
            for scene in chapter.scenes:
                if scene.scene_id == sc_id:
                    scene.content = state['draft_content']
                    scene.status = "written"
                    
                    # 将定稿内容追加到最终小说文本
                    final_scene_text = f"## [章节 {chapter.chapter_id}] {chapter.title}\n\n### 场景 {scene.scene_id}: \n\n{scene.content}\n"
                    
                    print(f"   - 章节 {chapter.chapter_id} 场景 {scene.scene_id}' 已定稿并加入全书。")
                    novel_summary = state.get('novel_summary', '')
                    prompt = SUMMARY_PROMPT.format(scene_content = scene.content)
                    response = llm.invoke(prompt)
                    scene_summary = f"第{ch_id}章第{sc_id}个场景概要：{response.content.strip()}"
                    # scene_summary = f"第{ch_id}章第{sc_id}个场景概要：Go"
                    print("   - 小说总结已更新。")
                    return {'scene_outline': scene_outline, 'final_novel_text': final_scene_text,
                            'last_scene_content': state['draft_content'][-500:], 
                            'novel_summary': novel_summary+"\n\n"+scene_summary}
    
    raise ValueError("无法找到当前场景以定稿！")

def final_namer(state: NovelState):
    """
    LLM节点：为完成的小说取一个有吸引力的名字。
    """
    print("---🏷️  执行: 最终命名师 ---")
    
    # 为了避免将整本小说都放进 prompt（太长且昂贵），我们主要依赖核心信息和总结
    # 但可以截取最终文本的开头和结尾部分，给 LLM 一些“文风”上的感知
    novel_preview = state['final_novel_text'][:1000] + "..." + state['final_novel_text'][-1000:]
    
    structured_llm = llm.with_structured_output(NovelTitleOutput)
    prompt = NAMER_PROMPT.format(user_prompt = state['messages'][-1].content, genre = state['genre'],
                                core_value = state['core_value'], logline = state['logline'],
                                novel_summary = state['novel_summary'], novel_preview = novel_preview)
    result = structured_llm.invoke(prompt)
    # result = NovelTitleOutput(title = 'title', rationale = '...')
    
    print(f"   - 最终书名: 《{result.title}》")
    print(f"   - 命名理由: {result.rationale}")
    return {'novel_title': result.title}

# 创建子图
subgraph_builder = StateGraph(WritingState)

subgraph_builder.add_node("scene_selector", scene_selector)
subgraph_builder.add_node("writer", writer)
subgraph_builder.add_node("editor", editor)
subgraph_builder.add_node("reviser", reviser)
subgraph_builder.add_node("content_approver", content_approver)
    
subgraph_builder.set_entry_point("scene_selector")
    
## 添加条件边
subgraph_builder.add_conditional_edges(
    "scene_selector",
    # 决定函数：检查是否所有场景都已写完
    lambda state: "end_writing" if state.get('is_finished', None) else "write_scene",
    {
        "write_scene": "writer",
        "end_writing": END # 子图的 END
    }
)
    
subgraph_builder.add_conditional_edges(
    "editor",
    # 决定函数：根据编辑的反馈决定下一步
    lambda state: state['next_action'],
    {
        "revise": "reviser",
        "approve": "content_approver"
    }
)
    
## 添加普通边
subgraph_builder.add_edge("writer", "editor")
subgraph_builder.add_edge("reviser", "writer")
subgraph_builder.add_edge("content_approver", "scene_selector")

# 创建主图
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