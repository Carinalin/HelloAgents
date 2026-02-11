import os
import streamlit as st
from dotenv import load_dotenv, find_dotenv  # 新增：导入dotenv相关函数
from langchain.chat_models import init_chat_model
from langchain_core.exceptions import LangChainException

# ====================== 1. 加载.env文件 ======================
def load_env_file():
    """
    加载当前目录（及上级目录）的.env文件，将其中的变量注入系统环境变量
    优先级：系统环境变量 > .env文件变量（load_dotenv默认不覆盖已存在的环境变量）
    """
    try:
        # find_dotenv()：自动查找当前目录/上级目录的.env文件，返回文件路径
        env_file_path = find_dotenv()
        if env_file_path:
            # 加载.env文件，override=False（默认）：不覆盖已有的系统环境变量
            load_dotenv(dotenv_path=env_file_path, override=False)
            st.success(f"✅ 成功加载.env文件：{env_file_path}")
        else:
            st.info("ℹ️ 未找到.env文件，将优先读取系统环境变量或手动输入API Key")
    except Exception as e:
        st.warning(f"⚠️ .env文件加载失败：{str(e)}（不影响后续操作）")


# ====================== 2. 定义模型供应商配置 ======================
MODEL_PROVIDERS = {
    "OpenAI": {
        "provider": "openai",
        "default_model": "gpt-3.5-turbo",
        "api_key_env": "OPENAI_API_KEY"
    },
    "Grok (XAI)": {
        "provider": "xai",
        "default_model": "grok-1",
        "api_key_env": "XAI_API_KEY"
    },
    "DeepSeek": {
        "provider": "deepseek",
        "default_model": "deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY"
    },
    "Anthropic (Claude)": {
        "provider": "anthropic",
        "default_model": "claude-3-haiku-20240307",
        "api_key_env": "ANTHROPIC_API_KEY"
    }
}

# ====================== 3. Streamlit交互界面 ======================
def get_model_credentials():
    """
    渲染模型供应商选择和API Key输入界面，返回选中的供应商配置和API Key
    优先级：系统环境变量 > .env文件变量 > 手动输入
    """
    # 先加载.env文件（全局执行）
    load_env_file()

    st.subheader("🔑 大模型配置")
    
    # 步骤1：下拉选择模型供应商
    selected_provider_name = st.selectbox(
        label="选择模型供应商",
        options=list(MODEL_PROVIDERS.keys()),
        index=0,
        help="支持OpenAI、Grok、DeepSeek、Anthropic等供应商"
    )
    
    # 步骤2：获取该供应商的配置
    provider_config = MODEL_PROVIDERS[selected_provider_name]
    
    # 步骤3：读取环境变量（已包含.env加载的变量），无则显示输入框
    api_key = os.getenv(provider_config["api_key_env"])
    if not api_key:
        api_key = st.text_input(
            label=f"{selected_provider_name} API Key",
            type="password",
            help=f"请输入{selected_provider_name}的API Key（可提前在.env文件中配置{provider_config['api_key_env']}）"
        )
        # 输入后设置环境变量
        if api_key:
            os.environ[provider_config["api_key_env"]] = api_key
    
    # 步骤4：自定义模型名
    model_name = st.text_input(
        label="模型名称",
        value=provider_config["default_model"],
        help=f"{selected_provider_name}默认模型：{provider_config['default_model']}"
    )
    
    # 验证API Key
    if not api_key:
        st.warning(f"请输入{selected_provider_name}的API Key！")
        return None, None, None
    
    return provider_config["provider"], model_name, api_key

# ====================== 4. 初始化大模型函数 ======================
def init_llm_model(temperature=0.3):
    """初始化大模型实例，返回llm对象"""
    model_provider, model_name, api_key = get_model_credentials()
    
    if not all([model_provider, model_name, api_key]):
        return None
    
    try:
        llm = init_chat_model(
            model_provider=model_provider,
            model=model_name,
            temperature=temperature,
            api_key=api_key
        )
        st.success(f"✅ {model_provider} 模型初始化成功！")
        return llm
    
    except LangChainException as e:
        st.error(f"❌ 模型初始化失败：{str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ 未知错误：{str(e)}")
        return None

# ====================== 5. 主流程调用 ======================
if __name__ == "__main__":
    st.title("大模型供应商配置与初始化")
    
    llm = init_llm_model(temperature=0.3)
    
    # 测试调用
    if llm:
        if prompt := st.text_input("输入测试prompt"):
            with st.spinner("模型思考中..."):
                response = llm.invoke(prompt)
                st.write("模型回复：", response.content)