import streamlit as st
import requests
import os

# ─── configuration ──────────────────────────────────────────

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="KnowledgeCast AI",
    page_icon="🎙️",
    layout="wide"
)

# ─── session state initialization ───────────────────────────

if "kb_ready" not in st.session_state:
    st.session_state.kb_ready = False
if "total_chunks" not in st.session_state:
    st.session_state.total_chunks = 0
if "sources_processed" not in st.session_state:
    st.session_state.sources_processed = 0

# ─── header ─────────────────────────────────────────────────

st.title("🎙️ KnowledgeCast AI")
st.markdown("Transform your PDFs and articles into summaries, podcasts, audiobooks, and Q&A.")
st.divider()

# ─── section 1: upload sources ──────────────────────────────

st.header("📁 Upload Sources")

col1, col2 = st.columns(2)

with col1:
    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload one or more PDF files to add to your knowledge base"
    )

with col2:
    urls_input = st.text_area(
        "Paste article URLs (one per line)",
        height=150,
        placeholder="https://example.com/article1\nhttps://example.com/article2",
        help="Each URL on a new line"
    )

if st.button("🚀 Process Sources", type="primary", use_container_width=True):
    if not uploaded_files and not urls_input.strip():
        st.error("Please upload at least one PDF or enter a URL.")
    else:
        with st.spinner("Processing sources... this may take a minute."):
            try:
                # prepare files
                files = []
                for f in uploaded_files:
                    files.append(("files", (f.name, f.getvalue(), "application/pdf")))

                # prepare URLs — convert newline separated to comma separated
                urls_comma = ",".join([u.strip() for u in urls_input.strip().split("\n") if u.strip()])

                response = requests.post(
                    f"{API_BASE}/process-sources",
                    files=files if files else None,
                    data={"urls_input": urls_comma}
                )

                if response.status_code == 200:
                    data = response.json()
                    st.session_state.kb_ready = True
                    st.session_state.total_chunks = data["total_chunks"]
                    st.session_state.sources_processed = data["processed_sources"]
                    st.success(f"✅ Knowledge base ready! Processed {data['processed_sources']} sources into {data['total_chunks']} chunks.")

                    if data["failed_sources"] > 0:
                        st.warning(f"⚠️ {data['failed_sources']} source(s) failed to process.")
                        for fail in data["failed_details"]:
                            st.caption(f"Failed: {fail['source']} — {fail['error']}")
                else:
                    st.error(f"Error: {response.json().get('detail', 'Unknown error')}")

            except Exception as e:
                st.error(f"Could not connect to backend: {str(e)}")

# show knowledge base status
if st.session_state.kb_ready:
    st.info(f"📚 Knowledge base active — {st.session_state.sources_processed} sources, {st.session_state.total_chunks} chunks")
else:
    st.warning("⚠️ No knowledge base yet. Upload sources above to get started.")

st.divider()

# ─── section 2: ask questions ───────────────────────────────

st.header("💬 Ask Questions")

query = st.text_input("Ask anything about your uploaded sources", placeholder="What are the main findings?")
top_k = st.slider("Number of context chunks", min_value=3, max_value=10, value=5)

if st.button("🔍 Ask", type="primary"):
    if not st.session_state.kb_ready:
        st.error("Please process sources first.")
    elif not query.strip():
        st.error("Please enter a question.")
    else:
        with st.spinner("Finding answer..."):
            try:
                response = requests.post(
                    f"{API_BASE}/ask",
                    json={"query": query, "top_k": top_k}
                )
                if response.status_code == 200:
                    data = response.json()
                    st.subheader("Answer")
                    st.write(data["answer"])
                    st.caption(f"Sources: {', '.join(data['sources_cited'])} | Chunks used: {data['chunks_retrieved']}")
                else:
                    st.error(response.json().get("detail", "Error getting answer"))
            except Exception as e:
                st.error(f"Connection error: {str(e)}")

st.divider()

# ─── section 3: generate content ────────────────────────────

st.header("🎵 Generate Content")

tab1, tab2 = st.tabs(["🎙️ Podcast", "📖 Audiobook"])

with tab1:
    st.subheader("Generate Podcast")
    pod_topic = st.text_input("Podcast topic", placeholder="e.g. key findings, main concepts", key="pod_topic")
    pod_duration = st.selectbox("Duration (minutes)", [2, 5, 10, 15], key="pod_duration")

    if st.button("🎙️ Generate Podcast", type="primary", key="gen_podcast"):
        if not st.session_state.kb_ready:
            st.error("Please process sources first.")
        elif not pod_topic.strip():
            st.error("Please enter a topic.")
        else:
            with st.spinner(f"Generating {pod_duration} minute podcast... this takes a moment."):
                try:
                    response = requests.post(
                        f"{API_BASE}/generate-podcast",
                        json={
                            "topic": pod_topic,
                            "duration": pod_duration,
                            "top_k": 6,
                            "use_elevenlabs": False
                        },
                        timeout=120
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.success("✅ Podcast generated!")

                        # show script
                        with st.expander("📝 View Script"):
                            st.text(data["script"])

                        # audio player
                        if data.get("audio_file") and os.path.exists(data["audio_file"]):
                            st.subheader("🔊 Listen")
                            st.audio(data["audio_file"])
                        elif data.get("download_url"):
                            st.markdown(f"[⬇️ Download Audio]({API_BASE}{data['download_url']})")

                        st.caption(f"Sources: {', '.join(data['sources_cited'])}")
                    else:
                        st.error(response.json().get("detail", "Generation failed"))
                except requests.Timeout:
                    st.error("Request timed out. Try a shorter duration.")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")

with tab2:
    st.subheader("Generate Audiobook")
    audio_topic = st.text_input("Audiobook topic", placeholder="e.g. chapter summary, key concepts", key="audio_topic")
    audio_duration = st.selectbox("Duration (minutes)", [2, 5, 10, 15], key="audio_duration")

    if st.button("📖 Generate Audiobook", type="primary", key="gen_audiobook"):
        if not st.session_state.kb_ready:
            st.error("Please process sources first.")
        elif not audio_topic.strip():
            st.error("Please enter a topic.")
        else:
            with st.spinner(f"Generating {audio_duration} minute audiobook..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/generate-audiobook",
                        json={
                            "topic": audio_topic,
                            "duration": audio_duration,
                            "top_k": 6
                        },
                        timeout=120
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.success("✅ Audiobook generated!")

                        with st.expander("📝 View Script"):
                            st.text(data["script"])

                        if data.get("audio_file") and os.path.exists(data["audio_file"]):
                            st.subheader("🔊 Listen")
                            st.audio(data["audio_file"])
                        elif data.get("download_url"):
                            st.markdown(f"[⬇️ Download Audio]({API_BASE}{data['download_url']})")

                        st.caption(f"Sources: {', '.join(data['sources_cited'])}")
                    else:
                        st.error(response.json().get("detail", "Generation failed"))
                except requests.Timeout:
                    st.error("Request timed out. Try a shorter duration.")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")

st.divider()

# ─── section 4: summaries ───────────────────────────────────

st.header("📋 Summaries")

sum_tab1, sum_tab2 = st.tabs(["📄 Full Summary", "🎯 Topic Summary"])

with sum_tab1:
    if st.button("📄 Generate Full Summary", type="primary"):
        if not st.session_state.kb_ready:
            st.error("Please process sources first.")
        else:
            with st.spinner("Generating summary..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/generate-summary",
                        json={"topic": ""},
                        timeout=60
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.subheader("Summary")
                        st.write(data["summary"])
                    else:
                        st.error(response.json().get("detail", "Summary failed"))
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")

with sum_tab2:
    sum_topic = st.text_input("Enter topic to summarize", placeholder="e.g. methodology, results, conclusion")
    if st.button("🎯 Generate Topic Summary", type="primary"):
        if not st.session_state.kb_ready:
            st.error("Please process sources first.")
        elif not sum_topic.strip():
            st.error("Please enter a topic.")
        else:
            with st.spinner("Generating topic summary..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/topic-summary",
                        json={"topic": sum_topic, "top_k": 6},
                        timeout=60
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.subheader(f"Summary: {data['topic']}")
                        st.write(data["summary"])
                        st.caption(f"Sources: {', '.join(data['sources_cited'])} | Chunks used: {data['chunks_used']}")
                    else:
                        st.error(response.json().get("detail", "Summary failed"))
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")

# ─── footer ─────────────────────────────────────────────────

st.divider()
st.caption("KnowledgeCast AI — RAG-powered knowledge synthesis platform")