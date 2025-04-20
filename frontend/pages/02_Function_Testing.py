import streamlit as st
import requests
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set page config
st.set_page_config(
    page_title="Function Testing - Serverless Platform",
    page_icon="🧪",
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
        .avg-container {
        display: flex;
        justify-content: space-around;
        margin-bottom: 20px;
    }
    .avg-box {
        padding: 15px;
        border-radius: 10px;
        width: 45%;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .gvisor-box {
        background-color: rgba(255, 0, 0, 0.1);
        border: 1px solid red;
    }
    .docker-box {
        background-color: rgba(0, 0, 255, 0.1);
        border: 1px solid blue;
    }
    .avg-title {
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 8px;
    }
    .avg-value {
        font-size: 22px;
        font-weight: bold;
    }
        }
    </style>
""", unsafe_allow_html=True)

# API URL - update this to match your backend URL
API_URL = "http://localhost:8000"

# Page title
st.markdown("""
    <div style='text-align: center; margin-bottom: 20px;'>
        <h1>🧪 Function Testing</h1>
        <p style='color: #6b7280; font-size: 1.1rem;'>Test your serverless functions with custom inputs</p>
    </div>
""", unsafe_allow_html=True)

# Main content
st.markdown("<div class='main'><h2>🛠️ Your Functions</h2><div class='card'>", unsafe_allow_html=True)

# Initialize session state for execution history
if 'execution_history' not in st.session_state:
    st.session_state.execution_history = []

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
                "Select a function to test",
                list(function_options.keys()),
                help="Choose a function to test with custom inputs"
            )
            
            if selected_function_name:
                selected_function_id = function_options[selected_function_name]
                
                # Fetch function details
                response = requests.get(f"{API_URL}/functions/{selected_function_id}")
                if response.status_code == 200:
                    function = response.json()
                    
                    # Display function details
                    st.markdown(f"<h3>Function: {function['name']}</h3>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([2, 3])
                    with col1:
                        st.markdown(f"""
                            <div class='card'>
                                <p><strong>Route:</strong> {function['route']}</p>
                                <p><strong>Language:</strong> {function['language']}</p>
                                <p><strong>Timeout:</strong> {function['timeout']} seconds</p>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # Show function code
                    with col2:
                        with st.expander("📜 Function Code", expanded=False):
                            st.code(function['code'], language=function['language'])
                    
                    # Input for function testing
                    st.markdown("<h3>🖱️ Test Input</h3>", unsafe_allow_html=True)
                    
                    # Default test inputs based on language
                    default_input = {}
                    if "hello" in function['code'].lower() or "world" in function['code'].lower():
                        default_input = {"name": "Test User"}
                    
                    # JSON input editor
                    st.markdown("<div class='tooltip'>", unsafe_allow_html=True)
                    input_method = st.radio(
                        "Input Method",
                        ["JSON Editor", "Form Editor"],
                        help="Choose how to provide input data"
                    )
                    st.markdown("<span class='tooltiptext'>Select input format</span></div>", unsafe_allow_html=True)
                    
                    if input_method == "JSON Editor":
                        json_input = st.text_area(
                            "JSON Input",
                            value=json.dumps(default_input, indent=2),
                            height=200,
                            help="Enter JSON input for the function"
                        )
                        
                        # Validate JSON
                        try:
                            input_data = json.loads(json_input)
                        except json.JSONDecodeError:
                            st.error("Invalid JSON format")
                            input_data = None
                    else:
                        # Simple form editor
                        st.write("Add key-value pairs:")
                        
                        # Initialize session state for form inputs if not exists
                        if 'form_inputs' not in st.session_state:
                            st.session_state.form_inputs = [{"key": "name", "value": "Test User"}]
                        
                        # Display existing inputs
                        input_data = {}
                        for i, inp in enumerate(st.session_state.form_inputs):
                            col1, col2, col3 = st.columns([3, 3, 1])
                            with col1:
                                st.session_state.form_inputs[i]["key"] = st.text_input(
                                    f"Key {i}",
                                    value=inp["key"],
                                    key=f"key_{i}",
                                    help="Input key"
                                )
                            with col2:
                                st.session_state.form_inputs[i]["value"] = st.text_input(
                                    f"Value {i}",
                                    value=inp["value"],
                                    key=f"value_{i}",
                                    help="Input value"
                                )
                            with col3:
                                if st.button("❌", key=f"remove_{i}", help="Remove this input"):
                                    st.session_state.form_inputs.pop(i)
                                    st.experimental_rerun()
                            
                            # Build input data dictionary
                            if inp["key"]:
                                input_data[inp["key"]] = inp["value"]
                        
                        # Add new input and clear buttons
                        col_add, col_clear = st.columns(2)
                        with col_add:
                            if st.button("➕ Add Input Field"):
                                st.session_state.form_inputs.append({"key": "", "value": ""})
                                st.experimental_rerun()
                        with col_clear:
                            if st.button("🧹 Clear Inputs"):
                                st.session_state.form_inputs = [{"key": "", "value": ""}]
                                st.experimental_rerun()
                    
                    # Execute button
                    if st.button("🚀 Execute Function"):
                        if input_data is not None:
                            with st.spinner("Executing function..."):
                                start_time = time.time()
                                try:
                                    # Execute the function
                                    response = requests.post(
                                        f"{API_URL}/functions/{selected_function_id}/execute",
                                        json=input_data
                                    )
                                    response1=requests.get(
                                        f"{API_URL}/functions/{selected_function_id}",
                                        json=input_data
                                    )
                                    function=response.json()
                                    function1=response1.json()
                                    virtualization = function1.get("virtualization")
                                    end_time = time.time()
                                    execution_time = (end_time - start_time) * 1000  # ms
                                    
                                    # Store execution in history
                                    st.session_state.execution_history.append({
                                        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                                        "execution_time_ms": execution_time,
                                        "status": "Success" if response.status_code == 200 else "Error",
                                        "virtualization": virtualization
                                    })
                                                                    
                                    # Display result
                                    st.markdown("<h3>📤 Result</h3>", unsafe_allow_html=True)
                                    
                                    if response.status_code == 200:
                                        st.success(f"Function executed successfully in {execution_time:.2f}ms!")
                                        
                                        # Try to parse as JSON and display
                                        try:
                                            result = response.json()
                                            st.json(result)
                                        except json.JSONDecodeError:
                                            st.code(response.text)
                                    else:
                                        st.error(f"Error executing function: {response.text}")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                                    st.session_state.execution_history.append({
                                        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                                        "execution_time_ms": execution_time,
                                        "status": "Error"
                                    })
                        else:
                            st.error("Please provide valid input data")
                    
                    # Execution history visualization
                    if st.session_state.execution_history:
                        st.markdown("<h3>📊 Execution History</h3>", unsafe_allow_html=True)
                        history_df = pd.DataFrame(st.session_state.execution_history)

                        error_df = history_df[history_df["execution_time_ms"] < 0]
                        gvisor_errors = error_df[error_df["virtualization"] == "gVisor"].shape[0]
                        docker_errors = error_df[error_df["virtualization"] == "docker"].shape[0]

                        
                        history_df = history_df[history_df["execution_time_ms"] >=0]

                        colors = ['red' if v == 'gVisor' else 'blue' for v in history_df["virtualization"]]

                        fig=go.Figure()
                        fig.add_trace(go.Bar(
                            x=history_df["time"].tolist(),
                            y=history_df["execution_time_ms"].tolist(),
                            text=history_df["virtualization"].tolist(),
                            marker_color=colors
                        ))
                        fig.update_layout(margin=dict(t=50, b=50, l=50, r=50), showlegend=True)
                        fig.add_trace(go.Bar(
                            x=[None], y=[None], name="gvisor", marker_color="red", showlegend=True
                        ))
                        fig.add_trace(go.Bar(
                            x=[None], y=[None], name="docker", marker_color="blue", showlegend=True
                        ))

                        gvisor_df = history_df[history_df["virtualization"] == "gVisor"]
                        docker_df = history_df[history_df["virtualization"] == "docker"]
                        
                        avg_gvisor = gvisor_df["execution_time_ms"].mean() if not gvisor_df.empty else 0
                        avg_docker = docker_df["execution_time_ms"].mean() if not docker_df.empty else 0

                        avg_html = f"""
                            <div style="display: flex; justify-content: space-around; margin-bottom: 20px; margin-top: 20px;">
                            <div style="padding: 15px; border-radius: 10px; width: 45%; text-align: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); background-color: rgba(255, 0, 0, 0.1); border: 2px solid #ff5252;">
                                <div style="font-weight: bold; font-size: 18px; margin-bottom: 8px; color: #d32f2f;">gVisor Stats</div>
                                <div style="font-size: 24px; font-weight: bold; color: #b71c1c;">{avg_gvisor:.2f} ms</div>
                                <div style="font-size: 16px; color: #d32f2f; margin-top: 8px;">Errors: <span style="font-weight: bold;">{gvisor_errors}</span></div>
                            </div>
                            <div style="padding: 15px; border-radius: 10px; width: 45%; text-align: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); background-color: rgba(0, 0, 255, 0.1); border: 2px solid #2979ff;">
                                <div style="font-weight: bold; font-size: 18px; margin-bottom: 8px; color: #1565c0;">Docker Stats</div>
                                <div style="font-size: 24px; font-weight: bold; color: #0d47a1;">{avg_docker:.2f} ms</div>
                                <div style="font-size: 16px; color: #1565c0; margin-top: 8px;">Errors: <span style="font-weight: bold;">{docker_errors}</span></div>
                            </div>
                        </div>
                        """
                        
                        st.markdown(avg_html, unsafe_allow_html=True)

                        with st.container():
                            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"Error fetching functions: {response.text}")
except Exception as e:
    st.error(f"Error connecting to API: {str(e)}")
    st.info(f"Make sure the API server is running at {API_URL}")

st.markdown("</div></div>", unsafe_allow_html=True)

# Footer
st.markdown("""
    <div style='text-align: center; margin-top: 20px;'>
        <p style='color: #6b7280; font-size: 0.9rem;'>Serverless Function Platform</p>
        <p style='color: #6b7280; font-size: 0.8rem;'>Built for the Serverless Function Execution Platform Project</p>
    </div>
""", unsafe_allow_html=True)