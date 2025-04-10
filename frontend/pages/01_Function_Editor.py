import streamlit as st
import requests
import json

# Set page config
st.set_page_config(
    page_title="Function Editor - Serverless Platform",
    page_icon="📝",
    layout="wide",
)

# API URL - update this to match your backend URL
API_URL = "http://localhost:8000"

# Page title
st.title("Function Editor")
st.write("Edit your serverless functions")

# Fetch functions from API
try:
    response = requests.get(f"{API_URL}/functions/")
    if response.status_code == 200:
        functions = response.json()
        
        if not functions:
            st.info("No functions found. Create your first function!")
        else:
            # Create a selectbox with function names
            function_options = {f["name"]: f["id"] for f in functions}
            selected_function_name = st.selectbox(
                "Select a function to edit",
                list(function_options.keys())
            )
            
            if selected_function_name:
                selected_function_id = function_options[selected_function_name]
                
                # Fetch function details
                response = requests.get(f"{API_URL}/functions/{selected_function_id}")
                if response.status_code == 200:
                    function = response.json()
                    
                    # Function edit form
                    with st.form("edit_function_form"):
                        name = st.text_input("Function Name", value=function["name"])
                        route = st.text_input("Function Route", value=function["route"])
                        language = st.selectbox("Language", ["python", "javascript"], index=0 if function["language"] == "python" else 1)
                        timeout = st.slider("Timeout (seconds)", min_value=1, max_value=300, value=function["timeout"])
                        code = st.text_area("Function Code", value=function["code"], height=400)
                        
                        submit_button = st.form_submit_button("Update Function")
                    
                    if submit_button:
                        if not name or not route or not code:
                            st.error("Please fill in all fields")
                        else:
                            # Update function payload
                            function_data = {
                                "name": name,
                                "route": route,
                                "language": language,
                                "code": code,
                                "timeout": timeout
                            }
                            
                            # Send to API
                            with st.spinner("Updating function..."):
                                try:
                                    response = requests.put(
                                        f"{API_URL}/functions/{selected_function_id}",
                                        json=function_data
                                    )
                                    
                                    if response.status_code == 200:
                                        st.success(f"Function '{name}' updated successfully!")
                                        st.json(response.json())
                                    else:
                                        st.error(f"Error updating function: {response.text}")
                                except Exception as e:
                                    st.error(f"Error connecting to API: {str(e)}")
    else:
        st.error(f"Error fetching functions: {response.text}")
except Exception as e:
    st.error(f"Error connecting to API: {str(e)}")
    st.info(f"Make sure the API server is running at {API_URL}")
