import streamlit as st
import requests
import json
import time

# Set page config
st.set_page_config(
    page_title="Function Testing - Serverless Platform",
    page_icon="🧪",
    layout="wide",
)

# API URL - update this to match your backend URL
API_URL = "http://localhost:8000"

# Page title
st.title("Function Testing")
st.write("Test your serverless functions with custom inputs")

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
                list(function_options.keys())
            )
            
            if selected_function_name:
                selected_function_id = function_options[selected_function_name]
                
                # Fetch function details
                response = requests.get(f"{API_URL}/functions/{selected_function_id}")
                if response.status_code == 200:
                    function = response.json()
                    
                    # Display function details
                    st.subheader(f"Function: {function['name']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Route:** {function['route']}")
                        st.write(f"**Language:** {function['language']}")
                        st.write(f"**Timeout:** {function['timeout']} seconds")
                    
                    # Show function code
                    with st.expander("Function Code", expanded=False):
                        st.code(function['code'], language=function['language'])
                    
                    # Input for function testing
                    st.subheader("Test Input")
                    
                    # Default test inputs based on language
                    default_input = {}
                    if "hello" in function['code'].lower() or "world" in function['code'].lower():
                        default_input = {"name": "Test User"}
                    
                    # JSON input editor
                    input_method = st.radio("Input Method", ["JSON Editor", "Form Editor"])
                    
                    if input_method == "JSON Editor":
                        json_input = st.text_area(
                            "JSON Input",
                            value=json.dumps(default_input, indent=2),
                            height=200
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
                                    key=f"key_{i}"
                                )
                            with col2:
                                st.session_state.form_inputs[i]["value"] = st.text_input(
                                    f"Value {i}", 
                                    value=inp["value"],
                                    key=f"value_{i}"
                                )
                            with col3:
                                if st.button("❌", key=f"remove_{i}"):
                                    st.session_state.form_inputs.pop(i)
                                    st.experimental_rerun()
                            
                            # Build input data dictionary
                            input_data[inp["key"]] = inp["value"]
                        
                        # Add new input button
                        if st.button("Add Input Field"):
                            st.session_state.form_inputs.append({"key": "", "value": ""})
                            st.experimental_rerun()
                    
                    # Execute button
                    if st.button("Execute Function"):
                        if input_data is not None:
                            with st.spinner("Executing function..."):
                                start_time = time.time()
                                try:
                                    # Execute the function
                                    response = requests.post(
                                        f"{API_URL}/functions/{selected_function_id}/execute",
                                        json=input_data
                                    )
                                    end_time = time.time()
                                    execution_time = (end_time - start_time) * 1000  # ms
                                    
                                    # Display result
                                    st.subheader("Result")
                                    
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
                        else:
                            st.error("Please provide valid input data")
    else:
        st.error(f"Error fetching functions: {response.text}")
except Exception as e:
    st.error(f"Error connecting to API: {str(e)}")
    st.info(f"Make sure the API server is running at {API_URL}")
