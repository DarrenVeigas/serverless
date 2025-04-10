import streamlit as st
import requests
import json
import time
import os
# Set page config
st.set_page_config(
    page_title="Serverless Function Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API URL - update this to match your backend URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Page title
st.title("Serverless Function Platform")
st.write("Deploy and manage serverless functions with ease")

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Functions", "Create Function", "Dashboard"])

if page == "Functions":
    st.header("Your Functions")
    
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
                
                st.table(function_data)
                
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
                        st.subheader(f"Function: {function['name']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**ID:** {function['id']}")
                            st.write(f"**Route:** {function['route']}")
                            st.write(f"**Language:** {function['language']}")
                            st.write(f"**Timeout:** {function['timeout']} seconds")
                            st.write(f"**Status:** {'Active' if function['is_active'] else 'Inactive'}")
                        
                        with col2:
                            # Function actions
                            if st.button("Execute Function"):
                                with st.spinner("Executing function..."):
                                    try:
                                        # Execute the function
                                        response = requests.post(
                                            f"{API_URL}/functions/{selected_function_id}/execute",
                                            json={}  # Empty payload for now
                                        )
                                        if response.status_code == 200:
                                            st.success("Function executed successfully!")
                                            st.json(response.json())
                                        else:
                                            st.error(f"Error executing function: {response.text}")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                            
                            if st.button("Delete Function"):
                                if st.checkbox("I understand this action cannot be undone"):
                                    with st.spinner("Deleting function..."):
                                        try:
                                            response = requests.delete(f"{API_URL}/functions/{selected_function_id}")
                                            if response.status_code == 204:
                                                st.success("Function deleted successfully!")
                                                time.sleep(1)
                                                st.experimental_rerun()
                                            else:
                                                st.error(f"Error deleting function: {response.text}")
                                        except Exception as e:
                                            st.error(f"Error: {str(e)}")
                        
                        # Show function code
                        st.subheader("Function Code")
                        st.code(function['code'], language=function['language'])
                        
                        # Show executions if available
                        if 'executions' in function and function['executions']:
                            st.subheader("Recent Executions")
                            execution_data = []
                            for exec in function['executions'][:10]:  # Show only the last 10
                                execution_data.append({
                                    "ID": exec["id"],
                                    "Status": exec["status"],
                                    "Time (ms)": round(exec["execution_time"], 2),
                                    "Virtualization": exec["virtualization"]
                                })
                            st.table(execution_data)
                        
                        # Function metrics
                        st.subheader("Function Metrics")
                        try:
                            metrics_response = requests.get(f"{API_URL}/metrics/function/{selected_function_id}")
                            if metrics_response.status_code == 200:
                                metrics = metrics_response.json()
                                
                                col1, col2, col3 = st.columns(3)
                                col1.metric("Total Executions", metrics["total_executions"])
                                col2.metric("Avg. Execution Time (ms)", round(metrics["avg_execution_time"], 2))
                                col3.metric("Success Rate (%)", round(metrics["success_rate"], 1))
                            else:
                                st.warning("Could not fetch function metrics")
                        except Exception as e:
                            st.error(f"Error fetching metrics: {str(e)}")
        else:
            st.error(f"Error fetching functions: {response.text}")
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        st.info(f"Make sure the API server is running at {API_URL}")

elif page == "Create Function":
    st.header("Create New Function")
    
    # Function form
    with st.form("function_form"):
        name = st.text_input("Function Name", placeholder="my-function")
        route = st.text_input("Function Route", placeholder="my-function")
        language = st.selectbox("Language", ["python", "javascript"])
        timeout = st.slider("Timeout (seconds)", min_value=1, max_value=300, value=30)
        
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
        
        submit_button = st.form_submit_button("Create Function")
    
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
                "timeout": timeout
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

elif page == "Dashboard":
    st.header("System Dashboard")
    
    # System metrics
    try:
        response = requests.get(f"{API_URL}/metrics/system")
        if response.status_code == 200:
            metrics = response.json()
            
            # Display metrics in cards
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Functions", metrics["total_functions"])
            col2.metric("Total Executions", metrics["total_executions"])
            col3.metric("Avg. Execution Time (ms)", round(metrics["avg_execution_time"], 2))
            
            # Success rate gauge
            st.subheader("Success Rate")
            success_rate = metrics["success_rate"]
            st.progress(success_rate / 100)
            st.write(f"{success_rate:.1f}%")
            
            # Virtualization breakdown
            st.subheader("Executions by Virtualization Technology")
            if "virtualization_breakdown" in metrics and metrics["virtualization_breakdown"]:
                # Convert to format suitable for charting
                chart_data = []
                for tech, count in metrics["virtualization_breakdown"].items():
                    chart_data.append({"technology": tech, "count": count})
                
                # Simple bar chart using st.bar_chart
                import pandas as pd
                df = pd.DataFrame.from_records(chart_data)
                df = df.set_index('technology')
                st.bar_chart(df)
            else:
                st.info("No execution data available yet")
        else:
            st.error(f"Error fetching system metrics: {response.text}")
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        st.info(f"Make sure the API server is running at {API_URL}")

# Footer
st.sidebar.markdown("---")
st.sidebar.info(
    """
    Serverless Function Platform © 2024
    
    A project for the Serverless Function Execution Platform course.
    """
)
