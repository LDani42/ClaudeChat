# Scratchpad section in right column
if st.session_state.scratchpad_visible and scratchpad_col is not None:
    with scratchpad_col:
        st.header("Scratchpad")
        
        # Add new item manually
        with st.expander("Add New Item", expanded=False):
            item_name = st.text_input("Item Name", key="new_item_name")
            item_type = st.selectbox("Content Type", ["text", "code", "table", "chart"])
            
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
            elif item_type == "chart":
                st.info("To create charts, use the visualization tools in the sidebar.")
            else:
                text = st.text_area("Text Content", height=150)
                if st.button("Save Text"):
                    if item_name:
                        add_to_scratchpad(item_name, "text", text)
                        st.success(f"Saved '{item_name}' to scratchpad")
        
        # Upload CSV for visualization
        with st.expander("Import Data for Visualization", expanded=False):
            uploaded_csv = st.file_uploader("Upload CSV file", type=["csv"], key="data_csv")
            if uploaded_csv:
                try:
                    import pandas as pd
                    data = pd.read_csv(uploaded_csv)
                    st.session_state.chart_data = data
                    st.success(f"Successfully imported {uploaded_csv.name} with {len(data)} rows and {len(data.columns)} columns.")
                    
                    if st.button("Preview Data"):
                        st.dataframe(data.head())
                        
                    chart_type = st.selectbox(
                        "Chart Type", 
                        ["Line Chart", "Bar Chart", "Scatter Plot", "Pie Chart", "Heatmap"],
                        key="chart_type_selector"
                    )
                    
                    if st.button("Create Visualization"):
                        create_chart(data, chart_type)
                except Exception as e:
                    st.error(f"Error loading CSV: {str(e)}")
        
        # Display scratchpad items
        if not st.session_state.scratchpad:
            st.info("Your scratchpad is empty. Chat with Claude to automatically collect useful information here.")
        else:
            # Group scratchpad items by type
            code_items = {k: v for k, v in st.session_state.scratchpad.items() if v["type"] == "code"}
            table_items = {k: v for k, v in st.session_state.scratchpad.items() if v["type"] == "table"}
            chart_items = {k: v for k, v in st.session_state.scratchpad.items() if v["type"] == "chart"}
            text_items = {k: v for k, v in st.session_state.scratchpad.items() if v["type"] not in ["code", "table", "chart"]}
            
            # Display charts first
            if chart_items:
                st.subheader("Charts & Visualizations")
                for name, item in chart_items.items():
                    with st.expander(f"{name}"):
                        # Display the chart image
                        import base64
                        from PIL import Image
                        import io
                        
                        try:
                            image_data = base64.b64decode(item["content"]["image_data"])
                            image = Image.open(io.BytesIO(image_data))
                            st.image(image, caption=item["content"]["description"])
                        except Exception as e:
                            st.error(f"Error displaying chart: {str(e)}")
                        
                        col1, col2 = st.columns([1, 1])
                        with col2:
                            if st.button(f"Delete", key=f"delete_chart_{name}"):
                                del st.session_state.scratchpad[name]
                                st.success(f"Deleted '{name}'")
                                st.rerun()
            
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
import seaborn as sns

# Set page configuration
st.set_page_config(
    page_title="Custom Claude UI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Determine if dark mode is enabled
is_dark_mode = st.experimental_get_query_params().get("theme", ["light"])[0] == "dark"

# Styles - updated for fixed chat input and scrollable message pane
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        max-width: 100%;
    }
    .stTextArea textarea {min-height: 100px;}
    
    /* Fixed layout for chat */
    .chat-outer-container {
        display: flex;
        flex-direction: column;
        height: 85vh;
        margin-bottom: 1rem;
        border-radius: 8px;
        background-color: rgba(40, 40, 40, 0.2);
        overflow: hidden;
    }
    
    .messages-scroll-container {
        flex-grow: 1;
        overflow-y: auto;
        padding: 1rem;
        scroll-behavior: smooth;
    }
    
    .chat-input-fixed-container {
        position: sticky;
        bottom: 0;
        background-color: rgba(30, 30, 30, 0.7);
        backdrop-filter: blur(10px);
        padding: 1rem;
        border-top: 1px solid rgba(100, 100, 100, 0.2);
        z-index: 100;
    }
    
    /* Message styling */
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.75rem;
        max-width: 90%;
        word-wrap: break-word;
    }
    
    /* Dark mode friendly colors */
    .user-message {
        background-color: #2a4b8d;
        margin-left: auto;
        color: #ffffff !important;
    }
    
    .assistant-message {
        background-color: #2d3748;
        margin-right: auto;
        color: #ffffff !important;
    }
    
    /* File upload styling */
    .file-upload {
        border: 2px dashed #ccc;
        border-radius: 5px;
        padding: 10px;
        text-align: center;
    }
    
    .file-attachment-icon {
        position: absolute;
        left: 10px;
        bottom: 10px;
        font-size: 20px;
        cursor: pointer;
        color: rgba(180, 180, 180, 0.8);
        z-index: 100;
    }
    
    /* File chips styling */
    .file-chip {
        display: inline-block;
        background-color: rgba(100, 100, 100, 0.3);
        border-radius: 16px;
        padding: 4px 12px;
        margin: 4px;
        font-size: 12px;
    }
    
    /* Split screen layout */
    .chat-panel {
        flex: 7;
        padding-right: 1rem;
    }
    
    .scratchpad-panel {
        flex: 3;
        background-color: rgba(40, 40, 40, 0.2);
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
    
    /* Chart container */
    .chart-container {
        background-color: rgba(40, 40, 40, 0.2);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Other styling */
    h1, h2, h3 {margin-top: 0;}
    
    /* Streamlit component overrides */
    .stChatInputContainer {
        padding-bottom: 20px;
        padding-top: 10px;
    }
    
    /* Auto-scrolling support */
    #auto-scroll-anchor {
        float: left;
        clear: both;
        height: 0;
    }
</style>

<script>
    // Auto-scroll function to keep messages at the bottom
    function scrollToBottom() {
        const messagesContainer = document.querySelector('.messages-scroll-container');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }
    
    // Call on load and add mutation observer to scroll when new messages are added
    document.addEventListener('DOMContentLoaded', function() {
        scrollToBottom();
        
        // Observe for changes to scroll when new content is added
        const targetNode = document.querySelector('.messages-scroll-container');
        if (targetNode) {
            const observer = new MutationObserver(scrollToBottom);
            observer.observe(targetNode, { childList: true, subtree: true });
        }
    });
</script>
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
if 'chart_data' not in st.session_state:
    st.session_state.chart_data = None

# Function to create and save charts based on data
def create_chart(data, chart_type):
    try:
        plt.figure(figsize=(10, 6))
        
        if chart_type == "Line Chart":
            plt.figure(figsize=(10, 6))
            for column in data.select_dtypes(include=['int64', 'float64']).columns:
                if column != 'date':
                    plt.plot(data['date'] if 'date' in data.columns else range(len(data)), 
                             data[column], label=column)
            plt.legend()
            plt.title("Line Chart")
            plt.xlabel("Date" if 'date' in data.columns else "Index")
            plt.ylabel("Value")
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            
        elif chart_type == "Bar Chart":
            # Use the first categorical column for grouping if available
            categorical_cols = data.select_dtypes(include=['object']).columns
            if len(categorical_cols) > 0:
                category_col = categorical_cols[0]
                numeric_cols = data.select_dtypes(include=['int64', 'float64']).columns
                if len(numeric_cols) > 0:
                    value_col = numeric_cols[0]
                    grouped_data = data.groupby(category_col)[value_col].mean().reset_index()
                    plt.bar(grouped_data[category_col], grouped_data[value_col])
                    plt.title(f"Average {value_col} by {category_col}")
                    plt.xlabel(category_col)
                    plt.ylabel(f"Average {value_col}")
            else:
                # If no categorical column, use the first numeric column
                numeric_cols = data.select_dtypes(include=['int64', 'float64']).columns
                if len(numeric_cols) > 0:
                    plt.bar(range(len(data)), data[numeric_cols[0]])
                    plt.title(f"Bar Chart of {numeric_cols[0]}")
                    plt.xlabel("Index")
                    plt.ylabel(numeric_cols[0])
            
        elif chart_type == "Scatter Plot":
            numeric_cols = data.select_dtypes(include=['int64', 'float64']).columns
            if len(numeric_cols) >= 2:
                x_col, y_col = numeric_cols[0], numeric_cols[1]
                categorical_cols = data.select_dtypes(include=['object']).columns
                
                if len(categorical_cols) > 0:
                    # Color by category if available
                    category_col = categorical_cols[0]
                    categories = data[category_col].unique()
                    for category in categories:
                        subset = data[data[category_col] == category]
                        plt.scatter(subset[x_col], subset[y_col], label=category, alpha=0.7)
                    plt.legend()
                else:
                    plt.scatter(data[x_col], data[y_col], alpha=0.7)
                
                plt.title(f"Scatter Plot: {y_col} vs {x_col}")
                plt.xlabel(x_col)
                plt.ylabel(y_col)
                plt.grid(True, linestyle='--', alpha=0.3)
            
        elif chart_type == "Pie Chart":
            categorical_cols = data.select_dtypes(include=['object']).columns
            if len(categorical_cols) > 0:
                category_col = categorical_cols[0]
                count_data = data[category_col].value_counts()
                plt.pie(count_data, labels=count_data.index, autopct='%1.1f%%', 
                        shadow=True, startangle=90)
                plt.axis('equal')
                plt.title(f"Distribution of {category_col}")
            
        elif chart_type == "Heatmap":
            numeric_data = data.select_dtypes(include=['int64', 'float64'])
            if not numeric_data.empty:
                corr = numeric_data.corr()
                sns.heatmap(corr, annot=True, cmap='coolwarm', linewidths=0.5)
                plt.title("Correlation Heatmap")
                plt.tight_layout()
        
        # Save the figure to a BytesIO object
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        
        # Add to scratchpad
        chart_name = f"chart_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Convert to base64 for storage
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        add_to_scratchpad(chart_name, "chart", {
            "type": chart_type,
            "image_data": img_str,
            "description": f"{chart_type} created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        })
        
        st.success(f"Chart '{chart_name}' added to scratchpad")
        return True
        
    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")
        return False

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
    # Improved regex pattern to better match code blocks
    code_pattern = r'```([\w\+\#\-\.]*)\s*\n(.*?)```'
    matches = re.findall(code_pattern, text, re.DOTALL)
    
    code_blocks = []
    for lang, code in matches:
        # Default to text if language is empty, otherwise clean up language name
        language = lang.strip().lower() if lang.strip() else "text"
        # Map common language aliases
        if language in ["py", "python3"]:
            language = "python"
        elif language in ["js", "jsx"]:
            language = "javascript"
        elif language in ["ts", "typescript"]:
            language = "typescript"
        
        code_blocks.append({
            "language": language,
            "code": code.strip()
        })
    
    return code_blocks

# Function to extract tables from responses
def extract_tables(text):
    # Improved markdown table pattern with better matching
    table_pattern = r'(\|.*\|.*\n\|[-:| ]+\|\n(?:\|.*\|.*\n)+)'
    matches = re.findall(table_pattern, text, re.DOTALL)
    
    tables = []
    for table_text in matches:
        tables.append(table_text.strip())
    
    return tables

# Add new item to scratchpad
def add_to_scratchpad(name, content_type, content):
    if not content:
        return None  # Don't add empty content
        
    # Clean the name to avoid special characters issues
    clean_name = re.sub(r'[^\w\s-]', '', name).strip()
    if not clean_name:
        clean_name = f"{content_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    if clean_name in st.session_state.scratchpad:
        # Increment name if it already exists
        count = 1
        new_name = f"{clean_name}_{count}"
        while new_name in st.session_state.scratchpad:
            count += 1
            new_name = f"{clean_name}_{count}"
        clean_name = new_name
    
    # Add the item to the scratchpad
    st.session_state.scratchpad[clean_name] = {
        "type": content_type,
        "content": content,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Log to console for debugging
    print(f"Added to scratchpad: {clean_name} ({content_type})")
    
    return clean_name

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

    # Reset chat button (keeps scratchpad)
    st.subheader("Chat Controls")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Reset Chat", help="Clear chat messages but keep scratchpad"):
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        if st.button("Clear All", help="Clear both chat and scratchpad"):
            st.session_state.messages = []
            st.session_state.scratchpad = {}
            st.rerun()
            
    # Visualization controls
    st.subheader("Visualization")
    
    # Create a chart with sample data
    if st.button("Create Sample Chart", help="Create a sample chart to test visualization"):
        # Generate sample data
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        data = {
            'date': dates,
            'value1': np.random.randint(10, 100, size=30),
            'value2': np.random.randint(20, 80, size=30),
            'category': np.random.choice(['A', 'B', 'C'], size=30)
        }
        
        st.session_state.chart_data = pd.DataFrame(data)
        st.success("Sample data created! Use 'Visualize Data' to create charts.")
    
    # Chart type selector (only show if data exists)
    if st.session_state.chart_data is not None:
        chart_type = st.selectbox(
            "Chart Type", 
            ["Line Chart", "Bar Chart", "Scatter Plot", "Pie Chart", "Heatmap"],
            index=0
        )
        
        if st.button("Visualize Data"):
            create_chart(st.session_state.chart_data, chart_type)

# Main layout with two columns
if st.session_state.scratchpad_visible:
    chat_col, scratchpad_col = st.columns([7, 3])
else:
    chat_col = st.container()
    scratchpad_col = None

# Chat interface
with chat_col:
    st.subheader("Chat with Claude")
    
    # Create a fixed layout for chat with message history in a scrollable container
    st.markdown('<div class="chat-outer-container">', unsafe_allow_html=True)
    
    # Scrollable messages container
    st.markdown('<div class="messages-scroll-container">', unsafe_allow_html=True)
    
    # Display messages
    for msg in st.session_state.messages:
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
    
    # Add an empty div at the bottom to allow auto-scrolling
    st.markdown('<div id="auto-scroll-anchor"></div>', unsafe_allow_html=True)
    
    # Close the messages container
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Fixed input container at the bottom
    st.markdown('<div class="chat-input-fixed-container">', unsafe_allow_html=True)
    
    # Toggle button for scratchpad
    if st.button("Toggle Scratchpad" + (" ▶" if st.session_state.scratchpad_visible else " ◀")):
        toggle_scratchpad()
    
    # File uploader with drag & drop support
    st.markdown('<div style="position: relative;">', unsafe_allow_html=True)
    st.markdown('<div class="file-attachment-icon">📎</div>', unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader("", 
                                      accept_multiple_files=True, 
                                      type=["png", "jpg", "jpeg", "pdf", "txt", "csv", "json", "xlsx"],
                                      label_visibility="collapsed")
    
    # Process uploaded files
    active_file_ids = []
    if uploaded_files:
        file_display = st.empty()
        with file_display.container():
            # Display uploaded files as chips
            file_chips_html = '<div style="margin-bottom: 10px;">'
            
            for uploaded_file in uploaded_files:
                file_id = handle_uploaded_file(uploaded_file)
                if file_id:
                    active_file_ids.append(file_id)
                    file_data = st.session_state.file_buffer[file_id]
                    file_chips_html += f'<span class="file-chip">{file_data["name"]}</span>'
            
            file_chips_html += '</div>'
            st.markdown(file_chips_html, unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input("Message Claude...")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
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
                st.info(f"Added code snippet to scratchpad: {name}")
            
            # Extract tables and add to scratchpad
            tables = extract_tables(assistant_message)
            for i, table in enumerate(tables):
                name = f"table_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
                add_to_scratchpad(name, "table", table)
                st.info(f"Added table to scratchpad: {name}")
                
            # Also add the entire response as a note
            if len(assistant_message) > 0:
                note_name = f"note_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                add_to_scratchpad(note_name, "text", assistant_message)
                st.info(f"Added assistant response to scratchpad: {note_name}")
            
        # Rerun to update the UI
        st.rerun()
