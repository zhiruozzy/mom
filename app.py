import streamlit as st
from google import genai
import pypdf
from docx import Document

# --- 1. 页面配置 ---
st.set_page_config(page_title="林业办公智能助手", page_icon="🌲", layout="wide")

# --- 2. 初始化客户端与模型自动选择 ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("请在 Settings -> Secrets 中配置 API Key")
    st.stop()

client = genai.Client(api_key=api_key)

# 自动选择最合适的模型（优先 1.5-flash，因为它配额多且稳定）
@st.cache_resource
def get_working_model():
    available_models = [m.name for m in client.models.list()]
    # 尝试顺序：1.5-flash -> 1.5-flash-latest -> 1.5-flash-002
    target_models = ["models/gemini-1.5-flash", "models/gemini-1.5-flash-latest", "models/gemini-1.5-flash-002"]
    
    for target in target_models:
        if target in available_models:
            # 返回不带 'models/' 前缀的名称，这是新版 SDK 的偏好
            return target.replace("models/", "")
    
    # 如果都没找到，返回第一个支持生成的模型
    return available_models[0].replace("models/", "")

working_model = get_working_model()

# --- 3. 辅助函数 ---
def parse_doc(file):
    try:
        if file.type == "application/pdf":
            return "".join([p.extract_text() for p in pypdf.PdfReader(file).pages])
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(file).paragraphs])
    except Exception as e:
        st.error(f"解析文件失败: {e}")
    return ""

# --- 4. 界面展示 ---
st.title("🌲 林业系统智能办公助手")
st.info(f"当前运行模式：智能优化态 ({working_model})") # 方便排查

tab1, tab2, tab3 = st.tabs(["📝 材料处理", "📸 拍照识物", "🏗️ 填空起草"])

# 以【材料处理】为例的调用逻辑
with tab1:
    u_file = st.file_uploader("上传 Word/PDF", type=["docx", "pdf"])
    u_text = st.text_area("或者输入内容：", height=200)
    task = st.radio("处理目标：", ["✨ 润色", "📝 摘要"])
    
    if st.button("开始处理", type="primary"):
        content = parse_doc(u_file) if u_file else u_text
        if content:
            with st.spinner("AI 正在工作中..."):
                try:
                    # 使用探测到的 working_model
                    res = client.models.generate_content(
                        model=working_model, 
                        contents=f"请作为林业专家，对以下内容进行{task}：\n\n{content}"
                    )
                    st.markdown(res.text)
                except Exception as e:
                    # 针对 429 配额错误的温馨提示
                    if "429" in str(e):
                        st.error("⚠️ 妈妈，现在用的人太多了，请等一分钟再试。")
                    else:
                        st.error(f"出错了: {e}")
        else:
            st.warning("请填入内容")

# ... (Tab2 和 Tab3 的逻辑类似，确保 model=working_model 即可)
