import streamlit as st
from google import genai
import pypdf
from docx import Document

# --- 1. 页面配置 ---
st.set_page_config(page_title="林业智能办公助手", page_icon="🌲", layout="wide")

# --- 2. 客户端初始化与模型自适应 ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("请在 Settings -> Secrets 中配置 API Key")
    st.stop()

client = genai.Client(api_key=api_key)

# 核心自愈逻辑：自动探测可用模型
@st.cache_resource
def auto_select_model():
    try:
        # 获取当前 Key 支持的所有模型列表
        models_list = [m.name for m in client.models.list()]
        
        # 优先级排序：尝试匹配不同的命名规范
        # 在 2026 年，有的环境需要前缀，有的不需要
        candidates = [
            "gemini-1.5-flash", 
            "models/gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-2.0-flash"
        ]
        
        for cand in candidates:
            if cand in models_list:
                return cand
        
        # 如果预设的都没找到，返回第一个支持生成内容的模型
        return models_list[0]
    except Exception as e:
        st.error(f"无法获取模型列表: {e}")
        return "gemini-1.5-flash" # 保底方案

target_model = auto_select_model()

# --- 3. 界面逻辑 ---
st.title("🌲 林业系统智能办公助手")
st.info(f"✨ 引擎状态：已自动连接至 {target_model}")

# ... (此处保留你之前的 Tab1, Tab2, Tab3 逻辑) ...

# 修改后的调用方式示例：
# res = client.models.generate_content(model=target_model, contents=prompt)
