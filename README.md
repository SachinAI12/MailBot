
# MailBot

MailBot is a Python-based application designed to intelligently process emails using the Microsoft Graph API and AI models for automated email responses. It reads, analyzes, and replies to emails based on predefined patterns and content similarity. The bot ensures high-quality responses through confidence checks and response guardrails, ensuring safe and accurate communication.

## Features

- **Email Fetching**: Retrieve emails from a specified folder using the Microsoft Graph API.
- **Automatic Response Generation**: Generates replies based on the email content using AI-powered models.
- **Confidence Level Checks**: Ensures the generated responses meet a specified confidence threshold before sending.
- **Guardrails**: Uses customizable rules and patterns to ensure only relevant and safe responses.
- **Customizable**: Easily extendable for more features, models, or different response formats.

## Technologies Used

- **Python 3.x**: Programming language used to build the backend.
- **Microsoft Graph API**: Provides access to emails, calendar, and other Microsoft services.
- **AI Models**: Uses pre-trained AI models (e.g., LLaMA) for generating intelligent email responses.
- **Pandas**: Used for data manipulation and handling structured data.
- **SentenceTransformers**: For semantic similarity scoring to help determine the relevance of responses.

## Requirements

- **Python 3.x**
- **Microsoft Azure Active Directory credentials**
- **AWS account for LLaMA** (if using this model for response generation)

## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SachinAI12/MailBot.git
   cd MailBot
   ```

2. **Install the required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Microsoft Graph API**:
   - Register your application in Microsoft Azure.
   - Obtain the client ID, tenant ID, and secret to access the Graph API.
   - Follow the [Microsoft Graph API documentation](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app) for setup instructions.

4. **Set up AWS Bedrock for LLaMA** (if applicable):
   - Set up an AWS account and retrieve the necessary API keys for AWS Bedrock.
   - Follow AWS documentation to deploy and configure the LLaMA model.

## Usage

1. **Run the script**:
   ```bash
   python main.py
   ```

2. The bot will automatically fetch unread emails from the specified folder, analyze the content, and generate a response. If the response meets the confidence level, it will be sent back to the email sender.

## Contributing

1. **Fork the repository**.
2. **Create a new branch**:
   ```bash
   git checkout -b feature-branch
   ```
3. **Make your changes and commit them**:
   ```bash
   git commit -am 'Add new feature'
   ```
4. **Push the branch**:
   ```bash
   git push origin feature-branch
   ```
5. **Submit a Pull Request** to merge your changes.

## License

Distributed under the MIT License. See the [LICENSE](LICENSE) file for more details.
