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

            print(text)

        except HttpError as err:
            print(err)


def add_current_and_child_tabs(tab, all_tabs):
    """Adds the provided tab to the list of all tabs, and recurses through and
    adds all child tabs.

    Args:
        tab: a Tab from a Google Doc.
        all_tabs: a list of all tabs in the document.
    """
    all_tabs.append(tab)
    for tab in tab.get("childTabs"):
        add_current_and_child_tabs(tab, all_tabs)


def get_all_tabs(doc):
    """Returns a flat list of all tabs in the document in the order they would
    appear in the UI (top-down ordering). Includes all child tabs.

    Args:
        doc: a document.
    """
    all_tabs = []
    # Iterate over all tabs and recursively add any child tabs to generate a
    # flat list of Tabs.
    for tab in doc.get("tabs"):
        add_current_and_child_tabs(tab, all_tabs)
    return all_tabs


def read_paragraph_element(element):
    """Returns the text in the given ParagraphElement.

    Args:
        element: a ParagraphElement from a Google Doc.
    """
    text_run = element.get("textRun")
    if not text_run:
        return ""
    return text_run.get("content")


def read_structural_elements(elements):
    """Recurses through a list of Structural Elements to read a document's text
    where text may be in nested elements.

    Args:
        elements: a list of Structural Elements.
    """
    text = ""
    for value in elements:
        if "paragraph" in value:
            elements = value.get("paragraph").get("elements")
            for elem in elements:
                text += read_paragraph_element(elem)
        elif "table" in value:
            # The text in table cells are in nested Structural Elements and tables may
            # be nested.
            table = value.get("table")
            for row in table.get("tableRows"):
                cells = row.get("tableCells")
                for cell in cells:
                    text += read_structural_elements(cell.get("content"))
        elif "tableOfContents" in value:
            # The text in the TOC is also in a Structural Element.
            toc = value.get("tableOfContents")
            text += read_structural_elements(toc.get("content"))
    return text


if __name__ == "__main__":
    get_doc_content(
        "https://docs.google.com/document/d/1cg7nsqEYdqf9OlXOBOl59xYwXy_5r54Z1_62uXMxOSA/edit?tab=t.0"
    )
