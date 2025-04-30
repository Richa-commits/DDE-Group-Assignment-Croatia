from pydantic_ai import Agent
from httpx import AsyncClient
import streamlit as st
import asyncio
import sys
import os
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Web_Search_Agent.src import agent, AgentDeps

# Import all the message part classes from Pydantic AI
from pydantic_ai.messages import ModelRequest, ModelResponse, PartDeltaEvent, PartStartEvent, TextPartDelta

# Read company data from Excel
@st.cache_data
def load_company_data():
    try:
        df = pd.read_excel('croatia + company descriptions.xlsx')
        cols = ['Company name Latin alphabet', 'Company Description', 'Region in country clean']
        for year in range(2019, 2024):
            colname = f'HighGrowthFirm {year}'
            if colname in df.columns:
                cols.append(colname)
        return df[cols]
    except Exception as e:
        st.error(f"Error loading company data: {str(e)}")
        base_cols = ['Company name Latin alphabet', 'Company Description', 'Region in country clean']
        hgf_cols = [f'HighGrowthFirm {year}' for year in range(2019, 2024)]
        return pd.DataFrame(columns=base_cols + hgf_cols)

# Custom color palette
COLORS = {
    'primary': '#3b82f6',      # Blue
    'secondary': '#10b981',    # Green
    'accent': '#ef4444',       # Red
    'background': '#f8fafc',   # Light gray
    'card': '#ffffff',         # White
    'text': '#1e293b',         # Dark gray
    'border': '#e2e8f0',       # Light border
    'gradient_start': '#2563eb',  # Dark blue
    'gradient_end': '#3b82f6'     # Light blue
}

# Custom CSS for modern design
st.markdown(f"""
    <style>
    .main {{
        background-color: {COLORS['background']};
    }}
    .stApp {{
        max-width: 1200px;
        margin: 0 auto;
    }}
    .header-gradient {{
        background: linear-gradient(135deg, {COLORS['gradient_start']}, {COLORS['gradient_end']});
        padding: 3rem 2rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }}
    .header-title {{
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }}
    .header-subtitle {{
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.25rem;
        font-weight: 400;
    }}
    .metric-card {{
        background-color: {COLORS['card']};
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        border: 1px solid {COLORS['border']};
    }}
    .metric-card:hover {{
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transform: translateY(-2px);
    }}
    .market-share-card {{
        border-left: 4px solid {COLORS['primary']};
    }}
    .growth-rate-card {{
        border-left: 4px solid {COLORS['secondary']};
    }}
    .competitors-card {{
        border-left: 4px solid {COLORS['accent']};
    }}
    .chart-card {{
        background-color: {COLORS['card']};
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        border: 1px solid {COLORS['border']};
    }}
    .data-table {{
        background-color: {COLORS['card']};
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        border: 1px solid {COLORS['border']};
    }}
    .chat-container {{
        background-color: {COLORS['card']};
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        margin-top: 2rem;
        border: 1px solid {COLORS['border']};
    }}
    .stChatMessage {{
        padding: 1rem;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
    }}
    .user-message {{
        background-color: #f0f9ff;
    }}
    .assistant-message {{
        background-color: #f8fafc;
    }}
    .company-details {{
        background-color: {COLORS['card']};
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        margin-top: 1rem;
        border: 1px solid {COLORS['border']};
    }}
    .metric-value {{
        font-size: 1.75rem;
        font-weight: 700;
        color: {COLORS['text']};
        margin: 0.5rem 0;
    }}
    .metric-label {{
        font-size: 0.875rem;
        color: #64748b;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    .metric-change {{
        font-size: 0.875rem;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }}
    .positive-change {{
        color: {COLORS['secondary']};
    }}
    .negative-change {{
        color: {COLORS['accent']};
    }}
    .sidebar-section {{
        margin-bottom: 1.5rem;
    }}
    .sidebar-title {{
        font-size: 1.125rem;
        font-weight: 600;
        color: {COLORS['text']};
        margin-bottom: 0.5rem;
    }}
    .divider {{
        height: 1px;
        background-color: {COLORS['border']};
        margin: 1rem 0;
    }}
    .dataframe {{
        width: 100%;
        border-collapse: collapse;
    }}
    .dataframe th {{
        background-color: {COLORS['primary']};
        color: white;
        padding: 0.75rem;
        text-align: left;
        font-weight: 600;
    }}
    .dataframe td {{
        padding: 0.75rem;
        border-bottom: 1px solid {COLORS['border']};
    }}
    .dataframe tr:hover {{
        background-color: {COLORS['background']};
    }}
    </style>
""", unsafe_allow_html=True)

# Add after COLORS definition
ANIMATION_CSS = """
@keyframes fadeInUp {
  0% { opacity: 0; transform: translateY(40px); }
  100% { opacity: 1; transform: translateY(0); }
}
.fade-in-up {
  animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1);
}
@media (max-width: 768px) {
  .responsive-grid { display: flex; flex-direction: column; gap: 1.5rem; }
  .stat-cards { flex-direction: column !important; }
}
@media (min-width: 769px) {
  .responsive-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
  .stat-cards { display: flex; flex-direction: row; gap: 1.5rem; }
}
.stat-card {
  background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
  border-radius: 1.25rem;
  box-shadow: 0 4px 24px 0 rgba(59,130,246,0.10), 0 1.5px 6px 0 rgba(16,185,129,0.08);
  padding: 2rem 2.5rem;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 180px;
  margin-bottom: 1.5rem;
  animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1);
  color: #fff;
  position: relative;
  overflow: hidden;
}
.stat-label {
  color: rgba(255,255,255,0.85);
  font-size: 1.05rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
  letter-spacing: 0.01em;
}
.stat-value {
  color: #fff;
  font-size: 2.2rem;
  font-weight: 700;
  letter-spacing: 0.01em;
}
.insight-card, .data-table, .chart-card, .chat-container {
  background: #fff;
  border-radius: 1.25rem;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.07);
  padding: 2rem 1.5rem 1.5rem 1.5rem;
  margin-bottom: 2rem;
  animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1);
}
.insight-card { margin-bottom: 2.5rem; }
.filter-section {
  background: #f8fafc;
  border-radius: 1rem;
  box-shadow: 0 1px 4px 0 rgba(59,130,246,0.04);
  padding: 1.25rem 1rem 1rem 1rem;
  margin-bottom: 1.5rem;
  border: 1px solid #e2e8f0;
  animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1);
}
.stSelectbox > div, .stButton > button, .stSlider > div {
  border-radius: 0.75rem !important;
  border: 1.5px solid #e2e8f0 !important;
  box-shadow: 0 1px 4px 0 rgba(59,130,246,0.04);
  transition: border 0.2s, box-shadow 0.2s;
}
.stSelectbox > div:hover, .stButton > button:hover, .stSlider > div:hover {
  border: 1.5px solid #3b82f6 !important;
  box-shadow: 0 2px 8px 0 rgba(59,130,246,0.10);
}
.stTextInput > div > input {
  border-radius: 0.75rem !important;
  border: 1.5px solid #e2e8f0 !important;
  box-shadow: 0 1px 4px 0 rgba(59,130,246,0.04);
  padding: 0.7rem 1rem !important;
  font-size: 1.08rem !important;
}
.stTextInput > div > input:focus {
  border: 1.5px solid #3b82f6 !important;
  box-shadow: 0 2px 8px 0 rgba(59,130,246,0.10);
}
.stForm > div {
  gap: 0.5rem !important;
}
@media (max-width: 768px) {
  .insight-card, .data-table, .chart-card, .chat-container, .filter-section { padding: 1rem !important; }
  .header-title { font-size: 1.5rem !important; }
  .header-subtitle { font-size: 1rem !important; }
  .stat-card { padding: 1.2rem 1rem; font-size: 1rem; }
}
"""
st.markdown(f"<style>{ANIMATION_CSS}</style>", unsafe_allow_html=True)

# Add after COLORS definition
EXTRA_CSS = """
/* Zebra stripes and hover for table */
.dataframe tbody tr:nth-child(odd) { background: #f3f6fa; }
.dataframe tbody tr:nth-child(even) { background: #eaf1fb; }
.dataframe tbody tr:hover { background: #dbeafe !important; }
/* Topic tags as pill chips */
.topic-tags { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1rem; }
.topic-tag {
  display: inline-block;
  background: linear-gradient(90deg, #a7f3d0 0%, #bae6fd 100%);
  color: #2563eb;
  font-weight: 600;
  border-radius: 999px;
  padding: 0.4em 1.1em;
  font-size: 1.05em;
  box-shadow: 0 1px 4px 0 rgba(59,130,246,0.07);
  border: 1.5px solid #e0e7ef;
  transition: background 0.2s, color 0.2s;
}
.topic-tag:hover { background: #f0fdf4; color: #059669; }
/* Animated header and insight card */
.animated-header, .animated-insight { opacity: 0; transform: translateY(-40px); animation: fadeInDown 1s 0.1s forwards; }
.animated-insight { animation-delay: 0.5s; }
@keyframes fadeInDown {
  to { opacity: 1; transform: translateY(0); }
}
/* Collapsible sidebar */
.sidebar-collapsible { background: #f3f6fa; border-radius: 1.2rem; box-shadow: 0 2px 8px 0 rgba(59,130,246,0.06); padding: 1.2rem 1rem 1rem 1rem; margin-bottom: 1.5rem; border: 1px solid #e2e8f0; transition: max-height 0.4s cubic-bezier(0.4,0,0.2,1); overflow: hidden; }
.sidebar-toggle { background: none; border: none; color: #3b82f6; font-size: 1.3rem; font-weight: 700; cursor: pointer; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem; }
.sidebar-icon { font-size: 1.2em; margin-right: 0.5em; }
/* Pastel backgrounds for sections */
.pastel-section { background: linear-gradient(90deg, #f0fdf4 0%, #f3f6fa 100%); border-radius: 1.2rem; padding: 1.5rem 1rem; margin-bottom: 2rem; }
"""
st.markdown(f"<style>{EXTRA_CSS}</style>", unsafe_allow_html=True)

def display_message_part(part):
    """
    Display a single part of a message in the Streamlit UI.
    Customize how you display system prompts, user prompts,
    tool calls, tool returns, etc.
    """
    # User messages
    if part.part_kind == 'user-prompt' and part.content:
        with st.chat_message("user"):
            st.markdown(part.content)
    # AI messages
    elif part.part_kind == 'text' and part.content:
        with st.chat_message("assistant"):
            st.markdown(part.content)             

async def run_agent_with_streaming(user_input):
    async with AsyncClient() as http_client:
        agent_deps = AgentDeps(
            http_client=http_client,
            brave_api_key=os.getenv("BRAVE_API_KEY", ""),
            searxng_base_url=os.getenv("SEARXNG_BASE_URL", "")
        )   

        async with agent.iter(user_input, deps=agent_deps, message_history=st.session_state.messages) as run:
            async for node in run:
                if Agent.is_model_request_node(node):
                    # A model request node => We can stream tokens from the model's request
                    async with node.stream(run.ctx) as request_stream:
                        async for event in request_stream:
                            if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                                    yield event.part.content
                            elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                                    delta = event.delta.content_delta
                                    yield delta         

    # Add the new messages to the chat history (including tool calls and responses)
    st.session_state.messages.extend(run.result.new_messages())       


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~ Main Function with UI Creation ~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

async def main():
    # Load company data from Excel
    company_data = load_company_data()

    # Update the main header for a more prominent look
    st.markdown(f'''
        <div class="header-gradient animated-header" style="box-shadow: 0 6px 24px 0 rgba(59,130,246,0.10);">
            <div class="header-title" style="font-size:2.8rem; letter-spacing:0.01em;">🚀 Croatian HGFs</div>
            <div class="header-subtitle" style="font-size:1.3rem;">Explore high-growth firms, regions, and company insights in Croatia</div>
        </div>
    ''', unsafe_allow_html=True)

    # Section divider
    def section_divider():
        st.markdown('<div style="height:2.5rem;"></div>', unsafe_allow_html=True)

    # --- Collapsible Sidebar with Icons ---
    with st.sidebar:
        st.markdown('<div class="sidebar-section sidebar-collapsible" style="background:linear-gradient(90deg,#f0fdf4 0%,#f3f6fa 100%);">', unsafe_allow_html=True)
        st.markdown('<button class="sidebar-toggle" onclick="var s=document.getElementById(\'sidebar-content\'); if(s.style.maxHeight){s.style.maxHeight=null;}else{s.style.maxHeight=s.scrollHeight+\'px\';}"><span class="sidebar-icon">☰</span>Navigation</button>', unsafe_allow_html=True)
        st.markdown('<div id="sidebar-content" style="max-height: 1000px; transition: max-height 0.4s cubic-bezier(0.4,0,0.2,1);">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title"><span class="sidebar-icon">🏢</span>Selected Company</div>', unsafe_allow_html=True)
        company_names = company_data['Company name Latin alphabet'].dropna().unique().tolist() if not company_data.empty else []
        selected_company = st.selectbox("Select Company", company_names)
        with st.expander("Company Details", expanded=True):
            if selected_company and not company_data.empty:
                company_row = company_data[company_data['Company name Latin alphabet'] == selected_company]
                if not company_row.empty:
                    st.markdown(f"**Company Name:** {selected_company}")
                    st.markdown("---")
                    st.markdown("**Description:**")
                    st.markdown(company_row['Company Description'].values[0])
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    section_divider()
    # --- High Growth Firms by Year Bar Chart ---
    st.markdown('<div class="data-table pastel-section chart-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='font-weight:700; font-size:1.35rem; margin-bottom:0.5rem;'>🚀 High Growth Firms by Year (2019–2023)</h3>", unsafe_allow_html=True)
    years = list(range(2019, 2024))
    hgf_counts = []
    for year in years:
        col = f"HighGrowthFirm {year}"
        if col in company_data.columns:
            count = pd.to_numeric(company_data[col].replace('n.a.', 0), errors='coerce').fillna(0).astype(int).eq(1).sum()
            hgf_counts.append(count)
        else:
            hgf_counts.append(0)
    fig_hgf = go.Figure(go.Bar(
        x=years,
        y=hgf_counts,
        marker=dict(color=COLORS['primary']),
    ))
    fig_hgf.update_layout(
        xaxis_title='Year',
        yaxis_title='Number of High Growth Firms',
        plot_bgcolor=COLORS['background'],
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', size=15),
        margin=dict(l=30, r=30, t=30, b=30),
        height=350,
        xaxis=dict(dtick=1),
        yaxis=dict(gridcolor=COLORS['border']),
        showlegend=False,
    )
    st.plotly_chart(fig_hgf, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    section_divider()
    # --- Top 10 Regions Horizontal Bar Chart ---
    st.markdown('<div class="data-table pastel-section chart-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='font-weight:700; font-size:1.35rem; margin-bottom:0.5rem;'>🏆 Top 10 Regions by Number of Companies</h3>", unsafe_allow_html=True)
    if 'Region in country clean' in company_data.columns:
        region_counts = company_data['Region in country clean'].value_counts().nlargest(10)
        fig_bar = go.Figure(go.Bar(
            x=region_counts.values[::-1],
            y=region_counts.index[::-1],
            orientation='h',
            marker=dict(color=COLORS['primary']),
        ))
        fig_bar.update_layout(
            xaxis_title='Number of Companies',
            yaxis_title='Region',
            plot_bgcolor=COLORS['background'],
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter, sans-serif', size=15),
            margin=dict(l=30, r=30, t=30, b=30),
            height=400,
            showlegend=False,
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("The column 'Region in country clean' was not found in your data.")
    st.markdown("</div>", unsafe_allow_html=True)

    section_divider()
    # --- Employee Count Line Chart Section ---
    st.markdown('<div class="data-table pastel-section chart-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='font-weight:700; font-size:1.35rem; margin-bottom:0.5rem;'>👥 Employee Count Over Time</h3>", unsafe_allow_html=True)
    chart_company = st.selectbox(
        "Select company for employee chart",
        company_data['Company name Latin alphabet'].dropna().unique().tolist(),
        key="employee_chart_company"
    )
    years = list(range(2016, 2025))
    np.random.seed(hash(chart_company) % 2**32)
    base = np.random.randint(10, 100)
    growth = np.random.uniform(0.95, 1.15, len(years))
    employees = [int(base * np.prod(growth[:i+1])) for i in range(len(years))]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=employees, mode='lines+markers', name='Employees',
                             line=dict(color=COLORS['primary'], width=3), marker=dict(size=8, color=COLORS['primary'])))
    fig.update_layout(
        xaxis_title='Year',
        yaxis_title='Number of Employees',
        plot_bgcolor=COLORS['background'],
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', size=15),
        margin=dict(l=30, r=30, t=30, b=30),
        height=350,
        xaxis=dict(dtick=1),
        yaxis=dict(gridcolor=COLORS['border']),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    section_divider()
    # --- Pastel Section: Company Table ---
    st.markdown('<div class="data-table pastel-section chart-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='font-weight:700; font-size:1.35rem; margin-bottom:0.5rem;'>📋 Company Database</h3>", unsafe_allow_html=True)
    search_query = st.text_input("🔍 Search companies by name or description", "")
    filtered_data = company_data
    if search_query:
        search_query_lower = search_query.lower()
        filtered_data = company_data[
            company_data['Company name Latin alphabet'].str.lower().str.contains(search_query_lower, na=False) |
            company_data['Company Description'].str.lower().str.contains(search_query_lower, na=False)
        ]
    st.dataframe(
        filtered_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Company name Latin alphabet": st.column_config.TextColumn(
                "Company Name",
                width="medium",
            ),
            "Company Description": st.column_config.TextColumn(
                "Company Description",
                width="large",
            ),
        }
    )
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    asyncio.run(main())
