from object.storage.client import ClientManager
import traceback
import os

class VideoRepository:
    def __init__(self, bucket: str, client_manager: ClientManager):
        self.bucket = bucket
        self.client_manager = client_manager
        self.path = "video/"

    def upload(self, file_name: str, object_name: str):
        try:
            client = self.client_manager.get_client()
            client.upload_file(file_name, self.bucket, self.path + object_name)
            return object_name
        except Exception as e:
            print(f"Cannot upload file: '{object_name}' to S3.", e)
            return None

    def upload_obj(self, file, object_name: str):
        try:
            client = self.client_manager.get_client()
            client.upload_fileobj(file, self.bucket, self.path + object_name)
            return object_name
        except Exception as e:
            print(f"Cannot upload file: '{object_name}' to S3.", e)
            return None

    def download(self, object_name: str, file_name: str):
        try:
            client = self.client_manager.get_client()

            file_dir = os.path.dirname(file_name)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir, exist_ok=True)

            client.download_file(self.bucket, self.path + object_name, file_name)
            return file_name
        except Exception as e:
            # test
            print(e)
            print(traceback.format_exc())
            
            print(f"Cannot download file: '{object_name}' from S3.")
            return None

    def get_object(self, object_name: str):
        try:
            client = self.client_manager.get_client()
            return client.get_object(Bucket=self.bucket, Key=self.path + object_name)
        except Exception as e:
            print(f"Cannot download file: '{object_name}' from S3.")
            return None

    def delete(self, object_name: str):
        try:
            client = self.client_manager.get_client()
            client.delete_object(Bucket=self.bucket, Key=self.path + object_name)
            return object_name
        except Exception as e:
            print(f"Cannot delete file: '{object_name}' from S3.")
            return None

    def get_object_list(self):
        try:
            client = self.client_manager.get_client()
            return client.list_objects_v2(Bucket=self.bucket, Prefix=self.path[:-1])
        except Exception as e:
            print(f"Cannot get object list in '{self.path}' from S3.")
            return None
        
    def get_presigned_url(self, file_path: str):
        try:
            client = self.client_manager.get_client()
            response = client.generate_presigned_url(
                'put_object',
                Params = {
                    'Bucket': self.bucket,
                    'Key': file_path,
                    'ContentType': 'video/mp4'
                },
                ExpiresIn = 3600
            )
            return response

        except Exception as e:
            print(f"Cannot get pre-sigend url to upload {file_path}")
            return None