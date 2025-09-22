import streamlit as st
import requests
import json
import pandas as pd

# --- Configuration ---
API_BASE_URL = "http://localhost:8000/api"

# Set the browser tab title
ST_PAGE_TITLE = "FinOps AI Copilot" 
# Set the on-screen dashboard header
ST_HEADER_TITLE = "FinOps AI Copilot" 
# Set the title for the KPI section
ST_KPI_SECTION_TITLE = "KPI Dashboard" 

ST_CHAT_TITLE = "Chat with AI Copilot"
API_KPI_URL = f"{API_BASE_URL}/kpi"
API_CHAT_URL = f"{API_BASE_URL}/ask"

# Set Streamlit Page Configuration
st.set_page_config(
    page_title=ST_PAGE_TITLE,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for centering the header title and styling cards
st.markdown("""
    <style>
    /* Center the main header */
    .centered-title {
        text-align: center;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0;
    }

    /* Card styling */
    .stCard {
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 1.5rem;
        background-color: rgba(255, 255, 255, 0.05);
        margin-bottom: 1rem;
    }
    .stCard h3 {
        font-size: 1.5rem;
        font-weight: bold;
    }
    
    /* Style the new centered chat button as a rectangle */
    .stButton button {
        width: 100%;
        max-width: 600px;
        height: 50px;
        font-size: 1.25rem;
        font-weight: bold;
        border-radius: 10px;
        background-color: rgba(45, 45, 45, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
        box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.5);
    }
    </style>
""", unsafe_allow_html=True)

# --- Helper Functions ---

def fetch_kpi_data():
    """Fetches KPI metrics from the FastAPI backend."""
    try:
        response = requests.get(API_KPI_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching KPI data: {e}")
        return None

def send_chat_message(question: str):
    """Sends a question to the RAG chatbot API."""
    try:
        response = requests.post(
            API_CHAT_URL, 
            json={"question": question},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "answer": f"API Error: Could not connect to the AI service. Is Ollama running? ({e})", "sources": "N/A"}

# --- UI Components ---

def render_kpi_cards(kpi_data):
    """Renders the top row of metric cards based on the mockup."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Monthly Spend", 
            value=f"${kpi_data['total_monthly_spend']:,.2f}", 
            delta=f"{kpi_data['monthly_trend_percentage']:+.2f}% vs. Last Month"
        )
    
    with col2:
        st.metric(
            label="Savings Opportunities (Estimated)", 
            value=f"${kpi_data['savings_opportunities']:,.2f}",
            delta="Analyze low-score resources"
        )
        
    with col3:
        st.metric(
            label="Identified Waste Spend", 
            value=f"${kpi_data['waste_metrics']:,.2f}",
            delta="Optimization Score < 0.3"
        )
        
    with col4:
        delta_val = kpi_data['monthly_trend_percentage']
        if delta_val > 10:
            status = "🚨 HIGH ANOMALY"
            color = "red"
        elif delta_val > 0:
            status = "⚠️ Moderate Increase"
            color = "orange"
        else:
            status = "✅ Stable / Decreased"
            color = "green"

        st.markdown(
            f"""
            <div style="
                border: 1px solid {color}; 
                padding: 10px; 
                border-radius: 5px; 
                background-color: rgba(100, 100, 100, 0.1);">
                <small style="color: grey;">Anomaly Detection</small>
                <h3 style="color: {color}; margin: 5px 0 0;">{status}</h3>
                <p style="font-size: 14px; color: grey;">Trend: {delta_val:+.2f}%</p>
            </div>
            """, 
            unsafe_allow_html=True
        )

def render_cost_drivers_chart(kpi_data):
    """Renders the Top 5 Cost Drivers as a bar chart."""
    st.subheader("Top 5 Cost Drivers (Current Month)")
    df = pd.DataFrame(kpi_data['top_5_cost_drivers'])
    df = df.set_index('service')
    st.bar_chart(df, height=350)

def render_chatbot_ui():
    """Renders the dark-themed floating chatbot UI."""
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your AI FinOps Copilot. Ask me about your costs, trends, or savings opportunities."}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about your FinOps data..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking... (Checking Ollama and RAG chain)"):
                api_response = send_chat_message(prompt)
                
                ai_answer = api_response.get("answer", "No response.")
                sources = api_response.get("sources", "N/A")

                st.markdown(ai_answer)
                st.caption(f"Sources: {sources}")
                
                st.session_state.messages.append({"role": "assistant", "content": ai_answer, "sources": sources})

# --- Application Entry Point ---

def main_dashboard():
    """Main function to render the full dashboard."""
    
    # Render the centered main title using markdown and CSS
    st.markdown(f'<h1 class="centered-title">{ST_HEADER_TITLE}</h1>', unsafe_allow_html=True)
    st.divider()

    kpi_data = fetch_kpi_data()

    if kpi_data and kpi_data.get("status") == "success":
        # KPI Dashboard Card
        with st.container(border=True):
            st.markdown(f'### {ST_KPI_SECTION_TITLE}')
            render_kpi_cards(kpi_data)
        
        # Two columns for charts and recommendations
        col_chart, col_reco = st.columns(2)

        with col_chart:
            # Top 5 Cost Drivers Card
            with st.container(border=True):
                render_cost_drivers_chart(kpi_data)
        
        with col_reco:
            # Actionable Recommendations Card
            with st.container(border=True):
                st.subheader("Actionable Recommendations")
                st.info("The AI Copilot has detected a moderate cost change this month.")
                st.markdown(
                    """
                    - **Investigate Trend:** Analyze the service(s) responsible for the current month's trend.
                    - **Right-size Resources:** Check resources with an `optimization_score < 0.3` for immediate savings potential.
                    - **Budget Alert:** Consider setting a threshold for the top cost driver for the next billing cycle.
                    """
                )
                st.caption("These recommendations are based on synthesized KPI data and RAG analysis.")

        # NEW: Centered button at the bottom to launch the chat
        st.markdown("<br>", unsafe_allow_html=True) # Add some spacing
        col_left, col_center, col_right = st.columns([1, 2, 1])
        with col_center:
            # Use a single, persistent state for the chat expander
            if 'chat_expanded' not in st.session_state:
                st.session_state.chat_expanded = False
                
            if st.button("Chat with AI Copilot", key="open_chat_button"):
                st.session_state.chat_expanded = not st.session_state.chat_expanded

        if st.session_state.chat_expanded:
            with st.container(border=True):
                st.subheader(ST_CHAT_TITLE)
                render_chatbot_ui()
    else:
        st.error("Cannot load dashboard data. Ensure the FastAPI backend is running and accessible on http://localhost:8000.")

if __name__ == "__main__":
    main_dashboard()
