import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_from_sheets(sheet_page):
    sheets='1WyTZhH5zl-IKGL6iYR1nL9W2n_8RNBg23BcCMcLsPys'
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    cred_path = resource_path('credentials.json')
    creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path,scope)
    client = gspread.authorize(creds)
    sheet =  client.open_by_key(sheets)

    wh_list_obj = sheet.worksheets()
    wh_list = list()
    for wh in wh_list_obj:
        wh_list.append(wh.title)
    if sheet_page not in wh_list:
        df = None
    else:
        worksheet = sheet.worksheet(sheet_page)
        df = pd.DataFrame(worksheet.get_all_records())
    return df

def update_sheets(df,sheet_page):
    sheets='1WyTZhH5zl-IKGL6iYR1nL9W2n_8RNBg23BcCMcLsPys'
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    cred_path = resource_path('credentials.json')
    creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path,scope)
    client = gspread.authorize(creds)
    sheet =  client.open_by_key(sheets)

    wh_list_obj = sheet.worksheets()
    wh_list = list()
    for wh in wh_list_obj:
        wh_list.append(wh.title)
    if sheet_page not in wh_list:
        nrows=len(df.axes[0])
        ncols=len(df.axes[1])
        worksheet = sheet.add_worksheet(title=sheet_page, rows=nrows, cols=ncols)
    else:
         worksheet = sheet.worksheet(sheet_page)

    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

    
