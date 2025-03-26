import os
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, BlobClient, generate_blob_sas, BlobSasPermissions
import re 


def extract_account_key_from_connection_string(connection_string):
    """
    Extract the account key from the Azure Storage connection string.
    
    :param connection_string: Azure Storage account connection string
    :return: Account key
    """
    match = re.search(r'AccountKey=([^;]+)', connection_string)
    if match:
        return match.group(1)
    raise ValueError("Could not extract account key from connection string")


def upload_mp4_to_azure_blob(local_file_path, connection_string, container_name, blob_name=None):
    """
    Upload an MP4 file to Azure Blob Storage.

    :param local_file_path: Full path to the local MP4 file
    :param connection_string: Azure Storage account connection string
    :param container_name: Name of the blob container
    :param blob_name: Optional. Name to use for the blob. If None, uses the original filename.
    :return: URL of the uploaded blob
    """
    try:
        # Create a BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Get a container client
        container_client = blob_service_client.get_container_client(container_name)
        
        # Use the original filename if no blob name is provided
        if blob_name is None:
            blob_name = os.path.basename(local_file_path)
        
        # Create a blob client
        blob_client = container_client.get_blob_client(blob_name)
        
        # Upload the file
        with open(local_file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        # Extract account name and account key from connection string
        account_name = blob_service_client.account_name
        account_key = extract_account_key_from_connection_string(connection_string)

        # Generate SAS token valid for 1 month
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(days=30)
        )

        # Construct SAS URL (both HTTP and HTTPS)
        http_sas_url = f"http://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
        https_sas_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
        
        print(f"Successfully uploaded {local_file_path} to {blob_name}")
        
        return {
            "blob_name": blob_name,
            "original_url": blob_client.url,
            "http_sas_url": http_sas_url,
            "https_sas_url": https_sas_url,
            "sas_token": sas_token
        }
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
