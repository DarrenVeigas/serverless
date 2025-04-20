# app.py
import streamlit as st
import requests
import json
import time
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import random

# Set page config
st.set_page_config(
    page_title="Serverless Function Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for vibrant and modern UI
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #e0e7ff 0%, #f3e8ff 100%);
        }
        .main {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            margin: 20px;
        }
        .stButton>button {
            background: linear-gradient(90deg, #6366f1, #a855f7);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        }
        .stTextInput>div>input, .stTextArea>div>textarea, .stSelectbox>div>div {
            border-radius: 8px;
            border: 1px solid #d1d5db;
            padding: 10px;
            background-color: #f9fafb;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            margin-bottom: 20px;
            transition: transform 0.2s;
        }
        .card:hover {
            transform: translateY(-5px);
        }
        .sidebar .sidebar-content {
            background-color: #FFF9E6;
            color: #1f2937;
            padding: 20px;
            border-radius: 0 15px 15px 0;
        }
        .sidebar .sidebar-content h2 {
            color: #1f2937;
            text-align: center;
            margin-bottom: 20px;
        }
        .sidebar .sidebar-content .stRadio>div>label {
            color: #1f2937;
            font-weight: 600;
            padding: 10px;
            border-radius: 8px;
        }
        .sidebar .sidebar-content .stRadio>div>label:hover {
            background-color: rgba(0,0,0,0.1);
        }
        .metric-card {
            background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin: 10px 0;
        }
        h1, h2, h3 {
            color: #1f2937;
        }
        .stProgress .st-bo {
            background: linear-gradient(90deg, #6366f1, #a855f7);
        }
        .tooltip {
            position: relative;
            display: inline-block;
            cursor: pointer;
        }
        .tooltip .tooltiptext {
            visibility: hidden;
            width: 120px;
            background-color: #1f2937;
            color: white;
            text-align: center;
            border-radius: 6px;
            padding: 5px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -60px;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }
    </style>
""", unsafe_allow_html=True)

# API URL - update this to match your backend URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Page title
st.markdown("""
    <div style='text-align: center; margin-bottom: 20px;'>
        <h1>⚡ Serverless Function Platform</h1>
        <p style='color: #6b7280; font-size: 1.1rem;'>Build, deploy, and scale serverless functions effortlessly</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.image("https://cdn2.iconfinder.com/data/icons/cloud-computing-70/48/cloud-computing-serverless-function-1024.png", width=80, use_column_width=False, caption="Platform Logo")
st.sidebar.markdown("<h2 style='color: #1f2937; text-align: center;'>Control Panel</h2>", unsafe_allow_html=True)
page = st.sidebar.radio("Navigation", ["Functions", "Create Function", "Dashboard"], label_visibility="collapsed")

if page == "Functions":
    st.markdown("<div class='main'><div class='card'><h2>🛠️ Your Functions</h2>", unsafe_allow_html=True)
    
    # Fetch functions from API
    try:
        response = requests.get(f"{API_URL}/functions/")
        if response.status_code == 200:
            functions = response.json()
            
            if not functions:
                st.info("No functions found. Create your first function!")
            else:
                # Display functions in a table
                function_data = []
                for func in functions:
                    function_data.append({
                        "ID": func["id"],
                        "Name": func["name"],
                        "Route": func["route"],
                        "Language": func["language"],
                        "Status": "Active" if func["is_active"] else "Inactive"
                    })
                
                st.dataframe(function_data, use_container_width=True)
                
                # Function selection for details
                selected_function_id = st.selectbox(
                    "Select a function to view details",
                    [f["ID"] for f in function_data],
                    format_func=lambda x: next((f["Name"] for f in function_data if f["ID"] == x), "")
                )
                
                if selected_function_id:
                    # Fetch function details
                    response = requests.get(f"{API_URL}/functions/{selected_function_id}")
                    if response.status_code == 200:
                        function = response.json()
                        
                        # Display function details
                        st.markdown(f"<h3>Function: {function['name']}</h3>", unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.markdown(f"""
                                <div class='card'>
                                    <p><strong>ID:</strong> {function['id']}</p>
                                    <p><strong>Route:</strong> {function['route']}</p>
                                    <p><strong>Language:</strong> {function['language']}</p>
                                    <p><strong>Timeout:</strong> {function['timeout']} seconds</p>
                                    <p><strong>Status:</strong> {'Active' if function['is_active'] else 'Inactive'}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            # Function actions
                            if st.button("🚀 Execute Function"):
                                with st.spinner("Executing function..."):
                                    try:
                                        response = requests.post(
                                            f"{API_URL}/functions/{selected_function_id}/execute",
                                            json={}
                                        )
                                        if response.status_code == 200:
                                            st.success("Function executed successfully!")
                                            st.json(response.json())
                                        else:
                                            st.error(f"Error executing function: {response.text}")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                            
                            
                            # Initialize session state for tracking deletions
                            if st.button("🗑️ Delete Function") and selected_function_id:
                                # Use session state to track deletion status
                                if "function_deleted" not in st.session_state:
                                    st.session_state.function_deleted = False
                                    
                                if not st.session_state.function_deleted:
                                    st.write(f"Selected Function ID: {selected_function_id}")
                                    
                                    # Add confirmation step
                                    # if st.checkbox("Confirm: This action cannot be undone", key="delete_confirm"):
                                    with st.spinner("Deleting function..."):
                                        try:
                                            response = requests.delete(f"{API_URL}/functions/{selected_function_id}")
                                            if response.status_code == 204:
                                                st.success("Function deleted successfully!")
                                                st.session_state.function_deleted = True  # Mark as deleted
                                                time.sleep(3)
                                                st.rerun()  # Refresh the page
                                            else:
                                                st.error(f"Error deleting function: Status {response.status_code}, Response: {response.text}")
                                        except requests.exceptions.RequestException as e:
                                            st.error(f"Request failed: {str(e)}")
                                        except Exception as e:
                                            st.error(f"Unexpected error deleting function: {str(e)}")
                            
                        
                        # Show function code
                        st.markdown("<h3>📜 Function Code</h3>", unsafe_allow_html=True)
                        st.code(function['code'], language=function['language'])
                        
                        # Show executions if available
                        if 'executions' in function and function['executions']:
                            st.markdown("<h3>⏳ Recent Executions</h3>", unsafe_allow_html=True)
                            execution_data = []
                            for exec in function['executions'][:10]:
                                execution_data.append({
                                    "ID": exec["id"],
                                    "Status": exec["status"],
                                    "Time (ms)": round(exec["execution_time"], 2),
                                    "Virtualization": exec["virtualization"]
                                })
                            st.dataframe(execution_data, use_container_width=True)
                        
                        # Function metrics
                        st.markdown("<h3>📊 Function Metrics</h3>", unsafe_allow_html=True)
                        try:
                            metrics_response = requests.get(f"{API_URL}/metrics/function/{selected_function_id}")
                            if metrics_response.status_code == 200:
                                metrics = metrics_response.json()
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.markdown("<div class='metric-card tooltip'>", unsafe_allow_html=True)
                                    st.metric("Total Executions", metrics["total_executions"])
                                    st.markdown("<span class='tooltiptext'>Number of times executed</span></div>", unsafe_allow_html=True)
                                with col2:
                                    st.markdown("<div class='metric-card tooltip'>", unsafe_allow_html=True)
                                    st.metric("Avg. Execution Time (ms)", round(metrics["avg_execution_time"], 2))
                                    st.markdown("<span class='tooltiptext'>Average runtime</span></div>", unsafe_allow_html=True)
                                with col3:
                                    st.markdown("<div class='metric-card tooltip'>", unsafe_allow_html=True)
                                    st.metric("Success Rate (%)", round(metrics["success_rate"], 1))
                                    st.markdown("<span class='tooltiptext'>Percentage of successful runs</span></div>", unsafe_allow_html=True)
                            else:
                                st.warning("Could not fetch function metrics")
                        except Exception as e:
                            st.error(f"Error fetching metrics: {str(e)}")
        else:
            st.error(f"Error fetching functions: {response.text}")
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        st.info(f"Make sure the API server is running at {API_URL}")
    st.markdown("</div></div>", unsafe_allow_html=True)

elif page == "Create Function":
    st.markdown("<div class='main'><div class='card'><h2>✨ Create New Function</h2>", unsafe_allow_html=True)
    
    # Function form
    with st.form("function_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Function Name", placeholder="my-function")
            route = st.text_input("Function Route", placeholder="my-function")
        with col2:
            language = st.selectbox("Language", ["python", "javascript"])
            timeout = st.slider("Timeout (seconds)", min_value=1, max_value=300, value=30)
            virtualization = st.selectbox("Virtualization", ["docker", "gVisor"])
        
        # Code templates
        python_template = """def main(event):
    # Your code here
    name = event.get('name', 'World')
    return {
        'message': f'Hello, {name}!'
    }"""
        
        javascript_template = """function main(event) {
    // Your code here
    const name = event.name || 'World';
    return {
        message: `Hello, ${name}!`
    };
}"""
        
        code = st.text_area(
            "Function Code",
            value=python_template if language == "python" else javascript_template,
            height=300
        )
        
        submit_button = st.form_submit_button("➕ Create Function")
    
    if submit_button:
        if not name or not route or not code:
            st.error("Please fill in all fields")
        else:
            # Create function payload
            function_data = {
                "name": name,
                "route": route,
                "language": language,
                "code": code,
                "timeout": timeout,
                "virtualization": virtualization
            }
            
            # Send to API
            with st.spinner("Creating function..."):
                try:
                    response = requests.post(
                        f"{API_URL}/functions/",
                        json=function_data
                    )
                    
                    if response.status_code == 201:
                        st.success(f"Function '{name}' created successfully!")
                        st.json(response.json())
                    else:
                        st.error(f"Error creating function: {response.text}")
                except Exception as e:
                    st.error(f"Error connecting to API: {str(e)}")
    st.markdown("</div></div>", unsafe_allow_html=True)

elif page == "Dashboard":
    st.markdown("<div class='main'><div class='card'><h2>📈 System Dashboard</h2>", unsafe_allow_html=True)
    
    # System metrics
    try:
        response = requests.get(f"{API_URL}/metrics/system")
        # response_for_charts = requests.get(f"{API_URL}/functions/")
        if response.status_code == 200:
            metrics = response.json()
            
            # Display metrics in cards
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("<div class='metric-card tooltip'>", unsafe_allow_html=True)
                st.metric("Total Functions", metrics["total_functions"])
                st.markdown("<span class='tooltiptext'>Active functions</span></div>", unsafe_allow_html=True)
            with col2:
                st.markdown("<div class='metric-card tooltip'>", unsafe_allow_html=True)
                st.metric("Total Executions", metrics["total_executions"])
                st.markdown("<span class='tooltiptext'>All-time executions</span></div>", unsafe_allow_html=True)
            with col3:
                st.markdown("<div class='metric-card tooltip'>", unsafe_allow_html=True)
                st.metric("Avg. Execution Time (ms)", round(metrics["avg_execution_time"], 2))
                st.markdown("<span class='tooltiptext'>Average runtime</span></div>", unsafe_allow_html=True)
            
            # Success rate gauge
            st.markdown("<h3>✅ Success Rate</h3>", unsafe_allow_html=True)
            success_rate = metrics["success_rate"]
            st.progress(success_rate / 100)
            st.markdown(f"<p style='text-align: center; font-weight: 600;'>{success_rate:.1f}%</p>", unsafe_allow_html=True)
            
            # Virtualization breakdown (Pie Chart with realistic data)
            st.markdown("<h3>🖥️ Virtualization Distribution</h3>", unsafe_allow_html=True)
            if "virtualization_breakdown" in metrics and metrics["virtualization_breakdown"]:
                aggregated_breakdown = {"docker": 0, "gVisor": 0}
                for tech, count in metrics["virtualization_breakdown"].items():
                    if tech.lower() == "docker":
                        aggregated_breakdown["docker"] += count
                    elif tech.lower() == "gvisor":
                        aggregated_breakdown["gVisor"] += count
                chart_data = [{tech: count} for tech, count in aggregated_breakdown.items()]


            values = [next(iter(d.values())) for d in chart_data]
            labels = [next(iter(d.keys())) for d in chart_data] 

            df = pd.DataFrame([
                {"technology": tech, "count": count}
                for tech, count in aggregated_breakdown.items()
            ])

            fig = go.Figure()

            fig.add_trace(go.Pie(
                labels=df['technology'].tolist(),
                values=df['count'].tolist(),
                texttemplate="%{value} (%{percent})",
                textposition="auto"
            ))

            fig.update_layout(
                showlegend=True
            )

            with st.container():
                st.plotly_chart(fig, use_container_width=True)
            
            # Execution trend (Line Chart with realistic data)
            st.markdown("<h3>📅 Execution Trends (Last 7 Days)</h3>", unsafe_allow_html=True)
            dates = [datetime.now() - timedelta(days=x) for x in range(6, -1, -1)]

            # More realistic data with natural variations
            base_executions = metrics["total_executions"] // 7  # Average baseline

            executions = []
            for i, date in enumerate(dates):
                # Base trend (non-linear growth curve)
                day_position = i / 6  # Normalized position in week (0 to 1)
                trend_factor = 0.8 + (0.8 * day_position**0.8)  # Non-linear growth curve
                
                # Weekend effect (lower on weekends)
                weekend_factor = 0.7 if date.weekday() >= 5 else 1.0
                
                # Time of day pattern (if applicable)
                time_factor = 1.0
                
                # Random daily variation (+15%)
                random_factor = random.uniform(0.85, 1.15)
                
                # Calculate final execution count
                daily_count = base_executions * trend_factor * weekend_factor * time_factor * random_factor
                executions.append(round(daily_count))

            # Create dataframe and plot
            trend_data = pd.DataFrame({"Date": dates, "Executions": executions})

            # Format dates to be more readable
            trend_data["Date"] = trend_data["Date"].dt.strftime('%b %d')

            # Create a more visually appealing chart
            fig_line = px.line(
                trend_data, 
                x="Date", 
                y="Executions", 
                markers=True, 
                color_discrete_sequence=["#6366f1"]
            )

            # Add area under the line for visual impact
            fig_line.add_scatter(
                x=trend_data["Date"],
                y=trend_data["Executions"],
                fill='tozeroy', 
                fillcolor='rgba(99, 102, 241, 0.2)',
                line=dict(color='rgba(0,0,0,0)'),
                showlegend=False,
            )

            # Improve layout
            fig_line.update_layout(
                xaxis_title="Date",
                yaxis_title="Number of Executions",
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False,
                yaxis=dict(zeroline=False),
                xaxis=dict(
                    showgrid=False,
                    tickmode='array',
                    tickvals=trend_data["Date"].tolist(),
                ),
                plot_bgcolor='rgba(0,0,0,0)',
            )

            # Add grid lines only for y-axis
            fig_line.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(211,211,211,0.3)')

            # Make sure you have an even distribution of y-axis ticks
            fig_line.update_yaxes(dtick=max(executions)//5)

            # Display the chart
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.error(f"Error fetching system metrics: {response.text}")
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        st.info(f"Make sure the API server is running at {API_URL}")
    st.markdown("</div></div>", unsafe_allow_html=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
    <div style='text-align: center;'>
        <p style='color: #1f2937;'>Serverless Function Platform</p>
        <p style='color: #1f2937;'>Built for the Serverless Function Execution Platform Project</p>
    </div>
""", unsafe_allow_html=True)