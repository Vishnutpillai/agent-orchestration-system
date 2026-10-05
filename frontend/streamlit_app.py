import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="Agent Orchestration System",
    page_icon="🤖",
    layout="wide",
)


st.title("🤖 Agent Orchestration System")

st.write(
    "Multi-agent AI system with Supervisor, Specialist Agents, "
    "Reviewer, and Human-in-the-Loop architecture."
)

task = st.text_area(
    "Enter your task",
    placeholder="Example: Explain how machine learning works",
    height=250,

)


if st.button("Run Agent", type="primary"):

    if not task.strip():
        st.warning("Please enter a task.")
    else:

        with st.spinner("Running agent workflow..."):

            response = requests.post(
                f"{API_URL}/run",
                json={"task": task},
                timeout=120,
            )

        if response.status_code == 200:

            data = response.json()

            st.subheader("Final Response")
            st.write(data["final_response"])

            st.subheader("Execution Plan")
            st.json(data["plan"])

            st.subheader("Agent Results")
            st.json(data["results"])

            st.subheader("Reviewer")
            st.json(data["review"])

        else:
            st.error(
                f"API error: {response.status_code}"
            )