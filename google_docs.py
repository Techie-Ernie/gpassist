import re
import os

# Google API
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]


def get_doc_content(url):
    documentID = re.findall("/document/d/([a-zA-Z0-9-_]+)", url)[
        0
    ]  # Regex to find the documentID
    print(documentID)
    if url:
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        try:
            service = build("docs", "v1", credentials=creds)
            # Retrieve the documents contents from the Docs service.
            document = service.documents().get(documentId=documentID).execute()
            print(f"The title of the document is: {document.get('title')}")
            text = ""
            # get doc content
            doc_content = document.get("body").get("content")
            for element in doc_content:
                # Handle standalone paragraphs
                if "paragraph" in element:
                    for run in element["paragraph"].get("elements"):
                        if "textRun" in run:
                            text += run["textRun"]["content"]
                # Handle tables
                elif "table" in element:
                    for row in element["table"]["tableRows"]:
                        for cell in row["tableCells"]:
                            for cell_content in cell.get("content"):
                                if "paragraph" in cell_content:
                                    for run in cell_content["paragraph"].get(
                                        "elements"
                                    ):
                                        if "textRun" in run:
                                            text += run["textRun"]["content"]

            return text

        except HttpError as err:
            print(err)
