import base64
import mimetypes
import os
import tempfile

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def build_drive_service(obj):
    company = obj.env.user.company_id.sudo()
    creds = Credentials(
        token=company.gdrive_access_token,
        refresh_token=company.gdrive_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=company.gdrive_client_id,
        client_secret=company.gdrive_client_secret,
        scopes=['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/drive.file'],
    )
    return build('drive', 'v3', credentials=creds)


def create_folder_on_drive(obj, name, parent_id=None):
    metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        metadata['parents'] = [parent_id]

    service = build_drive_service(obj)
    file = service.files().create(
        body=metadata,
        fields='id',
        supportsAllDrives=True
    ).execute()
    return file['id']


def create_stream_file(name, file_data):
    folder = tempfile.gettempdir()
    file_path = os.path.join(folder, name)
    with open(file_path, 'wb') as fp:
        fp.write(base64.b64decode(file_data))
    return file_path


def create_file_on_drive(obj, file_metadata, path):
    mimetype = mimetypes.guess_type(file_metadata['name'])[0] or 'application/octet-stream'
    media = MediaFileUpload(path, mimetype=mimetype)

    service = build_drive_service(obj)
    drive_file_obj = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webContentLink, webViewLink',
        supportsAllDrives=True
    ).execute()

    # Public sharing (optional)
    new_permission = {'type': 'anyone', 'role': 'reader'}
    service.permissions().create(
        fileId=drive_file_obj['id'],
        body=new_permission,
        transferOwnership=False,
        supportsAllDrives=True
    ).execute()

    drive_file_obj['download_link'] = drive_file_obj.get('webContentLink', '')
    return drive_file_obj


def delete_file_from_drive(obj, file_id):
    service = build_drive_service(obj)
    service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
