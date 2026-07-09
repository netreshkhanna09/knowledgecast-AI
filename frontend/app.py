import streamlit as st
import requests
import os
import json

# ─── configuration ──────────────────────────────────────────

API_BASE = "https://netreshkhanna09-knowledgecast-ai.hf.space"

st.set_page_config(
    page_title="KnowledgeCast AI",
    page_icon="🎙️",
    layout="wide"
)

# ─── helper functions ────────────────────────────────────────

def call_api(method, endpoint, **kwargs):
    """Helper for all API calls with proper error handling."""
    try:
        response = getattr(requests, method)(
            f"{API_BASE}{endpoint}",
            **kwargs
        )
        return response
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Make sure FastAPI is running on port 8000.")
        return None
    except requests.exceptions.Timeout:
        st.error("Request timed out. Try a shorter duration or smaller files.")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None

def normalize_urls(url_text: str) -> str:
    """Convert newline-separated URLs to comma-separated."""
    urls = [u.strip() for u in url_text.strip().split("\n") if u.strip()]
    return ",".join(urls)

def check_backend() -> bool:
    """Check if FastAPI backend is running."""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=30)
        return response.status_code == 200
    except:
        return False

def play_audio(download_url: str):
    """Fetch audio from API and play in Streamlit."""
    try:
        audio_response = requests.get(f"{API_BASE}{download_url}", timeout=30)
        if audio_response.status_code == 200:
            st.audio(audio_response.content, format="audio/mp3")
        else:
            st.warning("Could not load audio player. Use download link below.")
    except Exception as e:
        st.warning(f"Audio player error: {str(e)}")

# ─── backend check ───────────────────────────────────────────

with st.spinner("Connecting to backend... (may take 30-60 seconds on first load)"):
    if not check_backend():
        st.error("⚠️ Backend not responding. Please try refreshing the page in 30 seconds.")
        st.stop()

# ─── session state ───────────────────────────────────────────

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
        accept_multiple_files=True
    )

with col2:
    urls_input = st.text_area(
        "Paste article URLs (one per line)",
        height=150,
        placeholder="https://example.com/article1\nhttps://example.com/article2"
    )

if st.button("🚀 Process Sources", type="primary", use_container_width=True):
    if not uploaded_files and not urls_input.strip():
        st.error("Please upload at least one PDF or enter a URL.")
    else:
        status = st.empty()
        with st.spinner("Processing sources..."):
            status.write("📄 Preparing files...")

            files = []
            for f in uploaded_files:
                files.append(("files", (f.name, f.getvalue(), "application/pdf")))

            urls_comma = normalize_urls(urls_input)

            status.write("⚙️ Extracting, chunking and embedding...")

            response = call_api(
                "post",
                "/process-sources",
                files=files if files else None,
                data={"urls_input": urls_comma},
                timeout=180
            )

            if response and response.status_code == 200:
                data = response.json()
                st.session_state.kb_ready = True
                st.session_state.total_chunks = data["total_chunks"]
                st.session_state.sources_processed = data["processed_sources"]
                status.empty()
                st.success(f"✅ Knowledge base ready! {data['processed_sources']} sources → {data['total_chunks']} chunks.")

                if data["failed_sources"] > 0:
                    st.warning(f"⚠️ {data['failed_sources']} source(s) failed.")
                    for fail in data["failed_details"]:
                        st.caption(f"Failed: {fail['source']} — {fail['error']}")
            elif response:
                status.empty()
                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")

if st.session_state.kb_ready:
    st.info(f"📚 Active knowledge base — {st.session_state.sources_processed} sources, {st.session_state.total_chunks} chunks")
else:
    st.warning("⚠️ No knowledge base yet. Upload sources above.")

st.divider()

# ─── section 2: ask questions ───────────────────────────────

st.header("💬 Ask Questions")

query = st.text_input("Ask anything about your uploaded sources", placeholder="What are the main findings?")
top_k = st.slider("Context chunks", min_value=3, max_value=10, value=5)

if st.button("🔍 Ask", type="primary"):
    if not st.session_state.kb_ready:
        st.error("Please process sources first.")
    elif not query.strip():
        st.error("Please enter a question.")
    else:
        with st.spinner("Finding answer..."):
            response = call_api("post", "/ask", json={"query": query, "top_k": top_k}, timeout=60)
            if response and response.status_code == 200:
                data = response.json()
                st.subheader("Answer")
                st.write(data["answer"])
                st.caption(f"Sources: {', '.join(data['sources_cited'])} | Chunks: {data['chunks_retrieved']}")
            elif response:
                st.error(response.json().get("detail", "Error"))

st.divider()

# ─── section 3: generate content ────────────────────────────

st.header("🎵 Generate Content")

tab1, tab2 = st.tabs(["🎙️ Podcast", "📖 Audiobook"])

with tab1:
    pod_topic = st.text_input("Podcast topic", placeholder="key findings, main concepts", key="pod_topic")
    pod_duration = st.selectbox("Duration (minutes)", [2, 5, 10, 15], key="pod_duration")

    if st.button("🎙️ Generate Podcast", type="primary", key="gen_podcast"):
        if not st.session_state.kb_ready:
            st.error("Please process sources first.")
        elif not pod_topic.strip():
            st.error("Please enter a topic.")
        else:
            status_box = st.empty()
            result_container = st.container()

            try:
                with requests.post(
                    f"{API_BASE}/generate-podcast-stream",
                    json={
                        "topic": pod_topic,
                        "duration": pod_duration,
                        "top_k": 6,
                        "use_elevenlabs": False
                    },
                    stream=True,
                    timeout=300
                ) as response:

                    final_result = None

                    for line in response.iter_lines():
                        if not line:
                            continue
                        decoded = line.decode("utf-8")
                        if not decoded.startswith("data: "):
                            continue
                        message = decoded[6:]  # strip "data: " prefix

                        if message.startswith("ERROR:"):
                            status_box.error(message[6:])
                            break
                        elif message.startswith("RESULT:"):
                            final_result = json.loads(message[7:])
                            status_box.success("✅ Podcast ready!")
                        else:
                            status_box.info(message)

                    if final_result:
                        with result_container:
                            with st.expander("📝 View Script"):
                                st.text(final_result["script"])
                            if final_result.get("download_url"):
                                st.subheader("🔊 Listen")
                                play_audio(final_result["download_url"])
                                st.markdown(f"[⬇️ Download MP3]({API_BASE}{final_result['download_url']})")
                            st.caption(f"Sources: {', '.join(final_result['sources_cited'])}")

            except requests.exceptions.Timeout:
                status_box.error("Request timed out. Try a shorter duration.")
            except Exception as e:
                status_box.error(f"Connection error: {str(e)}")

with tab2:
    audio_topic = st.text_input("Audiobook topic", placeholder="chapter summary, key concepts", key="audio_topic")
    audio_duration = st.selectbox("Duration (minutes)", [2, 5, 10, 15], key="audio_duration")

    if st.button("📖 Generate Audiobook", type="primary", key="gen_audiobook"):
        if not st.session_state.kb_ready:
            st.error("Please process sources first.")
        elif not audio_topic.strip():
            st.error("Please enter a topic.")
        else:
            status_box = st.empty()
            result_container = st.container()

            try:
                with requests.post(
                    f"{API_BASE}/generate-audiobook-stream",
                    json={
                        "topic": audio_topic,
                        "duration": audio_duration,
                        "top_k": 6
                    },
                    stream=True,
                    timeout=300
                ) as response:

                    final_result = None

                    for line in response.iter_lines():
                        if not line:
                            continue
                        decoded = line.decode("utf-8")
                        if not decoded.startswith("data: "):
                            continue
                        message = decoded[6:]

                        if message.startswith("ERROR:"):
                            status_box.error(message[6:])
                            break
                        elif message.startswith("RESULT:"):
                            final_result = json.loads(message[7:])
                            status_box.success("✅ Audiobook ready!")
                        else:
                            status_box.info(message)

                    if final_result:
                        with result_container:
                            with st.expander("📝 View Script"):
                                st.text(final_result["script"])
                            if final_result.get("download_url"):
                                st.subheader("🔊 Listen")
                                play_audio(final_result["download_url"])
                                st.markdown(f"[⬇️ Download MP3]({API_BASE}{final_result['download_url']})")
                            st.caption(f"Sources: {', '.join(final_result['sources_cited'])}")

            except requests.exceptions.Timeout:
                status_box.error("Request timed out. Try a shorter duration.")
            except Exception as e:
                status_box.error(f"Connection error: {str(e)}")
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
                response = call_api("post", "/generate-summary", json={"topic": ""}, timeout=120)
                if response and response.status_code == 200:
                    data = response.json()
                    st.subheader("Summary")
                    st.write(data["summary"])
                elif response:
                    st.error(response.json().get("detail", "Failed"))

with sum_tab2:
    sum_topic = st.text_input("Topic to summarize", placeholder="methodology, results, conclusion")
    if st.button("🎯 Generate Topic Summary", type="primary"):
        if not st.session_state.kb_ready:
            st.error("Please process sources first.")
        elif not sum_topic.strip():
            st.error("Please enter a topic.")
        else:
            with st.spinner("Generating topic summary..."):
                response = call_api("post", "/topic-summary", json={"topic": sum_topic, "top_k": 6}, timeout=60)
                if response and response.status_code == 200:
                    data = response.json()
                    st.subheader(f"Summary: {data['topic']}")
                    st.write(data["summary"])
                    st.caption(f"Sources: {', '.join(data['sources_cited'])} | Chunks: {data['chunks_used']}")
                elif response:
                    st.error(response.json().get("detail", "Failed"))

st.divider()
st.caption("KnowledgeCast AI — RAG-powered knowledge synthesis platform")

st.divider()

# ─── section 5: history ─────────────────────────────────────

st.header("🕓 Generation History")

# type filter
filter_type = st.selectbox(
    "Filter by type",
    ["All", "podcast", "audiobook", "summary", "topic_summary", "qa"],
    key="history_filter"
)

col_refresh, col_clear = st.columns([1, 5])
with col_refresh:
    refresh = st.button("🔄 Refresh", key="refresh_history")

if st.button("📜 Load History", type="primary", key="load_history") or refresh:
    response = call_api("get", "/history", timeout=10)

    if response and response.status_code == 200:
        data = response.json()
        records = data["records"]

        # apply filter
        if filter_type != "All":
            records = [r for r in records if r["output_type"] == filter_type]

        if not records:
            st.info("No history found. Generate something first.")
        else:
            st.success(f"Found {len(records)} record(s)")

            for record in records:
                # build a readable label for each record
                type_emoji = {
                    "podcast": "🎙️",
                    "audiobook": "📖",
                    "summary": "📄",
                    "topic_summary": "🎯",
                    "qa": "💬"
                }.get(record["output_type"], "📝")

                label = f"{type_emoji} {record['output_type'].upper()} — {record['topic'] or 'no topic'} — {record['created_at']}"

                with st.expander(label):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.caption(f"**Type:** {record['output_type']}")
                        st.caption(f"**Topic:** {record['topic'] or '—'}")
                    with col2:
                        st.caption(f"**Sources:** {record['sources'] or '—'}")
                        st.caption(f"**Duration:** {str(record['duration']) + ' min' if record['duration'] else '—'}")

                    st.markdown("**Generated Content:**")
                    st.write(record["content"])

                    # replay audio if available
                    if record.get("audio_path"):
                        filename = os.path.basename(record["audio_path"])
                        st.subheader("🔊 Replay Audio")
                        play_audio(f"/download-audio/{filename}")
                        st.markdown(f"[⬇️ Download MP3]({API_BASE}/download-audio/{filename})")

                    # delete button
                    if st.button(f"🗑️ Delete", key=f"delete_{record['id']}"):
                        del_response = call_api("delete", f"/history/{record['id']}", timeout=10)
                        if del_response and del_response.status_code == 200:
                            st.success("Deleted. Click Refresh to update.")
                        else:
                            st.error("Could not delete.")
    elif response:
        st.error(response.json().get("detail", "Failed to load history"))