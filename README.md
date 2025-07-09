# 🪨 Geode - Obsidian + AI ⚠️ **In Development** 

**Geode** is a desktop application that serves as an intelligent bridge between your local [Obsidian](https://obsidian.md/) vault and advanced AI models, primarily Google's [Gemini AI](https://gemini.google.com/). Transform your knowledge base into a dynamic, interactive platform for insight, organization, and creation.

**🎯 Simple Setup:** Choose your preferred AI provider from 8 options - just pick one, enter its API key, and you're ready! Switch providers anytime through the settings UI without losing your work.

Built with a modular Python backend and a PyQt6 GUI, Geode provides deep, stateful AI integration directly within your personal knowledge management workflow. This project was largely developed through AI-assisted coding and iterative prompting.

---

## ✨ Core Features

### 🧠 **Intelligent Conversation System**
- **8 AI Providers:** Gemini (primary), Claude, OpenAI, Cohere, Mistral, Ollama (local), Perplexity, Together AI
- **Stateful, Persistent Conversations:** Engage in complex, multi-step tasks with context-aware AI
- **Session Management:** All conversations automatically saved with resumable chat history
- **Advanced Tool Integration:** AI can directly interact with your vault through built-in tools

### 📁 **Vault Integration**
- **Live File System Access:** Read, write, create, and organize files within your Obsidian vault
- **Intelligent File Discovery:** Recursive vault scanning with smart autocomplete
- **Path-Aware Operations:** Context-sensitive file operations with safety checks
- **Real-time Sync:** Changes reflect immediately in both Geode and Obsidian

### 🔌 **Extensible Plugin System**
- **Drop-and-Play Plugins:** Add new capabilities by placing Python files in the `plugins/` directory
- **Protocol-Based Architecture:** Clean plugin interface with automatic discovery and loading
- **Tool Registration:** Plugins automatically extend AI capabilities with new functions
- **Error Isolation:** Plugin failures don't crash the main application
- **Optional MCP Integration:** Connect to MCP servers for additional tools and capabilities (best compatibility with Claude, OpenAI, Cohere, Mistral, and Together AI)

### 🎨 **User Experience**
- **Clean UI Design:** Multi-pane interface optimized for productivity
- **Smart Autocomplete:** Type `/` to instantly find and reference vault files
- **Responsive Threading:** Non-blocking AI operations keep the UI smooth
- **Comprehensive Settings:** Easy configuration management with validation

### 🛡️ **Reliability Features**
- **Error Handling:** Custom exception hierarchy with graceful degradation
- **Connection Resilience:** Automatic retry logic and timeout management
- **Thread Safety:** Mutex-protected operations for multi-threaded stability
- **Logging:** Detailed logs for debugging and monitoring

---

## 🚀 Quick Start

### **⚡ Super Quick Setup (2 minutes)**

1. **Download & Install:**
   ```bash
   git clone https://github.com/KOPC149/obsidian-geode.git
   cd obsidian-geode
   pip install -r requirements.txt
   ```

2. **Get API Keys:**
   - **Gemini (recommended):** [Get free key](https://aistudio.google.com/app/apikey)
   - **Ollama (local/free):** [Download Ollama](https://ollama.ai/) instead

3. **Run Geode:**
   ```bash
   python geode_gui.py
   ```
   
4. **First Launch:** Settings dialog opens automatically - just enter your API keys!

### **Prerequisites**

1. **Python 3.8+** (3.10+ recommended)
2. **Obsidian** with the **Local REST API** community plugin enabled
3. **API Keys (choose your preferred provider):**
   - **Gemini (Primary):** Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))
   - **Claude:** Anthropic API key ([Console](https://console.anthropic.com/))
   - **OpenAI:** OpenAI API key ([Platform](https://platform.openai.com/api-keys))
   - **Cohere:** Cohere API key ([Dashboard](https://dashboard.cohere.com/api-keys))
   - **Mistral:** Mistral API key ([Platform](https://console.mistral.ai/))
   - **Perplexity:** Perplexity API key ([Settings](https://www.perplexity.ai/settings/api))
   - **Together AI:** Together API key ([Platform](https://api.together.xyz/settings/api-keys))
   - **Ollama:** Local installation only ([Download](https://ollama.ai/)) - no API key needed
   - **Required:** Obsidian Local REST API key (from plugin settings)

### **Installation**

1. **Clone and setup:**
   ```bash
   git clone https://github.com/KOPC149/obsidian-geode.git
   cd obsidian-geode
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   Or use the setup script:
   ```bash
   python setup.py
   ```

4. **Launch Geode:**
   ```bash
   python geode_gui.py
   ```

The application will guide you through the initial setup process on first launch.

---

## 🏗️ Architecture

Geode follows a modular architecture designed for maintainability and extensibility:

### **Backend Package (`geode_bridge/`)**
```
geode_bridge/
├── bridge.py          # Main orchestrator and AI integration
├── config.py          # Configuration management with validation
├── obsidian_api.py     # Obsidian API client
├── history.py          # Chat session persistence
├── plugins.py          # Dynamic plugin system
└── exceptions.py       # Error handling
```

### **Frontend (`geode_gui.py`)**
- **Multi-threaded PyQt6 interface** with responsive design
- **Component-based architecture** for maintainable UI code
- **Signal-based communication** between UI and backend
- **Dark theme support**

### **Plugin System (`plugins/`)**
- **Protocol-based development** for consistent plugin interfaces
- **Automatic discovery** and loading of plugin files
- **Tool registration** extends AI capabilities seamlessly
- **Error isolation** prevents plugin failures from affecting core functionality

---

## 🔧 Configuration

Geode supports multiple configuration methods:

### **GUI Settings**
Access settings through the application's settings dialog (⚙️ button).

### **Configuration File**
Create a `config.json` file in the project root. **Only include the API key for your chosen provider:**

**Example for Gemini (default):**
```json
{
  "ai_provider": "gemini",
  "gemini_api_key": "your_gemini_api_key",
  "obsidian_api_key": "your_obsidian_api_key",
  "obsidian_host": "127.0.0.1",
  "obsidian_port": "27124",
  "model_name": "gemini-2.5-pro",
  "plugin_directory": "plugins"
}
```

**Example for Claude:**
```json
{
  "ai_provider": "claude",
  "claude_api_key": "your_claude_api_key",
  "obsidian_api_key": "your_obsidian_api_key",
  "model_name": "claude-3-5-sonnet-20241022"
}
```

**Example for Ollama (local):**
```json
{
  "ai_provider": "ollama",
  "ollama_base_url": "http://localhost:11434",
  "obsidian_api_key": "your_obsidian_api_key",
  "model_name": "llama3.1:8b"
}
```

### **Environment Variables**
Override any setting with environment variables:
```bash
export AI_PROVIDER="gemini"
export GEMINI_API_KEY="your_gemini_key_here"
export CLAUDE_API_KEY="your_claude_key_here"
export OPENAI_API_KEY="your_openai_key_here"
export COHERE_API_KEY="your_cohere_key_here"
export MISTRAL_API_KEY="your_mistral_key_here"
export PERPLEXITY_API_KEY="your_perplexity_key_here"
export TOGETHER_API_KEY="your_together_key_here"
export OLLAMA_BASE_URL="http://localhost:11434"
export OBSIDIAN_API_KEY="your_obsidian_key_here"
export AI_MODEL="gemini-2.5-pro"
```

---

## 🤖 **AI Provider Guide**

Not sure which AI to choose? Here's what each one excels at:

| Provider | Best For | Key Strengths | Cost |
|----------|----------|---------------|------|
| **🔥 Gemini** | General use, coding | Fast, reliable, great reasoning | Low |
| **🧠 Claude** | Writing, analysis | Excellent writing, thoughtful responses | Medium |
| **💫 OpenAI** | Popular choice | Well-known, consistent, good docs | Medium |
| **⚡ Cohere** | Business use | Enterprise-grade, reliable API | Medium |
| **🇪🇺 Mistral** | European users | Privacy-focused, competitive performance | Low |
| **🏠 Ollama** | Privacy/offline | Completely local, no API costs | Free |
| **🔍 Perplexity** | Research | Web search built-in, fact-checking | Medium |
| **🤝 Together** | Open source | Access to many models, cost-effective | Low |

**💡 Quick Recommendations:**
- **New users:** Start with Gemini (default, reliable)
- **Privacy conscious:** Use Ollama (completely local)
- **Writers:** Try Claude (exceptional writing quality)
- **Researchers:** Use Perplexity (built-in web search)

---

## 🔌 Plugin Development

Extend Geode's capabilities with custom plugins:

### **Basic Plugin Structure**
```python
class MyPlugin:
    def get_name(self) -> str:
        return "my_awesome_plugin"
    
    def get_description(self) -> str:
        return "Does something awesome with vault data"
    
    def get_tools(self) -> list:
        return [self.my_tool_function]
    
    def my_tool_function(self, parameter: str) -> str:
        """This function will be available to the AI."""
        return f"Processed: {parameter}"
```

### **Plugin Guidelines**
- Place `.py` files in the `plugins/` directory
- Implement the required protocol methods (`get_name`, `get_description`, `get_tools`)
- Return tool functions that the AI can call
- Handle errors gracefully within your tools
- Use descriptive function names and docstrings

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### **Development Setup**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes with tests
4. Submit a pull request

### **Areas for Contribution**
- 🐛 Bug fixes and stability improvements
- ✨ New core features
- 🔌 Plugin development and examples
- 📚 Documentation improvements
- 🎨 UI/UX enhancements
- 🧪 Test coverage expansion

### **Code Standards**
- Follow PEP 8 style guidelines
- Add comprehensive docstrings
- Include type hints where appropriate
- Write tests for new functionality
- Update documentation as needed

---

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

---

## 🛠️ **Troubleshooting**

### **Common Issues & Solutions**

**❌ "Failed to connect to Obsidian"**
- ✅ Install the "Local REST API" plugin in Obsidian
- ✅ Enable the plugin in Obsidian settings
- ✅ Check the API key matches between Obsidian and Geode

**❌ "AI API authentication failed"**
- ✅ Verify your API key is correct (copy-paste carefully)
- ✅ Check if your API key has expired or hit limits
- ✅ For Ollama: Make sure Ollama is running (`ollama serve`)

**❌ "Model not found"**
- ✅ Try a different model from the dropdown
- ✅ For Ollama: Pull the model first (`ollama pull llama3.1:8b`)

**❌ "App won't start"**
- ✅ Update Python: `python --version` (need 3.8+)
- ✅ Install dependencies: `pip install -r requirements.txt`
- ✅ Check the logs in `geode.log`

**🆘 Still stuck?** 
- Check [Issues](https://github.com/KOPC149/obsidian-geode/issues) for solutions
- Create a new issue with your `geode.log` file

---

## ⭐ Acknowledgments

This project was primarily developed through AI-assisted coding and represents a collaboration between human creativity and AI capabilities:

### **Core Technologies**
- The amazing work put into [Obsidian](https://obsidian.md/) by the development team
- The incredible power of **Google's Gemini AI models**
- The essential **Obsidian Local REST API** plugin for vault integration
- The **PyQt6** framework for desktop applications
- The **Python ecosystem** and its libraries

### **AI Development Partners**
- **Gemini 2.5** for the initial development, core architecture design, and foundational implementation that created this application
- **Claude (Anthropic)** for comprehensive code review, refactoring, and architecture improvements that enhanced the codebase

### **Community**
- All contributors, testers, and users who help make Geode better
- The Obsidian community for inspiration and feedback
- Open source projects that make development possible

---

## 🔗 Links

- **Issues:** [Report bugs or request features](https://github.com/KOPC149/obsidian-geode/issues)
- **Discussions:** [Ask questions and share ideas](https://github.com/KOPC149/obsidian-geode/discussions)
- **Obsidian:** [Download Obsidian](https://obsidian.md/)
- **Local REST API Plugin:** [Essential plugin for vault integration](https://github.com/coddingtonbear/obsidian-local-rest-api)

---

*Built with ❤️ through AI-assisted development for the knowledge management community*
