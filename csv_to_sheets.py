from __future__ import print_function

import os.path
import glob
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

global service
global spreadsheetId


def get_sheet_id(spreadsheet, title):
    # gets the sheet_id for given name
    for _sheet in spreadsheet['sheets']:
        if _sheet['properties']['title'] == title:
            return _sheet['properties']['sheetId']


def delete_sheet(sheet_id):
    # deletes a sheet with the given name
    body = {
        'requests': [{
            'deleteSheet': {
                'sheetId': sheet_id,
            }
        }]
    }

    try:
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheetId,
            body=body).execute()
    except HttpError as err:
        print(err)


def add_sheet(title):
    # add a new sheet with the given name
    body = {
        'requests': [{
            'addSheet': {
                'properties': {
                    'title': title,
                }
            }
        }]
    }

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheetId,
        body=body
    ).execute()


def upload_csv(csv_path, sheet_id):
    with open(csv_path, 'r') as csv_file:
        csvContents = csv_file.read()
    body = {
        'requests': [{
            'pasteData': {
                "coordinate": {
                    "sheetId": sheet_id,
                    "rowIndex": "0",
                    "columnIndex": "0",
                },
                "data": csvContents,
                "type": 'PASTE_NORMAL',
                "delimiter": ',',
            }
        }]
    }
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheetId,
        body=body
    ).execute()

    return response


def list_files(folder):
    return glob.glob(folder + "/*.csv")


def main(argv):
    global folder
    global spreadsheetId

    if len(argv) < 2:
        print("Usage: csv_to_sheets.py <folder> <spreadsheetId>")
        sys.exit(2)

    folder = argv[0]
    spreadsheetId = argv[1]

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        global service
        service = build('sheets', 'v4', credentials=creds)

        spreadsheet = service.spreadsheets().get(
            spreadsheetId=spreadsheetId
        ).execute()

        # retrieve the list of CSV files
        files = list_files(
            folder
        )

        for path in files:
            # get the sheet name from the file name
            sheet_name = os.path.splitext(os.path.basename(path))[0]

            print("Preparing Sheets: " + sheet_name)
            sheet_id = get_sheet_id(spreadsheet, sheet_name)
            if sheet_id > -1:
                delete_sheet(sheet_id)
            add_sheet(title=sheet_name)

        spreadsheet = service.spreadsheets().get(
            spreadsheetId=spreadsheetId
        ).execute()

        for path in files:
            # get the sheet name from the file name
            sheet_name = os.path.splitext(os.path.basename(path))[0]

            print("Uploading: " + sheet_name)
            sheet_id = get_sheet_id(spreadsheet, sheet_name)
            if sheet_id > -1:
                upload_csv(path, sheet_id)

    except HttpError as err:
        print(err)


if __name__ == "__main__":
    main(sys.argv[1:])
