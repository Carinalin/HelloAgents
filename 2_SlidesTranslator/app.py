import os
import sys
import logging
import streamlit as st
from models import init_llm_model
from graph import create_graph
import tempfile

# 定义语言名称和代码的映射字典
LANGUAGE_OPTIONS = {
    "中文": "Chinese",
    "英文": "English",
    "日语": "Japanese",
    "韩文": "Korean",
}

# 配置日志系统
def setup_logging():
    # 创建日志目录（如果不存在）
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, "ppt_translator.log")
    
    # 设置日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # 1. 输出到文件 (用于生产环境排查)
            logging.FileHandler(log_file, encoding='utf-8'),
            # 2. 输出到控制台 (Streamlit 底部可以看到)
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    # 初始化日志配置
    setup_logging()
    
    # 获取 logger (在 main 中也使用 logger 打印配置信息)
    logger = logging.getLogger(__name__)

    # 绘制前端
    st.set_page_config(page_title="PPT 翻译 Agent", layout="wide")
    st.title("🚀 PPT 翻译 Agent")
    st.markdown("基于 LangGraph + Streamlit + 异步编程构建。高效并发翻译，保持原设计。")

    with st.sidebar:
        st.header("设置")
        target_lang_name = st.selectbox(label="翻译语言",
                                        options=list(LANGUAGE_OPTIONS.keys()),
                                        index=0)
        target_lang = LANGUAGE_OPTIONS[target_lang_name]
        uploaded_file = st.file_uploader("上传 PPT 文件", type=['pptx'])
        
        # 并发设置
        st.subheader("性能设置")
        max_concurrent = st.slider("最大并发请求数", min_value=1, max_value=20, value=10)
        batch_size = st.slider("批次大小", min_value=1, max_value=20, value=10)
        
        # 配置模型
        st.title("大模型供应商配置与初始化")
    
        llm = init_llm_model(temperature=0.3)
    
        # 测试调用
        if llm:
            if prompt := st.text_input("输入测试prompt"):
                with st.spinner("模型思考中..."):
                    response = llm.invoke(prompt)
                    st.write("模型回复：", response.content)

    if uploaded_file is not None:
        st.info(f"📄 已上传文件: `{uploaded_file.name}`")

        logger.info(f"用户上传文件: {uploaded_file.name}")
        
        if st.button("开始翻译", type="primary"):

            # 记录开始事件
            logger.info(f"收到翻译请求: 文件名={uploaded_file.name}, 目标语言={target_lang}")

            with tempfile.TemporaryDirectory() as tmpdir:
                input_path = os.path.join(tmpdir, uploaded_file.name)
                output_filename = f"{target_lang}_{uploaded_file.name}"
                output_path = os.path.join(tmpdir, output_filename)
                
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                initial_state = {
                    "input_ppt_path": input_path,
                    "output_ppt_path": output_path,
                    "target_language": target_lang,
                    "extracted_data": [],
                    "translation_map": {},
                    "status_msg": "初始化中...",
                    "max_concurrent": max_concurrent,
                    "batch_size": batch_size,
                }
                
                app = create_graph(llm)
                
                # 创建进度条和状态容器
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # 使用自定义的运行器来更新进度
                    def run_with_progress():
                        # 模拟进度更新
                        status_text.text("🔄 正在解析 PPT...")
                        progress_bar.progress(10)
                        
                        result = app.invoke(initial_state)
                        
                        status_text.text(result["status_msg"])
                        progress_bar.progress(100)
                        
                        return result
                    
                    final_state = run_with_progress()
                    
                    st.success(final_state["status_msg"])
                    
                    with open(output_path, "rb") as fp:
                        st.download_button(
                            label="📥 下载翻译后的 PPT",
                            data=fp,
                            file_name=output_filename,
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                        )
                        
                except Exception as e:
                    st.error(f"处理出错: {str(e)}")

if __name__ == "__main__":
    main()