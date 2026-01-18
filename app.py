import streamlit as st
from google import genai
from google.genai import types
import pypdf
from docx import Document

# --- 1. 页面配置 ---
st.set_page_config(page_title="林业办公智能助手", page_icon="🌲", layout="wide")

# --- 2. 从 Cloud Secrets 读取 Key ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("请在 Streamlit Cloud 后台配置 API Key！")
    st.stop()

client = genai.Client(api_key=api_key)

# --- 3. 辅助函数 ---
def parse_doc(file):
    if file.type == "application/pdf":
        return "".join([p.extract_text() for p in pypdf.PdfReader(file).pages])
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return "\n".join([p.text for p in Document(file).paragraphs])
    return ""

# --- 4. 界面设计 ---
st.title("🌲 林业系统智能办公助手")
st.caption("妈妈专用的公文创作、识物与润色工具")

tab1, tab2, tab3 = st.tabs(["📝 材料处理", "📸 拍照识物", "🏗️ 填空起草"])

# --- 材料处理 ---
with tab1:
    col_a, col_b = st.columns([2, 1])
    with col_a:
        u_file = st.file_uploader("上传您的原稿 (Word/PDF)", type=["docx", "pdf"])
        u_text = st.text_area("或者直接输入内容：", height=200)
    with col_b:
        task = st.radio("您想怎么处理？", ["✨ 全文润色（正式风）", "📝 总结要点", "🧐 合规性检查"])
        if st.button("开始处理", type="primary"):
            content = parse_doc(u_file) if u_file else u_text
            if content:
                with st.spinner("处理中..."):
                    res = client.models.generate_content(
                        model="gemini-2.0-flash", 
                        contents=f"请作为林业局资深文秘，对以下内容进行{task}：\n\n{content}"
                    )
                    st.markdown(res.text)
            else:
                st.warning("请先提供内容哦")

# --- 拍照识物 ---
with tab2:
    st.subheader("巡护路上拍的照片，传上来看看")
    u_img = st.file_uploader("上传动植物照片", type=["jpg", "png", "jpeg"])
    if u_img:
        st.image(u_img, width=400)
        if st.button("识别并生成材料"):
            with st.spinner("AI 正在分析..."):
                res = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=["请识别图中的生物，并写一段专业的林业科普或鉴定报告。", 
                              types.Part.from_bytes(data=u_img.getvalue(), mime_type=u_img.type)]
                )
                st.markdown(res.text)

# --- 填空起草 ---
with tab3:
    st.subheader("做个选择题，AI 帮您写")
    mode = st.selectbox("请选择公文类型", ["湿地巡护日志", "春季防火通知", "野生动物保护建议"])
    
    with st.container(border=True):
        if mode == "湿地巡护日志":
            t1 = st.text_input("巡护地点", "XX 湿地保护区")
            t2 = st.text_input("观察物种", "黑鹳、天鹅等")
            t3 = st.text_area("现场情况", "水位平稳，植被生长良好，无盗猎行为。")
            prompt = f"请写一份专业的湿地巡护日志。地点：{t1}，物种：{t2}，情况：{t3}。"
        elif mode == "春季防火通知":
            t1 = st.text_input("通知对象", "各护林站、周边村民")
            t2 = st.text_input("禁火日期", "3月1日至5月1日")
            prompt = f"请起草一份林业局春季防火通知。对象：{t1}，日期：{t2}。要求语气严谨庄重。"
    
    if st.button("一键生成全文"):
        with st.spinner("起草中..."):
            res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            st.markdown(res.text)
            st.download_button("下载材料", res.text, "起草稿.txt")
