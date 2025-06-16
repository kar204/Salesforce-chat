# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import json
# from datetime import datetime

# from config import (
#     client_id,
#     client_secret,
#     username,
#     password,
#     login_url,
#     watsonx_url,
#     watsonx_project_id,
#     watsonx_model_id
# )
# from watsonx_utils import (
#     validate_watsonx_config,
#     create_data_context,
#     query_watsonx_ai,
#     parse_intent_fallback,
#     get_watsonx_token
# )
# from salesforce_utils import load_salesforce_data
# from analysis_engine import execute_analysis, display_analysis_result
# from ai import summarize_analysis_result_with_ai  # AI summarizer with chunking


# # Predefined project and subproject lists
# WAVE_CITY_SUBPROJECTS = [
#     "ARANYAM VALLEY", "ARMONIA VILLA", "DREAM BAZAAR", "DREAM HOMES", "EDEN", "ELIGO", "EWS", "EWS_001_(410)",
#     "EXECUTIVE FLOORS", "FSI", "Generic", "Golf Range", "INSTITUTIONAL", "LIG", "LIG_001_(310)", "Mayfair Park",
#     "NEW PLOTS", "OLD PLOTS", "PRIME FLOORS", "SCO.", "SWAMANORATH", "VERIDIA", "VERIDIA-3", "VERIDIA-4",
#     "VERIDIA-5", "VERIDIA-6", "VERIDIA-7", "VILLAS", "WAVE FLOOR", "WAVE GALLERIA"
# ]

# WAVE_ESTATE_SUBPROJECTS = [
#     "COMM BOOTH", "HARMONY GREENS", "INSTITUTIONAL_WE", "PLOT-RES-IF", "PLOTS-COMM", "PLOTS-RES", "SCO",
#     "WAVE FLOOR 85", "WAVE FLOOR 99", "WAVE GARDEN", "WAVE GARDEN GH2-Ph-2"
# ]

# WMCC_SUBPROJECTS = [
#     "AMORE", "HSSC", "LIVORK", "TRUCIA"
# ]

# PROJECT_OPTIONS = ["WAVE CITY", "WAVE ESTATE", "WMCC", "SELECT ALL"]

# # Page config and styling
# st.set_page_config(page_title="LeadBot Analytics", layout="wide", initial_sidebar_state="expanded")
# st.markdown("""
# <style>
#     .user-msg {
#         padding: 10px;
#         margin: 5px 0;
#         background-color: #d1ecf1;
#         border-radius: 10px;
#         color: black;
#     }
#     .bot-msg {
#         padding: 10px;
#         margin: 5px 0;
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         color: black !important;
#         border-radius: 10px;
#     }
# </style>
# """, unsafe_allow_html=True)

# st.title("🤖 Wave Group (CRM-BOT)")
# st.markdown("*Welcome To Wave, How May I help you?*")

# # Add Clear Chat button
# if st.button("🧹 Clear Chat"):
#     st.session_state.conversation = []
#     st.session_state.show_details = False
#     st.session_state.show_graph = False
#     st.session_state.last_query_idx = -1
#     st.experimental_rerun()

# st.markdown("---")

# # Load Salesforce data with caching
# @st.cache_data(show_spinner=True)
# def load_data():
#     return load_salesforce_data()

# leads_df, users_df, cases_df, events_df, opportunities_df, task_df, load_error = load_data()

# if load_error:
#     st.error(f"❌ Error loading Salesforce data: {load_error}")
#     st.stop()

# data_context = create_data_context(leads_df, users_df, cases_df, events_df, opportunities_df, task_df)

# # Initialize session state variables if not present
# if 'conversation' not in st.session_state:
#     st.session_state.conversation = []
# if 'show_details' not in st.session_state:
#     st.session_state.show_details = False
# if 'show_graph' not in st.session_state:
#     st.session_state.show_graph = False
# if 'last_query_idx' not in st.session_state:
#     st.session_state.last_query_idx = -1

# def reset_flags():
#     st.session_state.show_details = False
#     st.session_state.show_graph = False

# def plot_graph(graph_data):
#     if not graph_data:
#         st.info("No graphical data available for this query.")
#         return
#     for field, counts in graph_data.items():
#         df = pd.DataFrame(list(counts.items()), columns=[field, 'Count'])
#         if df.empty:
#             st.info(f"No data to plot for {field}.")
#             continue
#         fig = px.bar(df, x=field, y='Count', title=f"Distribution of {field}")
#         st.plotly_chart(fig, use_container_width=True)

# def get_financial_year_dates(selection, custom_year=None):
#     try:
#         if selection == "Current FY":
#             return pd.Timestamp("2024-04-01", tz="UTC"), pd.Timestamp("2025-03-31 23:59:59", tz="UTC")
#         elif selection == "Last FY":
#             return pd.Timestamp("2023-04-01", tz="UTC"), pd.Timestamp("2024-03-31 23:59:59", tz="UTC")
#         elif selection == "Custom" and custom_year:
#             year_int = int(custom_year)
#             return pd.Timestamp(f"{year_int}-04-01", tz="UTC"), pd.Timestamp(f"{year_int+1}-03-31 23:59:59", tz="UTC")
#     except Exception:
#         return None, None

# def process_query(user_question):
#     reset_flags()

#     product_project_keywords = ["product", "project", "sale", "lead", "conversion", "funnel", "source", "geography"]
#     is_special_query = any(k in user_question.lower() for k in product_project_keywords)

#     filters = {}

#     if is_special_query:
#         st.markdown("### Step 1: Select Financial Year")
#         financial_year = st.selectbox("Financial Year:", ["Current FY", "Last FY", "Custom"])
#         custom_year = None
#         if financial_year == "Custom":
#             custom_year = st.text_input("Enter starting year (e.g., 2024)")
#         financial_year_start, financial_year_end = get_financial_year_dates(financial_year, custom_year)

#         st.markdown("### Step 2: Select Project")
#         selected_project = st.selectbox("Project:", PROJECT_OPTIONS, index=3)  # Default to SELECT ALL

#         if selected_project == "WAVE CITY":
#             subprojects = WAVE_CITY_SUBPROJECTS
#         elif selected_project == "WAVE ESTATE":
#             subprojects = WAVE_ESTATE_SUBPROJECTS
#         elif selected_project == "WMCC":
#             subprojects = WMCC_SUBPROJECTS
#         elif selected_project == "SELECT ALL":
#             subprojects = WAVE_CITY_SUBPROJECTS + WAVE_ESTATE_SUBPROJECTS + WMCC_SUBPROJECTS
#         else:
#             subprojects = []

#         st.markdown("### Step 3: Select Sub-project(s) / Product(s)")
#         selected_subprojects = st.multiselect(
#             "Sub-project(s):",
#             options=["Select All"] + subprojects,
#             default=["Select All"]
#         )

#         if selected_subprojects and "Select All" in selected_subprojects:
#             selected_subprojects = subprojects

#         if financial_year_start and financial_year_end and 'CreatedDate' in leads_df.columns:
#             filters["CreatedDate"] = {"$gte": financial_year_start.isoformat(), "$lte": financial_year_end.isoformat()}

#         if selected_project != "SELECT ALL":
#             filters["Project__c"] = selected_project

#         if selected_subprojects and len(selected_subprojects) > 0:
#             filters["Project_Category__c"] = selected_subprojects

#     try:
#         analysis_plan = query_watsonx_ai(user_question, data_context, leads_df, cases_df, events_df, users_df, opportunities_df, task_df)
#     except Exception as e:
#         st.error(f"Error querying WatsonX AI: {e}")
#         analysis_plan = {"analysis_type": "error", "explanation": "AI query failed."}

#     if "filters" not in analysis_plan or not isinstance(analysis_plan["filters"], dict):
#         analysis_plan["filters"] = {}

#     for key, val in filters.items():
#         analysis_plan["filters"][key] = val

#     if analysis_plan.get("analysis_type") == "error":
#         fallback_plan = parse_intent_fallback(user_question, "")
#         backend_result = execute_analysis(fallback_plan, leads_df, users_df, cases_df, events_df, opportunities_df, task_df, user_question)
#         ai_summary = f"AI processing error: {analysis_plan.get('explanation', '')}\nShowing fallback analysis results."
#         follow_ups = []
#     else:
#         backend_result = execute_analysis(analysis_plan, leads_df, users_df, cases_df, events_df, opportunities_df, task_df, user_question)

#         ai_summary = summarize_analysis_result_with_ai(
#             backend_result,
#             user_question,
#             watsonx_url,
#             watsonx_project_id,
#             watsonx_model_id,
#             get_watsonx_token
#         )
#         follow_ups = []

#     st.session_state.conversation.append({"role": "user", "content": user_question})
#     st.session_state.conversation.append({"role": "assistant", "content": ai_summary})

#     st.markdown(f"**AI Summary:** {ai_summary}")

#     if st.button("Show Graph"):
#         st.session_state.show_graph = True

#     if st.button("Show Details"):
#         st.session_state.show_details = True

#     if st.session_state.show_graph:
#         plot_graph(backend_result.get("graph_data", {}))

#     if st.session_state.show_details:
#         graph_data = backend_result.get("graph_data", {})
#         if not graph_data:
#             st.info("No detailed data available for this query.")
#         else:
#             for field, counts in graph_data.items():
#                 df = pd.DataFrame(list(counts.items()), columns=[field, 'Count'])
#                 st.markdown(f"### Details for {field}")
#                 st.dataframe(df)

#     st.session_state.last_query_idx += 1

# user_question = st.text_input("Enter your query:", key="user_input")

# if user_question:
#     process_query(user_question)
























































































import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime

from config import (
    client_id,
    client_secret,
    username,
    password,
    login_url,
    watsonx_url,
    watsonx_project_id,
    watsonx_model_id
)
from watsonx_utils import (
    validate_watsonx_config,
    create_data_context,
    query_watsonx_ai,
    parse_intent_fallback,
    get_watsonx_token
)
from salesforce_utils import load_salesforce_data
from analysis_engine import execute_analysis, display_analysis_result
from ai import summarize_analysis_result_with_ai  # AI summarizer with chunking


# Predefined project and subproject lists
WAVE_CITY_SUBPROJECTS = [
    "ARANYAM VALLEY", "ARMONIA VILLA", "DREAM BAZAAR", "DREAM HOMES", "EDEN", "ELIGO", "EWS", "EWS_001_(410)",
    "EXECUTIVE FLOORS", "FSI", "Generic", "Golf Range", "INSTITUTIONAL", "LIG", "LIG_001_(310)", "Mayfair Park",
    "NEW PLOTS", "OLD PLOTS", "PRIME FLOORS", "SCO.", "SWAMANORATH", "VERIDIA", "VERIDIA-3", "VERIDIA-4",
    "VERIDIA-5", "VERIDIA-6", "VERIDIA-7", "VILLAS", "WAVE FLOOR", "WAVE GALLERIA"
]

WAVE_ESTATE_SUBPROJECTS = [
    "COMM BOOTH", "HARMONY GREENS", "INSTITUTIONAL_WE", "PLOT-RES-IF", "PLOTS-COMM", "PLOTS-RES", "SCO",
    "WAVE FLOOR 85", "WAVE FLOOR 99", "WAVE GARDEN", "WAVE GARDEN GH2-Ph-2"
]

WMCC_SUBPROJECTS = [
    "AMORE", "HSSC", "LIVORK", "TRUCIA"
]

PROJECT_OPTIONS = ["WAVE CITY", "WAVE ESTATE", "WMCC", "SELECT ALL"]

# Page config and styling
st.set_page_config(page_title="LeadBot Analytics", layout="wide", initial_sidebar_state="expanded")

# Title and subtitle
st.title("🤖 Wave Group (CRM-BOT)")
st.markdown("*Welcome To Wave, How May I help you?*")

# Clear chat button
if st.button("🧹 Clear Chat"):
    st.session_state.conversation = []
    st.session_state.show_details = False
    st.session_state.show_graph = False
    st.session_state.last_query_idx = -1
    st.experimental_rerun()

st.markdown("---")

# Load Salesforce data with caching
@st.cache_data(show_spinner=True)
def load_data():
    return load_salesforce_data()

leads_df, users_df, cases_df, events_df, opportunities_df, task_df, load_error = load_data()

if load_error:
    st.error(f"❌ Error loading Salesforce data: {load_error}")
    st.stop()

data_context = create_data_context(leads_df, users_df, cases_df, events_df, opportunities_df, task_df)

# Initialize session state variables if not present
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'show_details' not in st.session_state:
    st.session_state.show_details = False
if 'show_graph' not in st.session_state:
    st.session_state.show_graph = False
if 'last_query_idx' not in st.session_state:
    st.session_state.last_query_idx = -1

def reset_flags():
    st.session_state.show_details = False
    st.session_state.show_graph = False

def plot_graph(graph_data):
    if not graph_data:
        st.info("No graphical data available for this query.")
        return
    for field, counts in graph_data.items():
        df = pd.DataFrame(list(counts.items()), columns=[field, 'Count'])
        if df.empty:
            st.info(f"No data to plot for {field}.")
            continue
        fig = px.bar(df, x=field, y='Count', title=f"Distribution of {field}")
        st.plotly_chart(fig, use_container_width=True)

def get_financial_year_dates(selection, custom_year=None):
    try:
        if selection == "Current FY":
            return pd.Timestamp("2024-04-01", tz="UTC"), pd.Timestamp("2025-03-31 23:59:59", tz="UTC")
        elif selection == "Last FY":
            return pd.Timestamp("2023-04-01", tz="UTC"), pd.Timestamp("2024-03-31 23:59:59", tz="UTC")
        elif selection == "Custom" and custom_year:
            year_int = int(custom_year)
            return pd.Timestamp(f"{year_int}-04-01", tz="UTC"), pd.Timestamp(f"{year_int+1}-03-31 23:59:59", tz="UTC")
    except Exception:
        return None, None

def process_query(user_question):
    reset_flags()

    product_project_keywords = ["product", "project", "sale", "lead", "conversion", "funnel", "source", "geography"]
    is_special_query = any(k in user_question.lower() for k in product_project_keywords)

    filters = {}

    if is_special_query:
        st.markdown("### Filters")
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            financial_year = st.selectbox("Financial Year", ["Current FY", "Last FY", "Custom"], key="financial_year")
            custom_year = None
            if financial_year == "Custom":
                custom_year = st.text_input("Enter starting year (e.g., 2024)", key="custom_year")

        with col2:
            selected_project = st.selectbox("Select Project(s)", PROJECT_OPTIONS, index=3, key="selected_project")

        with col3:
            # Determine subprojects based on selected_project
            if selected_project == "WAVE CITY":
                subprojects = WAVE_CITY_SUBPROJECTS
            elif selected_project == "WAVE ESTATE":
                subprojects = WAVE_ESTATE_SUBPROJECTS
            elif selected_project == "WMCC":
                subprojects = WMCC_SUBPROJECTS
            elif selected_project == "SELECT ALL":
                subprojects = WAVE_CITY_SUBPROJECTS + WAVE_ESTATE_SUBPROJECTS + WMCC_SUBPROJECTS
            else:
                subprojects = []

            selected_subprojects = st.multiselect(
                "Select Product(s)",
                options=["Select All"] + subprojects,
                default=["Select All"],
                key="selected_subprojects"
            )

        if selected_subprojects and "Select All" in selected_subprojects:
            selected_subprojects = subprojects

        financial_year_start, financial_year_end = get_financial_year_dates(financial_year, custom_year)

        if financial_year_start and financial_year_end and 'CreatedDate' in leads_df.columns:
            filters["CreatedDate"] = {"$gte": financial_year_start.isoformat(), "$lte": financial_year_end.isoformat()}

        if selected_project != "SELECT ALL":
            filters["Project__c"] = selected_project

        if selected_subprojects and len(selected_subprojects) > 0:
            filters["Project_Category__c"] = selected_subprojects

    try:
        analysis_plan = query_watsonx_ai(user_question, data_context, leads_df, cases_df, events_df, users_df, opportunities_df, task_df)
    except Exception as e:
        st.error(f"Error querying WatsonX AI: {e}")
        analysis_plan = {"analysis_type": "error", "explanation": "AI query failed."}

    if "filters" not in analysis_plan or not isinstance(analysis_plan["filters"], dict):
        analysis_plan["filters"] = {}

    for key, val in filters.items():
        analysis_plan["filters"][key] = val

    if analysis_plan.get("analysis_type") == "error":
        fallback_plan = parse_intent_fallback(user_question, "")
        backend_result = execute_analysis(fallback_plan, leads_df, users_df, cases_df, events_df, opportunities_df, task_df, user_question)
        ai_summary = f"AI processing error: {analysis_plan.get('explanation', '')}\nShowing fallback analysis results."
        follow_ups = []
    else:
        backend_result = execute_analysis(analysis_plan, leads_df, users_df, cases_df, events_df, opportunities_df, task_df, user_question)

        ai_summary = summarize_analysis_result_with_ai(
            backend_result,
            user_question,
            watsonx_url,
            watsonx_project_id,
            watsonx_model_id,
            get_watsonx_token
        )
        follow_ups = []

    st.session_state.conversation.append({"role": "user", "content": user_question})
    st.session_state.conversation.append({"role": "assistant", "content": ai_summary})

    st.markdown(f"""<p style="margin-top:20px;"><b>AI Summary:</b> {ai_summary}</p>""", unsafe_allow_html=True)

    if st.button("Show Graph"):
        st.session_state.show_graph = True

    if st.button("Show Details"):
        st.session_state.show_details = True

    if st.session_state.show_graph:
        plot_graph(backend_result.get("graph_data", {}))

    if st.session_state.show_details:
        graph_data = backend_result.get("graph_data", {})
        if not graph_data:
            st.info("No detailed data available for this query.")
        else:
            for field, counts in graph_data.items():
                df = pd.DataFrame(list(counts.items()), columns=[field, 'Count'])
                st.markdown(f"### Details for {field}")
                st.dataframe(df)

    st.session_state.last_query_idx += 1

user_question = st.text_input("Enter your query:", key="user_input")

if user_question:
    process_query(user_question)
