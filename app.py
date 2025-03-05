import streamlit as st
import anthropic
import os
import json
import base64
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from PIL import Image
import io
import re
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Custom Claude UI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Determine if dark mode is enabled
is_dark_mode = st.experimental_get_query_params().get("theme", ["light"])[0] == "dark"

# Styles - updated for dark mode compatibility
st.markdown("""
<style>
    .main .block-container {padding-top: 1rem;}
    .stTextArea textarea {min-height: 100px;}
    .scratchpad {
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.75rem;
        max-width: 90%;
    }
    .user-message {
        background-color: #e6f7ff;
        margin-left: auto;
        color: #333333 !important; /* Force dark text for user messages */
    }
    .assistant-message {
        background-color: #f0f2f6;
        margin-right: auto;
        color: #333333 !important; /* Force dark text for assistant messages */
    }
    h1, h2, h3 {margin-top: 0;}
    .file-upload {
        border: 2px dashed #ccc;
        border-radius: 5px;
        padding: 10px;
        text-align: center;
    }
    /* Split screen layout */
    .chat-container {
        display: flex;
        flex-direction: row;
        width: 100%;
    }
    .chat-panel {
        flex: 7;
        padding-right: 1rem;
    }
    .scratchpad-panel {
        flex: 3;
        background-color: rgba(240, 242, 246, 0.1);
        border-radius: 0.5rem;
        padding: 1rem;
        height: calc(100vh - 80px);
        overflow-y: auto;
        position: sticky;
        top: 0;
    }
    .collapse-button {
        position: absolute;
        top: 10px;
        right: 10px;
        z-index: 1000;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'scratchpad' not in st.session_state:
    st.session_state.scratchpad = {}
if 'current_scratchpad_item' not in st.session_state:
    st.session_state.current_scratchpad_item = None
if 'file_buffer' not in st.session_state:
    st.session_state.file_buffer = {}
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'scratchpad_visible' not in st.session_state:
    st.session_state.scratchpad_visible = True

# Sidebar settings
with st.sidebar:
    st.title("Custom Claude UI")
    
    # API Key input
    api_key = st.text_input("Anthropic API Key", type="password", help="Enter your Anthropic API Key")
    if api_key:
        st.session_state.api_key = api_key
    
    # Model selection
    model_options = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229", 
        "claude-3-haiku-20240307",
        "claude-3-5-sonnet-20240620",
        "claude-3-7-sonnet-20250219",  # Future model release (placeholder)
    ]
    selected_model = st.selectbox("Select Claude Model", model_options, index=1)
    
    # System prompt
    system_prompt = st.text_area(
        "System Prompt", 
        value="You are Claude, an AI assistant created by Anthropic. You're helpful, harmless, and honest.",
        help="Custom instructions for the assistant"
    )
    
    # Temperature setting
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    
    # Max token settings
    max_tokens = st.slider("Max Tokens", min_value=100, max_value=200000, value=4000, step=100)

    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Function to handle file uploads and encode them
def handle_uploaded_file(uploaded_file):
    if uploaded_file is None:
        return None
    
    # Save file to session state buffer
    file_id = f"{uploaded_file.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Read the file
    file_bytes = uploaded_file.getvalue()
    
    # Handle different file types
    file_type = uploaded_file.type
    file_data = {
        "name": uploaded_file.name,
        "type": file_type,
        "size": len(file_bytes),
        "data": base64.b64encode(file_bytes).decode('utf-8'),
        "display_data": None
    }
    
    # For images, create display data
    if file_type.startswith('image/'):
        file_data["display_data"] = file_bytes
    
    # For text files, decode the content
    if file_type == 'text/plain' or file_type == 'text/csv' or 'json' in file_type:
        try:
            file_data["text_content"] = file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            file_data["text_content"] = None
    
    # Store in session state
    st.session_state.file_buffer[file_id] = file_data
    return file_id

# Function to create Claude message with file attachments
def create_claude_message(message_text, file_ids=None):
    if not file_ids:
        return {"role": "user", "content": message_text}
    
    message_content = [{"type": "text", "text": message_text}]
    
    for file_id in file_ids:
        if file_id in st.session_state.file_buffer:
            file_data = st.session_state.file_buffer[file_id]
            
            # For images, add as image type
            if file_data['type'].startswith('image/'):
                message_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": file_data['type'],
                        "data": file_data['data']
                    }
                })
            # For text files, include content as text
            elif 'text_content' in file_data and file_data['text_content']:
                message_content.append({
                    "type": "text",
                    "text": f"Content of file {file_data['name']}:\n\n{file_data['text_content']}"
                })
    
    return {"role": "user", "content": message_content}

# Function to parse and extract code from Claude's responses
def extract_code_blocks(text):
    code_pattern = r'```(\w*)\n(.*?)```'
    matches = re.findall(code_pattern, text, re.DOTALL)
    
    code_blocks = []
    for lang, code in matches:
        code_blocks.append({
            "language": lang.strip() if lang.strip() else "text",
            "code": code.strip()
        })
    
    return code_blocks

# Function to extract tables from responses
def extract_tables(text):
    # Simple markdown table pattern
    table_pattern = r'\|.*\|.*\n\|[-:| ]+\|\n(\|.*\|.*\n)+'
    matches = re.findall(table_pattern, text, re.DOTALL)
    
    tables = []
    for table_text in matches:
        tables.append(table_text.strip())
    
    return tables

# Function to add content to scratchpad
def add_to_scratchpad(name, content_type, content):
    if name in st.session_state.scratchpad:
        # Increment name if it already exists
        count = 1
        new_name = f"{name}_{count}"
        while new_name in st.session_state.scratchpad:
            count += 1
            new_name = f"{name}_{count}"
        name = new_name
    
    st.session_state.scratchpad[name] = {
        "type": content_type,
        "content": content,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return name

# Function to call Claude API
def query_claude(messages, model, system_prompt, temperature, max_tokens):
    if not st.session_state.api_key:
        st.error("Please enter your Anthropic API Key in the sidebar")
        return None
    
    try:
        # Initialize Anthropic client with only the API key
        client = anthropic.Anthropic(api_key=st.session_state.api_key)
        
        # Call the messages API
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=messages
        )
        
        return response
    except Exception as e:
        st.error(f"Error calling Claude API: {str(e)}")
        return None

# Toggle scratchpad visibility
def toggle_scratchpad():
    st.session_state.scratchpad_visible = not st.session_state.scratchpad_visible
    st.rerun()

# Main layout with two columns
if st.session_state.scratchpad_visible:
    chat_col, scratchpad_col = st.columns([7, 3])
else:
    chat_col = st.container()
    scratchpad_col = None

# Chat interface
with chat_col:
    st.subheader("Chat with Claude")

    # File uploader
    uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True, type=["png", "jpg", "jpeg", "pdf", "txt", "csv", "json", "xlsx"])
    active_file_ids = []

    # Display uploaded files as chips
    if uploaded_files:
        file_cols = st.columns(4)
        for i, uploaded_file in enumerate(uploaded_files):
            file_id = handle_uploaded_file(uploaded_file)
            if file_id:
                active_file_ids.append(file_id)
                with file_cols[i % 4]:
                    # Display thumbnails for images
                    file_data = st.session_state.file_buffer[file_id]
                    if file_data['type'].startswith('image/') and file_data['display_data']:
                        st.image(file_data['display_data'], caption=file_data['name'], width=100)
                    else:
                        st.code(f"📄 {file_data['name']}", language=None)

    # Chat input
    user_input = st.chat_input("Message Claude...")

    # Process user input
    if user_input:
        # Create message for UI display
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Create message for Claude API with file attachments
        claude_message = create_claude_message(user_input, active_file_ids)
        
        # Prepare messages for API
        api_messages = [m for m in st.session_state.messages if m["role"] != "system"]
        # Replace the last user message with the one that includes files
        if api_messages and api_messages[-1]["role"] == "user":
            api_messages[-1] = claude_message
        
        # Call Claude API
        with st.status("Claude is thinking..."):
            response = query_claude(
                api_messages,
                selected_model,
                system_prompt,
                temperature,
                max_tokens
            )
        
        if response:
            assistant_message = response.content[0].text
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})
            
            # Extract code blocks and add to scratchpad
            code_blocks = extract_code_blocks(assistant_message)
            for i, block in enumerate(code_blocks):
                name = f"code_snippet_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
                add_to_scratchpad(name, "code", block)
            
            # Extract tables and add to scratchpad
            tables = extract_tables(assistant_message)
            for i, table in enumerate(tables):
                name = f"table_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
                add_to_scratchpad(name, "table", table)

    # Display chat messages
    for msg in st.session_state.messages:
        message_container = st.container()
        
        with message_container:
            if msg["role"] == "user":
                st.markdown(f"""
                    <div class="chat-message user-message">
                        <p><strong>You:</strong></p>
                        <p>{msg["content"]}</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <p><strong>Claude:</strong></p>
                    </div>
                """, unsafe_allow_html=True)
                st.write(msg["content"])

    # Toggle button for scratchpad
    if st.button("Toggle Scratchpad" + (" ▶" if st.session_state.scratchpad_visible else " ◀")):
        toggle_scratchpad()

# Scratchpad section in right column
if st.session_state.scratchpad_visible and scratchpad_col is not None:
    with scratchpad_col:
        st.header("Scratchpad")
        
        # Add new item manually
        with st.expander("Add New Item", expanded=False):
            item_name = st.text_input("Item Name", key="new_item_name")
            item_type = st.selectbox("Content Type", ["text", "code", "table"])
            
            if item_type == "code":
                language = st.selectbox("Language", ["python", "javascript", "html", "css", "sql", "bash", "text"])
                code = st.text_area("Code Content", height=150)
                if st.button("Save Code"):
                    if item_name:
                        add_to_scratchpad(item_name, "code", {"language": language, "code": code})
                        st.success(f"Saved '{item_name}' to scratchpad")
            elif item_type == "table":
                table_markdown = st.text_area("Table (Markdown Format)", value="| Column 1 | Column 2 |\n| --- | --- |\n| Data 1 | Data 2 |", height=150)
                if st.button("Save Table"):
                    if item_name:
                        add_to_scratchpad(item_name, "table", table_markdown)
                        st.success(f"Saved '{item_name}' to scratchpad")
            else:
                text = st.text_area("Text Content", height=150)
                if st.button("Save Text"):
                    if item_name:
                        add_to_scratchpad(item_name, "text", text)
                        st.success(f"Saved '{item_name}' to scratchpad")
        
        # Display scratchpad items
        if not st.session_state.scratchpad:
            st.info("Your scratchpad is empty. Chat with Claude to automatically collect useful information here.")
        else:
            # Group scratchpad items by type
            code_items = {k: v for k, v in st.session_state.scratchpad.items() if v["type"] == "code"}
            table_items = {k: v for k, v in st.session_state.scratchpad.items() if v["type"] == "table"}
            text_items = {k: v for k, v in st.session_state.scratchpad.items() if v["type"] not in ["code", "table"]}
            
            # Display code snippets
            if code_items:
                st.subheader("Code Snippets")
                for name, item in code_items.items():
                    with st.expander(f"{name}"):
                        st.code(item["content"]["code"], language=item["content"]["language"])
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            # Edit button opens edit form
                            if st.button(f"Edit", key=f"edit_{name}"):
                                st.session_state.current_scratchpad_item = name
                                st.session_state["edit_mode"] = True
                                st.rerun()
                        with col2:
                            # Delete button
                            if st.button(f"Delete", key=f"delete_{name}"):
                                del st.session_state.scratchpad[name]
                                st.success(f"Deleted '{name}'")
                                st.rerun()
            
            # Display tables
            if table_items:
                st.subheader("Tables")
                for name, item in table_items.items():
                    with st.expander(f"{name}"):
                        st.markdown(item["content"])
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button(f"Edit", key=f"edit_table_{name}"):
                                st.session_state.current_scratchpad_item = name
                                st.session_state["edit_mode"] = True
                                st.rerun()
                        with col2:
                            if st.button(f"Delete", key=f"delete_table_{name}"):
                                del st.session_state.scratchpad[name]
                                st.success(f"Deleted '{name}'")
                                st.rerun()
            
            # Display other text content
            if text_items:
                st.subheader("Notes")
                for name, item in text_items.items():
                    with st.expander(f"{name}"):
                        st.write(item["content"])
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button(f"Edit", key=f"edit_text_{name}"):
                                st.session_state.current_scratchpad_item = name
                                st.session_state["edit_mode"] = True
                                st.rerun()
                        with col2:
                            if st.button(f"Delete", key=f"delete_text_{name}"):
                                del st.session_state.scratchpad[name]
                                st.success(f"Deleted '{name}'")
                                st.rerun()
        
        # Edit mode for selected scratchpad item
        if "edit_mode" in st.session_state and st.session_state["edit_mode"] and st.session_state.current_scratchpad_item:
            st.subheader(f"Edit: {st.session_state.current_scratchpad_item}")
            item = st.session_state.scratchpad[st.session_state.current_scratchpad_item]
            
            if item["type"] == "code":
                language = st.selectbox("Language", ["python", "javascript", "html", "css", "sql", "bash", "text"], 
                                        index=["python", "javascript", "html", "css", "sql", "bash", "text"].index(item["content"]["language"]))
                code = st.text_area("Code", value=item["content"]["code"], height=300)
                if st.button("Update Code"):
                    st.session_state.scratchpad[st.session_state.current_scratchpad_item]["content"] = {"language": language, "code": code}
                    st.success("Updated successfully")
                    st.session_state["edit_mode"] = False
                    st.rerun()
            elif item["type"] == "table":
                table_markdown = st.text_area("Table (Markdown)", value=item["content"], height=300)
                if st.button("Update Table"):
                    st.session_state.scratchpad[st.session_state.current_scratchpad_item]["content"] = table_markdown
                    st.success("Updated successfully")
                    st.session_state["edit_mode"] = False
                    st.rerun()
            else:
                text = st.text_area("Text", value=item["content"], height=300)
                if st.button("Update Text"):
                    st.session_state.scratchpad[st.session_state.current_scratchpad_item]["content"] = text
                    st.success("Updated successfully")
                    st.session_state["edit_mode"] = False
                    st.rerun()
            
            if st.button("Cancel"):
                st.session_state["edit_mode"] = False
                st.session_state.current_scratchpad_item = None
                st.rerun()

# Footer
st.divider()
st.caption("Custom Claude UI - Built with Streamlit")
