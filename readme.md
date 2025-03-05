# Custom Claude UI with Scratchpad

A multimodal chatbot interface for Claude AI with a built-in scratchpad for storing notes, code, and tables.

## Features

- 🤖 Connect to any Claude model through the Anthropic API
- 📸 Upload and send images, documents, and text files to Claude
- 🔄 Switch between different Claude models
- 📝 Automatic scratchpad that stores:
  - Code snippets from Claude's responses
  - Tables and structured data
  - Notes and other text content
- ✏️ Edit specific segments of the scratchpad
- 💻 Written in Python using Streamlit for easy deployment

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/claude-custom-ui.git
   cd claude-custom-ui
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   streamlit run app.py
   ```

## Usage

1. Enter your Anthropic API key in the sidebar
2. Select your preferred Claude model
3. Customize the system prompt (optional)
4. Adjust temperature and token settings as needed
5. Upload files to include in your conversation
6. Chat with Claude!

## Scratchpad Features

The scratchpad automatically captures:
- Code snippets from Claude's responses (with syntax highlighting)
- Tables in markdown format
- You can manually add, edit, or delete scratchpad items

## Deployment

You can deploy this application to Streamlit sharing or other platforms:

1. Push to GitHub:
   ```
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. Deploy on Streamlit Cloud:
   - Visit [Streamlit Sharing](https://streamlit.io/sharing)
   - Connect your GitHub repository
   - Deploy with a few clicks

## Security Note

Your Anthropic API key is stored in the session state and is not persisted between sessions. For additional security when deploying, consider using environment variables or a secure secrets management system.

## License

MIT License