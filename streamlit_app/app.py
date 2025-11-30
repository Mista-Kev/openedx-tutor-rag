import streamlit as st
from streamlit_app.backend import query_rag_backend
# ---- Page config ----
st.set_page_config(
    page_title="RAG UI",
    page_icon="📚",
    layout="wide",
)

# ---- Title + description ----
st.title("RAG UI – Qdrant + Open edX")
st.write(
    "Prototype interface to test retrieval-augmented generation "
    "using the Qdrant plugin."
)

# ---- Sidebar ----
st.sidebar.header("Settings")
top_k = st.sidebar.slider("Number of results", min_value=1, max_value=10, value=5)
show_metadata = st.sidebar.checkbox("Show metadata", value=True)

# ---- Main input area ----
query = st.text_input("Ask a question about the content:", "")

run_clicked = st.button("🔍 Run query")

# ---- placeholder ----
results_placeholder = st.empty()

if run_clicked and query.strip():
    # replace this
    with st.spinner("Querying RAG backend…"):
        results = query_rag_backend(query, top_k=top_k)

    with results_placeholder.container():
        st.subheader("Results")
        for i, r in enumerate(results[:top_k], start=1):
            st.markdown(f"**Result {i}** — score: `{r['score']:.2f}`")
            st.write(r["text"])
            if show_metadata:
                with st.expander("Metadata"):
                    st.json(r["metadata"])
            st.markdown("---")
elif run_clicked:
    st.warning("Please enter a query first.")

