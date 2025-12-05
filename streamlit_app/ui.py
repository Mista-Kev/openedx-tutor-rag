# Adapted from https://github.com/streamlit/demo-ai-assistant
# UI only – backend will be provided by backend.query_rag_backend in this project

from collections import namedtuple
import datetime
import textwrap
import time
import pathlib
import streamlit as st
from backend import query_rag_backend

st.set_page_config(page_title="OpenEdX Insights", page_icon="👾")

def load_css():
    css_path = pathlib.Path(__file__).parent / "styles.css"
    css = css_path.read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Default settings when sidebar is hidden
top_k = 5
show_metadata = True
show_scores = True  # reserved if you use it later

# -----------------------------------------------------------------------------
# Config & constants

HISTORY_LENGTH = 5
MIN_TIME_BETWEEN_REQUESTS = datetime.timedelta(seconds=3)

DEBUG_MODE = st.query_params.get("debug", "false").lower() == "true"

INSTRUCTIONS = textwrap.dedent("""
    - You are a helpful assistant focused on answering questions about
      Open edX content and related learning materials.
    - Use context and history to provide a coherent answer.
    - Use markdown such as headers, code blocks, bullet points, and backticks
      for inline code.
    - Assume the user is a newbie.
    - Be brief, but clear.
""")

SUGGESTIONS = {
    ":material/school: Find a course section": (
        "Show me all course sections related to introduction to Python."
    ),
    ":material/search: Search course content": (
        "Search the content for topics about graded assignments."
    ),
    ":material/analytics: Analyze learner activity": (
        "What content do learners interact with most in this course?"
    ),
    ":material/help: Clarify a concept": (
        "Explain the difference between graded and ungraded components."
    ),
    ":material/insights: Summarize a course": (
        "Give me a short summary of the main topics covered in this course."
    ),
}

TaskInfo = namedtuple("TaskInfo", ["name", "function", "args"])
TaskResult = namedtuple("TaskResult", ["name", "result"])


def history_to_text(chat_history):
    """Converts chat history into a string (mostly for future use / debugging)."""
    return "\n".join(f"[{h['role']}]: {h['content']}" for h in chat_history)


def show_feedback_controls(message_index: int) -> None:
    """Shows the 'How did I do?' control under an assistant message."""
    st.write("")

    with st.popover("How did I do?"):
        with st.form(key=f"feedback-{message_index}", border=False):
            with st.container(gap=None):
                st.markdown(":small[Rating]")
                rating = st.feedback(options="stars")

            details = st.text_area("More information (optional)")

            if st.checkbox("Include chat history with my feedback", True):
                relevant_history = st.session_state.messages[:message_index]
            else:
                relevant_history = []

            ""  # Add some space

            if st.form_submit_button("Send feedback"):
                # TODO: Submit feedback somewhere (e.g. log or API)
                _ = rating, details, relevant_history
                pass


@st.dialog("Legal disclaimer")
def show_disclaimer_dialog():
    st.caption("""
        This assistant is an internal prototype for exploring Open edX content.
        Answers may be incomplete, inaccurate, or biased. Always verify results
        before using them for important decisions. Do not enter private,
        sensitive, personal, or regulated data.
    """)


# -----------------------------------------------------------------------------
# Main app entrypoint


def render_app() -> None:
    load_css()
    # ----- Title row -----
    title_row = st.container(
        horizontal=True,
        vertical_alignment="bottom",
    )

    with title_row:
        st.title("What do you want to know?", anchor=False, width="stretch")

    user_just_asked_initial_question = (
        "initial_question" in st.session_state and st.session_state.initial_question
    )

    user_just_clicked_suggestion = (
        "selected_suggestion" in st.session_state
        and st.session_state.selected_suggestion
    )

    user_first_interaction = (
        user_just_asked_initial_question or user_just_clicked_suggestion
    )

    has_message_history = (
        "messages" in st.session_state and len(st.session_state.messages) > 0
    )

    # ----- Initial screen -----
    if not user_first_interaction and not has_message_history:
        st.session_state.messages = []

        with st.container():
            st.chat_input("Type a question", key="initial_question")

            selected_suggestion = st.pills(
                label="Examples",
                label_visibility="collapsed",
                options=SUGGESTIONS.keys(),
                key="selected_suggestion",
            )

        st.button(
            "&nbsp;:small[:gray[:material/balance: Legal disclaimer]]",
            type="tertiary",
            on_click=show_disclaimer_dialog,
        )

        st.stop()

    # ----- Chat input after first interaction -----
    user_message = st.chat_input("Ask a follow-up…")

    if not user_message:
        if user_just_asked_initial_question:
            user_message = st.session_state.initial_question
        if user_just_clicked_suggestion:
            user_message = SUGGESTIONS[st.session_state.selected_suggestion]

    with title_row:

        def clear_conversation():
            st.session_state.messages = []
            st.session_state.initial_question = None
            st.session_state.selected_suggestion = None

        st.button(
            "Restart",
            icon=":material/refresh:",
            on_click=clear_conversation,
        )

    if "prev_question_timestamp" not in st.session_state:
        st.session_state.prev_question_timestamp = datetime.datetime.fromtimestamp(0)

    # ----- Render existing history -----
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.container()  # Fix ghost message bug.

            st.markdown(message["content"])

            if message["role"] == "assistant":
                show_feedback_controls(i)

    # ----- Handle new user message -----
    if user_message:
        # Avoid LaTeX interpretation of "$"
        user_message = user_message.replace("$", r"\$")

        # Display user message
        with st.chat_message("user"):
            st.text(user_message)

        # Display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Searching your Open edX content…"):
                # Rate-limit the input if needed.
                question_timestamp = datetime.datetime.now()
                time_diff = (
                    question_timestamp - st.session_state.prev_question_timestamp
                )
                st.session_state.prev_question_timestamp = question_timestamp

                if time_diff < MIN_TIME_BETWEEN_REQUESTS:
                    time.sleep(time_diff.seconds + time_diff.microseconds * 0.001)

                # Call backend to retrieve results
                results = query_rag_backend(user_message)

            # Build a markdown string from the retrieval results
            lines = []
            for i, r in enumerate(results, start=1):
                score = r.get("score", None)
                text = r.get("text", "")
                metadata = r.get("metadata", {})

                header = f"**Result {i}**"
                if isinstance(score, (float, int)):
                    header += f" — score: `{score:.2f}`"

                lines.append(header)
                lines.append("")
                lines.append(text)

                if show_metadata and metadata:
                    lines.append("")
                    lines.append("<details><summary>Metadata</summary>")
                    lines.append("```json")
                    # basic pretty print
                    for k, v in metadata.items():
                        lines.append(f"{k}: {v}")
                    lines.append("```")
                    lines.append("</details>")

                lines.append("---")

            response_text = "\n".join(lines) if lines else "_No results found._"

            # Show the response in the chat bubble
            st.markdown(response_text)

            # Update chat history
            st.session_state.messages.append(
                {"role": "user", "content": user_message}
            )
            st.session_state.messages.append(
                {"role": "assistant", "content": response_text}
            )

            # Feedback
            show_feedback_controls(len(st.session_state.messages) - 1)


# Optional: allow running this file directly with `streamlit run ui.py`
if __name__ == "__main__":
    render_app()