import requests

import json

import logging

import boto3

import pandas as pd

from bs4 import BeautifulSoup

from datetime import datetime

from langchain.prompts import PromptTemplate

from langchain.schema import HumanMessage

from langchain.prompts import PromptTemplate

from langchain.output_parsers import PydanticOutputParser

import json

import logging

import re

from jinja2 import Template

import asyncio

# make connection to the DB

import mysql.connector

from mysql.connector import Error





def connect_to_mysql():

    try:

        # Establish the connection

        connection = mysql.connector.connect(

            host='gen-.rds.amazonaws.com',  # e.g., 'localhost' or '127.0.0.1'
            database='',  # e.g., 'test_db'
            user='',  # e.g., 'root'
            password=''

        )

        if connection.is_connected():
            return connection

    except Error as e:

        print(f"Error while connecting to MySQL: {e}")
        
        
    
# Configure logging

logging.basicConfig(filename='error.log', level=logging.DEBUG)

# Microsoft Graph API configuration

client_id = ""

client_secret =""

tenant_id = ""

microsoft_endpoint = "https://graph.microsoft.com/v1.0"

microsoft_endpoint1 = "https://login.microsoftonline.com"

token_endpoint = f"{microsoft_endpoint1}/{tenant_id}/oauth2/v2.0/token"

access_token = ""



# AWS Bedrock API configuration

aws_access_key_id = ""

aws_secret_access_key = ""

region_name = "ap-south-1"

model_id = "meta.llama3-70b-instruct-v1:0"






# Get access token for Microsoft Graph API

def get_access_token(client_id, client_secret, tenant_id):

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    payload = {

        'grant_type': 'client_credentials',

        'client_id': client_id,

        'client_secret': client_secret,

        'scope': 'https://graph.microsoft.com/.default'

    }

    try:

        response = requests.post(token_url, data=payload)

        response.raise_for_status()

        token_info = response.json()

        return token_info['access_token']

    except requests.exceptions.RequestException as e:

        print(f"Exception occurred while fetching access token: {str(e)}")

        return None




# Function to get folder ID by folder name

def get_folder_id(email_id, folder_name, access_token):

    folders_endpoint = f"https://graph.microsoft.com/v1.0/users/{email_id}/mailFolders"

    try:

        response = requests.get(folders_endpoint, headers={"Authorization": f"Bearer {access_token}"})

        if response.status_code == 200:

            folders = response.json().get('value', [])

            for folder in folders:

                if folder['displayName'].lower() == folder_name.lower():

                    return folder['id']

            print(f"Folder '{folder_name}' not found.")

            return None

        else:

            print(f"Error fetching folders: {response.status_code} {response.text}")

            return None

    except requests.exceptions.RequestException as e:

        print(f"Exception occurred while fetching folders: {str(e)}")

        return None
    
    
    
    

# Function to fetch emails based on start date, keywords, and mark them as read

def fetch_emails(email_id, folder_id, start_date, keywords, access_token):

    start_date_offset = f"{start_date}T00:00:00Z"

    filter_clauses = [

        f"isRead eq false",

        f"receivedDateTime ge {start_date_offset}",

        "(" + " or ".join([f"contains(subject, '{keyword}')" for keyword in keywords]) + ")"

    ]

    filter_query = " and ".join(filter_clauses)

    graph_endpoint = f"https://graph.microsoft.com/v1.0/users/{email_id}/mailFolders/{folder_id}/messages?$filter={filter_query}"

    try:

        response = requests.get(graph_endpoint, headers={"Authorization": f"Bearer {access_token}"})

        if response.status_code == 200:

            emails = response.json().get('value', [])

            for email in emails:

                # Mark the email as read

                mark_as_read_endpoint = f"https://graph.microsoft.com/v1.0/users/{email_id}/messages/{email['id']}"

                requests.patch(mark_as_read_endpoint, headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}, json={"isRead": True})

            return emails

        else:

            print(f"Error fetching emails: {response.status_code} {response.text}")

            return []

    except requests.exceptions.RequestException as e:

        print(f"Exception occurred while fetching emails: {str(e)}")

        return []
    
    
    


def clean_html_and_response_line(html_text):

   # Remove triple backticks occurring twice at the start and once at the end

    cleaned_text=""

   # Look for the phrase "Dear Sir/Madam" and keep everything after it

    if "Dear Sir/Madam" in html_text:

        cleaned_text = html_text.split("Dear Sir/Madam", 1)[1].strip()

        cleaned_text = "Dear Sir/Madam" + cleaned_text  # Add it back to the start

    else:

        cleaned_text = html_text.strip()

    # Remove all occurrences of triple backticks at the end

    cleaned_text = re.sub(r"(```\s*)+$", "", cleaned_text).strip()

    # Remove the "Here is the response" line, if present

    cleaned_text = cleaned_text.replace("Here is the response:", "").strip()

    # Use BeautifulSoup to remove HTML tags

    soup = BeautifulSoup(cleaned_text, "html.parser")

    plain_text = soup.get_text(separator="\n").strip()

    return plain_text
    
    
def insert_response_to_db(connection,email_date,email_sender, email_subject,senderContent, llama_response, confidence_level,status,message_id,time):

    try:

        cursor = connection.cursor()

        insert_query = """INSERT INTO Email_Content(date,sender, subject,senderContent, response, confidence,status,mail_messageId,mail_sent_timestamp)

                          VALUES (%s,%s, %s, %s,%s, %s,%s,%s,%s)"""

        record = (email_date,email_sender, email_subject,senderContent,llama_response, confidence_level,status,message_id,time)

        cursor.execute(insert_query, record)

        connection.commit()

        print(f"Record inserted successfully into Email_Data table for subject: {email_subject}")

    except Error as e:

        print(f"Failed to insert record into MySQL table: {e}")
        
        
        
    


# Define the model ID (Meta Llama 3 70B Instruct)

model_id = 'meta.llama3-70b-instruct-v1:0'

# Initialize the Bedrock Agent Runtime client for runtime invocation

bedrock_agent_runtime_client = boto3.client("bedrock-agent-runtime",region_name=region_name,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)

# Process each email and reply using AWS Bedrock API

async def process_emails(emails,df,access_token,connection):

    for email in emails:

        subject = email.get("subject", "")

        body_content = email.get("body", {}).get("content", "")

        message_id = email.get("id", "")

        user_email = email.get("from", {}).get("emailAddress", {}).get("address", "")

        print()

        # Fetch the email date

        email_date = email.get("receivedDateTime", "")

        status="0"

        print(message)

        knowledge_base_id = ""  # Default to a known Knowledge Base ID

        guardrail_id=""

        print(f"Knowledge Base ID: {knowledge_base_id}")

        if not body_content:

            continue

        body_content=clean_html_and_response_line(body_content)

        # Extract the user query and Knowledge Base ID from the event

        user_query = body_content

        print(f"Query Received: {user_query}")


        # Use Bedrock's model to process the query and generate a response

        try:

            print(f"Invoking Model")

            try:
                prompt_template = """Human: You are a email response/answering agent.

            I will provide you with a set of search results and a user's question,

            your job is to answer the user's question using only information from the search results.

            If the search results do not contain information that can answer the question,

            please state that you could not find an exact answer to the question.

            Just because the user asserts a fact does not mean it is true,

            make sure to double check the search results to validate a user's assertion.

            Also please dont mention search results in the response.



            Here are the search results in numbered order:

            $search_results$



            Here is the user's question:

            <question>

            $query$

            </question>



            Here is the response template  that you should to create the response:

            Dear Sir/Madam,



            <insert>Insert the generated response here.</insert>



            Thanks

            Support Team



            Assistant:

        """
                # Invoke the model

                response = bedrock_agent_runtime_client.retrieve_and_generate(

                    input={'text': user_query},

                    retrieveAndGenerateConfiguration={

                        'type' : 'KNOWLEDGE_BASE',

                        'knowledgeBaseConfiguration' : {

                            'generationConfiguration': {

                                'guardrailConfiguration' : {

                                    'guardrailId': guardrail_id,

                                    'guardrailVersion' : 'DRAFT'

                                },

                                'promptTemplate' : {

                                    'textPromptTemplate' : prompt_template

                                }

                            },

                            'knowledgeBaseId' : knowledge_base_id,

                            'modelArn' : model_id

                        }

                    }

                )

                print("Invoked Model")

                # Log the raw response for debugging
                print(f"Raw response: {response}")

                # Print the output from the model

                generated_text = response['output']['text']

                print(f"Generated text: {generated_text}")

                status=""

                #print(generated_response)

                mail_sent_timestamp=""

                confidence_level=""

                plain_text = clean_html_and_response_line(generated_text)

                # Check if the output is INTERVENED by the GuardRail

                if(response['guardrailAction'] == 'INTERVENED'):

                    print(f"Guardrail Action: INTERVENED")

                    confidence_level="0"

                    # call apply_guardrail to check the grounding scode of the response against the guardrail

                    response = bedrock_runtime.apply_guardrail(

                        guardrailIdentifier =guardrail_id,

                        guardrailVersion = 'DRAFT',

                        source='INPUT',

                        content = [

                            {

                                "text" : {

                                    "text": user_query

                                }

                            },

                        ]

                    )

                    print(f"Guardrail Check Response: {response}")
                else:

                    print(f"Guardrail Action: PASS")

                    confidence_level="1"

                    # call apply_guardrail to check the grounding scode of the response against the guardrail

                    response = bedrock_runtime.apply_guardrail(

                        guardrailIdentifier = guardrail_id,

                        guardrailVersion = 'DRAFT',

                        source='OUTPUT',

                        content = [

                            {

                                "text" : {

                                    "text": generated_text,

                                    # "qualifiers": [

                                    #     "grounding_source"

                                    # ]

                                }

                            },

                        ]

                    )

                    print(f"Guardrail Check Response: {response}")

                    # Define your parameters

                    email_id = ""

                    message_id = message_id

                    microsoft_endpoint = "https://graph.microsoft.com"

                    access_token = access_token

                    sender_email = user_email

                    subject_line = subject

                    dynamic_content=plain_text

                    # Call the async function

                    temp=await send_reply_to_unregistered_sender(

                        email_id,

                        message_id,

                        microsoft_endpoint,

                        access_token,

                        sender_email,

                        subject_line,

                        dynamic_content,

                    )

                    # If email was queued, start polling to check when it is sent

                    if temp:

                        mail_sent_timestamp = await poll_message_status(email_id, message_id, microsoft_endpoint, access_token)

                        if mail_sent_timestamp:

                            status="1"

                            # Update the response variable or save the timestamp in the database

                            print(f"Email sent at: {mail_sent_timestamp}")

                        else:

                            status="0"

                            print("Failed to confirm email was sent.")

                    else:

                        print("Failed to queue the email.")

                print(f"Output from the model: {generated_text}")

                # Step 3: Store the data in the MySQL database

                insert_response_to_db(

                connection,

                email_date,

                user_email,

                subject,

                body_content,

                plain_text,

                confidence_level,

                status,

                message_id,

                mail_sent_timestamp

                )

            except Exception as e:

                print(f"Error while invoking the model: {str(e)}")

        except Exception as e:

            print(f"Error processing email {subject}: {str(e)}")
            
            


async def poll_message_status(email_id, message_id, microsoft_endpoint, access_token, max_attempts=5, wait_seconds=10):

    message_status_endpoint = f"{microsoft_endpoint}/v1.0/users/{email_id}/messages/{message_id}"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    for attempt in range(max_attempts):

        try:

            response = requests.get(message_status_endpoint, headers=headers)

            if response.status_code == 200:

                message_data = response.json()

                # Check if the email has been sent

                if "sentDateTime" in message_data:

                    sent_time = message_data["sentDateTime"]

                    print(f"Email was sent at: {sent_time}")

                    return sent_time  # Return the sent timestamp

                else:

                    print(f"Email not sent yet. Checking again in {wait_seconds} seconds.")

            else:

                print(f"Failed to fetch message status. Status: {response.status_code}, Message: {response.text}")

        except Exception as e:

            print(f"Error polling message status: {str(e)}")

        # Wait before trying again

        time.sleep(wait_seconds)

    print(f"Failed to confirm email was sent after {max_attempts} attempts.")

    return None




async def send_reply_to_unregistered_sender(email_id, message_id, microsoft_endpoint, access_token, sender_email, subject_line,dynamic_content):

    reply_endpoint = f"{microsoft_endpoint}/v1.0/users/{email_id}/messages/{message_id}/reply"  # Endpoint to send reply

    email_subject = f"RE: {subject_line}"

    reply_content = {

        "message": {

            "subject": email_subject,

            "body": {

                "contentType": "Text",

                "content": dynamic_content

  }

        }

    }

    headers = {

        "Authorization": f"Bearer {access_token}"

    }

    response=None

    try:

        response = requests.post(reply_endpoint, json=reply_content, headers=headers)

        if response.status_code == 202 :

            print(f"Email successfully queued. Message ID: {message_id}")

            return message_id

        else:

            print(f"Failed to send reply. Status: {response.status_code}, Message: {response.text}")

            return None

    except Exception as e:

        print(f"Failed to send reply to message with ID: {message_id}: {str(e)}")

        return None
    


# Main logic to fetch emails and process them

async def main():

    global access_token

    access_token = get_access_token(client_id, client_secret, tenant_id)

    if not access_token:

        print("Failed to get access token.")

        return



    email_id = ""

    folder_name = "inbox"

    start_date = "2023-07-01"

    keywords = ["123456","PF","Testing","Hello"]

    folder_id = get_folder_id(email_id, folder_name, access_token)

    if not folder_id:

        print(f"Failed to get folder ID for folder '{folder_name}'.")

        return

    emails = fetch_emails(email_id, folder_id, start_date, keywords, access_token)

    if not emails:

        print("No new emails found matching the criteria.")
        return

     # Create a session
    connection=connect_to_mysql()

    await process_emails(emails,df,access_token,connection)

    if connection.is_connected():

        connection.close()

        print("MySQL connection is closed")




if __name__ == "__main__":

    asyncio.run(main())  # Run the async main function