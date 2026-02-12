# PPT Translation Agent

A powerful web application built with Streamlit that intelligently translates text boxes in PowerPoint presentations (currently does not support tables, SmartArt, or charts) while preserving original design and formatting. This project leverages LangGraph for workflow orchestration and supports multiple LLM providers for high-quality translations.

![image-20260211181128512](asset/image-20260211181128512.png)

![image-20260211182426765](asset/image-20260211182426765.png)

![PPT Translation Agent](https://img.shields.io/badge/Streamlit-Web%20App-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-green.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-Workflow-orange.svg)
![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)

## 🚀 Features

- **Smart Translation**: Uses advanced LLM models for professional-quality translations
- **Design Preservation**: Maintains original PPT layout, formatting, and styling
- **Multi-Language Support**: English, Chinese, Japanese, and Korean
- **Concurrent Processing**: Efficient batch translation with configurable concurrency
- **Visual Width Intelligence**: Automatically adjusts font sizes for CJK vs Latin scripts
- **Professional Formatting**: Preserves Arabic numerals, brand names, and business tone
- **Web Interface**: User-friendly Streamlit interface with progress tracking

## 📋 Requirements

- Python 3.12
- Streamlit
- LangGraph
- LangChain
- python-pptx
- python-dotenv
- asyncio

## 🔧 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Carinalin/HelloAgents.git
   cd 2_SlidesTranslator
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
3. **Configure API Keys:**
  
   - Create a `.env` file in the project root
   - Add your LLM provider API keys:
   ```
   DEEPSEEK_API_KEY=your_deepseek_api_key
   OPENAI_API_KEY=your_openai_api_key
   # Add other provider keys as needed
   ```

## 🚀 Usage

### Launch the Web Application

```bash
streamlit run app.py
```

### How to Use

1. **Upload PPT**: Use the file uploader to upload your PowerPoint presentation (.pptx)
2. **Select Target Language**: Choose from English, Chinese, Japanese, or Korean
3. **Configure Performance**: Adjust concurrency and batch size settings
4. **Start Translation**: Click "Begin Translation" and monitor progress
5. **Download Result**: Download the translated PPT with preserved formatting

### Supported LLM Providers

The application supports multiple LLM providers:
- **DeepSeek**: Default provider
- **OpenAI**: GPT-3.5-turbo, GPT-4, etc.
- **Anthropic**: Claude models
- **Grok (XAI)**: Grok models

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with your API keys:

```env
# LLM Provider API Keys
DEEPSEEK_API_KEY=your_deepseek_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
XAI_API_KEY=your_xai_api_key_here
```

### Performance Settings

- **Max Concurrent Requests**: 1-20 (default: 10)
- **Batch Size**: 1-10 (default: 5)

Higher values provide faster processing but may increase API costs and rate limiting.

## 🏗️ Architecture

```
2_SlidesTranslator/
├── app.py                    # Main Streamlit application
├── models.py                 # LLM configuration and initialization
├── graph.py                  # LangGraph workflow orchestration
├── utils.py                  # PPT manipulation utilities
├── prompts/
│   └── translation_instruction.txt  # Translation prompt template
├── template/                 # Sample PPT files
└── .env                      # Environment variables (create by yourself)
```

### Core Components

1. **app.py**: Streamlit web interface with file upload, language selection, and progress tracking
2. **graph.py**: Three-stage workflow - Parse → Translate → Reconstruct
3. **utils.py**: Advanced PPT manipulation with visual width calculation and layout optimization
4. **models.py**: Multi-provider LLM configuration with environment variable management

### Translation Workflow

1. **Parse PPT**: Extract text from PowerPoint slides with position and formatting data
2. **Translate**: Use async LLM calls with intelligent batching and retry logic
3. **Reconstruct**: Intelligently rebuild PPT with translated text, adjusting layout as needed

## 🧠 Smart Features

### Visual Width Intelligence
- Automatically calculates visual width differences between CJK and Latin scripts
- Adjusts font sizes to prevent text overflow
- Maintains text box proportions and layout integrity

### Professional Translation Rules
- Preserves Arabic numerals unchanged (e.g., "500" stays "500")
- Maintains brand/product names appropriately
- Professional business-appropriate tone
- Concise presentation-friendly output

### Layout Optimization
- Dynamic font size reduction based on text length ratios
- Collision detection for text boxes
- Group processing for consistent formatting
- Smart text wrapping and overflow handling

## 📊 Performance

- **Concurrent Processing**: Configurable batch sizes for efficient API usage
- **Progress Tracking**: Real-time progress updates during translation
- **Memory Efficient**: Temporary file handling for large presentations
- **Error Handling**: Robust retry logic and graceful error recovery

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Streamlit for the web framework
- LangGraph for workflow orchestration
- python-pptx for PowerPoint manipulation
- Various LLM providers for translation capabilities

## 🐛 Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure your `.env` file contains valid API keys
2. **File Upload Issues**: Verify the file is a valid .pptx format
3. **Translation Quality**: Adjust the temperature parameter in `models.py`
4. **Performance**: Increase batch size for faster processing (may increase costs)

### Getting Help

- Check the console for detailed error messages
- Verify API key validity with your provider
- Ensure sufficient API rate limits for your usage

## 📞 Contact

For questions and support, please open an issue in the repository or contact the maintainers.
