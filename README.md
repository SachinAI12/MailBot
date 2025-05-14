# AI-Powered Email Response Bot

This Python-based email bot integrates **Microsoft Graph API** and **AWS Bedrock's LLaMA3 70B model** to automate reading, analyzing, and replying to incoming emails. It retrieves email content from a specific folder, processes it using Bedrock's LLM via a knowledge base, evaluates response confidence with guardrails, and optionally stores results in a MySQL database.

---

## 🔧 Features

- ✅ Connects to a specified folder in Microsoft Outlook using Graph API
- ✅ Reads unread emails filtered by date and subject keywords
- ✅ Uses AWS Bedrock (LLaMA3 70B) to generate context-aware replies
- ✅ Cleans and formats HTML email bodies
- ✅ Applies guardrails to check grounding and response safety
- ✅ Logs and stores all email metadata and response in a MySQL database

---

## 📁 Project Structure

```plaintext
.
├── main.py                  # Main script for reading & replying to emails
├── requirements.txt         # Python dependencies
├── error.log                # Logs any runtime or API errors
└── README.md                # Project documentation
📦 Requirements
Ensure you have the following:

Python 3.8+

A registered Azure AD App with Mail.ReadWrite and Mail.Send permissions

AWS credentials with Bedrock access

MySQL server accessible for logging

Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
🔐 Configuration
Microsoft Graph API:
Config	Description
client_id	Azure AD Application (client) ID
client_secret	Application secret
tenant_id	Azure Directory (tenant) ID
email_id	Email address to fetch messages from

AWS Bedrock:
Config	Description
aws_access_key_id	AWS access key
aws_secret_access_key	AWS secret key
region_name	AWS region (e.g., ap-south-1)
model_id	LLaMA3 model ARN
knowledge_base_id	ID of knowledge base in Bedrock
guardrail_id	Guardrail ID to apply grounding

MySQL:
Update credentials for:

python
Copy
Edit
mysql.connector.connect(
    host='your-rds-endpoint',
    database='your-database',
    user='your-username',
    password='your-password'
)
🚀 How It Works
Access Token: Retrieves an OAuth token using Microsoft credentials.

Folder ID: Resolves the folder ID (e.g., “ProgramFolder”) from its name.

Email Fetching: Filters unread emails using Graph API based on keywords and date.

Processing:

Cleans HTML email content

Invokes LLaMA3 model with a prompt template and knowledge base

Applies AWS guardrails to check the confidence of the response

Storage: Stores query, response, sender info, confidence level, and timestamp in MySQL.

📄 Sample Output Format (MySQL Table: Email_Content)
Field	Description
date	Email received date
sender	Email sender address
subject	Subject of the email
senderContent	Cleaned text body of the email
response	Generated LLM response
confidence	Confidence level (0 or 1)
status	Processing status
mail_messageId	Graph API message ID
mail_sent_timestamp	Time when response is generated

🛡️ Guardrails and Confidence Levels
The system uses AWS Bedrock guardrails to:

Filter inappropriate or hallucinated content

Return a confidence_level of 1 (high) or 0 (low)

Intervene and log when responses violate content policies

🧪 Testing
You can simulate an incoming email by sending a message to the monitored folder with known keywords. Run the script and observe:

Terminal logs

Database entries

Email replies (optional extension)

