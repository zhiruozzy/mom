import streamlit as st
from google import genai
import pypdf
from docx import Document

# --- 1. 页面配置 ---
st.set_page_config(page_title="林业办公智能助手", page_icon="🌲", layout="wide")

# --- 2. 初始化客户端 ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("请在 Settings -> Secrets 中配置 API Key")
    st.stop()

client = genai.Client(api_key=api_key)

# --- 3. 核心修复：自动探测并选择可用模型 ---
@st.cache_resource
def get_best_model():
    try:
        # 获取当前 Key 支持的所有模型
        all_models = [m.name for m in client.models.list()]
        
        # 定义偏好顺序（1.5-flash 比较稳健）
        # 注意：SDK 有时返回带 models/ 的名称，有时不带，这里做兼容处理
        preferences = [
            "gemini-1.5-flash", 
            "models/gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-2.0-flash"
        ]
        
        for p in preferences:
            if p in all_models:
                # 关键：移除 'models/' 前缀，因为新版 generate_content 内部会自动添加
                return p.replace("models/", "")
        
        # 如果都没找到，返回第一个支持生成内容的模型
        return all_models[0].replace("models/", "")
    except Exception as e:
        st.error(f"探测模型失败: {e}")
        return "gemini-1.5-flash"

working_model = get_best_model()

# --- 4. 辅助函数 ---
def parse_doc(file):
    try:
        if file.type == "application/pdf":
            return "".join([p.extract_text() for p in pypdf.PdfReader(file).pages])
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(file).paragraphs])
    except Exception:
        return ""
    return ""

# --- 5. 界面设计 ---
st.title("🌲 林业系统智能办公助手")
st.caption(f"当前运行引擎：{working_model}") # 显示当前真正起作用的模型

tab1, tab2, tab3 = st.tabs(["📝 材料处理", "📸 拍照识物", "🏗️ 填空起草"])

# --- 材料处理 ---
with tab1:
    u_file = st.file_uploader("上传原稿 (Word/PDF)", type=["docx", "pdf"])
    u_text = st.text_area("输入文字：", height=200)
    task = st.radio("处理目标：", ["✨ 润色", "📝 摘要"])
    
    if st.button("开始处理", type="primary"):
        content = parse_doc(u_file) if u_file else u_text
        if content:
            with st.spinner("AI 正在思考..."):
                try:
                    res = client.models.generate_content(
                        model=working_model, 
                        contents=f"请作为林业专家，对以下内容进行{task}：\n\n{content}"
                    )
                    st.markdown(res.text)
                except Exception as e:
                    if "429" in str(e):
                        st.error("⚠️ 现在用的人太多了，请等一分钟再试哦。")
                    else:
                        st.error(f"抱歉，出错了：{e}")

# --- 填空起草 (妈妈最常用的功能) ---
with tab3:
    mode = st.selectbox("文件类型", ["湿地巡护日志", "春季防火通知"])
    # 此处省略具体表单代码，确保调用时使用 model=working_model
    if st.button("一键生成全文"):
        with st.spinner("起草中..."):
            try:
                # 示例 Prompt 逻辑
                res = client.models.generate_content(model=working_model, contents="请起草一份林业材料...")
                st.markdown(res.text)
            except Exception as e:
                st.error(f"生成失败: {e}")
