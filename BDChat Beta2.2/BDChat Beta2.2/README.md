# Law Firm FAQ Chatbot v2.1

A Python-based chatbot that provides automated responses to legal queries using Azure's DeepSeek AI model and a structured FAQ dataset.

## Project Structure

```
FAQChat Beta2.1/
├── chatbot.py                 # Main chatbot application
├── requirements.txt           # Python dependencies
├── README.md                  # This documentation
└── (Bot4Pro) Simulated FAQ Dataset (with topic).xlsx  # FAQ dataset
```

## Features

- Interactive GUI interface using tkinter
- Topic-based response generation
- Automatic fee range formatting
- Warning message for legal disclaimers
- Robust error handling and retry mechanisms

## Prerequisites

- Python 3.8 or higher
- Azure DeepSeek API access
- Required Python packages (listed in requirements.txt)

## Installation

1. Clone or download the FAQChat Beta2.1 folder
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The chatbot requires the following configuration in `chatbot.py`:
- DEEPSEEK_API_KEY: Your Azure DeepSeek API key
- DEEPSEEK_ENDPOINT: Azure DeepSeek endpoint URL
- DEEPSEEK_MODEL: Model name (currently set to "deepseek-r1")

## Usage

1. Ensure the Excel file "(Bot4Pro) Simulated FAQ Dataset (with topic).xlsx" is in the same directory as chatbot.py
2. Run the chatbot:
   ```bash
   python chatbot.py
   ```
3. Type your legal query in the input field and press Enter or click Send

## Response Format

The chatbot provides responses in the following format:
1. Main response content
2. Selected relevant topics
3. Warning message about AI-generated content

## Error Handling

The chatbot includes:
- Automatic retry mechanism for failed responses
- Fallback topics for topic selection failures
- Graceful error messages for users

## Notes for Team Members

1. The project is self-contained and can be run on any computer with Python installed
2. Make sure to update the Azure DeepSeek API credentials before running
3. The Excel dataset should not be modified without updating the code accordingly
4. All dependencies are listed in requirements.txt

## Limitations

- Requires internet connection for API access
- Response quality depends on the FAQ dataset
- Maximum response length is limited by the API token limit

## Support

For technical issues or questions, please contact the development team. 