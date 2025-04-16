import streamlit as st
import requests
import json

# Set page config
st.set_page_config(
    page_title="Function Editor - Serverless Platform",
    page_icon="📝",
    layout="wide",
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
            background: linear-gradient(180deg, #4f46e5, #7c3aed);
            color: white;
            padding: 20px;
            border-radius: 0 15px 15px 0;
        }
        h1, h2, h3 {
            color: #1f2937;
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
API_URL = "http://localhost:8000"

# Page title
st.markdown("""
    <div style='text-align: center; margin-bottom: 20px;'>
        <h1>📝 Function Editor</h1>
        <p style='color: #6b7280; font-size: 1.1rem;'>Edit and fine-tune your serverless functions</p>
    </div>
""", unsafe_allow_html=True)

# Main content
st.markdown("<div class='main'><h2>🛠️ Your Functions</h2><div class='card'>", unsafe_allow_html=True)

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
                list(function_options.keys()),
                help="Choose a function to modify its details and code"
            )
            
            if selected_function_name:
                selected_function_id = function_options[selected_function_name]
                
                # Fetch function details
                response = requests.get(f"{API_URL}/functions/{selected_function_id}")
                if response.status_code == 200:
                    function = response.json()
                    
                    # Split layout into two columns: form and code preview
                    col1, col2 = st.columns([3, 2])
                    
                    with col1:
                        # Function edit form
                        with st.form("edit_function_form"):
                            st.markdown("<h3>Edit Function</h3>", unsafe_allow_html=True)
                            col_name, col_route = st.columns(2)
                            with col_name:
                                name = st.text_input("Function Name", value=function["name"], help="Unique name for your function")
                            with col_route:
                                route = st.text_input("Function Route", value=function["route"], help="API route for function execution")
                            language = st.selectbox("Language", ["python", "javascript"], index=0 if function["language"] == "python" else 1, help="Programming language of the function")
                            st.markdown("<div class='tooltip'>", unsafe_allow_html=True)
                            timeout = st.slider("Timeout (seconds)", min_value=1, max_value=300, value=function["timeout"], help="Maximum execution time")
                            st.markdown("<span class='tooltiptext'>Max execution time</span></div>", unsafe_allow_html=True)
                            code = st.text_area("Function Code", value=function["code"], height=400, help="Write your function code here")
                            
                            submit_button = st.form_submit_button("✨ Update Function")
                    
                    with col2:
                        # Code preview
                        st.markdown("<h3>Code Preview</h3>", unsafe_allow_html=True)
                        st.code(function['code'], language=function['language'])
                    
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

st.markdown("</div></div>", unsafe_allow_html=True)

# Footer
st.markdown("""
    <div style='text-align: center; margin-top: 20px;'>
        <p style='color: #6b7280; font-size: 0.9rem;'>Serverless Function Platform © 2024</p>
        <p style='color: #6b7280; font-size: 0.8rem;'>Built for the Serverless Function Execution Platform course</p>
    </div>
""", unsafe_allow_html=True)