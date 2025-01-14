import unittest
from unittest.mock import MagicMock, patch
from boto3 import client
from object.storage.client import ClientManager
from object.repository.video import VideoRepository


class TestVideoRepository(unittest.TestCase):

    def setUp(self):
        self.client_manager = MagicMock(spec=ClientManager)
        self.video_repo = VideoRepository("bucket", self.client_manager)

    def test_upload(self):
        file_name = "file_name"
        object_name = "object_name"
        s3_client = MagicMock(spec=client("s3"))
        self.client_manager.get_client.return_value = s3_client
        result = self.video_repo.upload(file_name, object_name)
        s3_client.upload_file.assert_called_once_with(
            file_name, "bucket", "video/object_name"
        )
        self.assertEqual(result, object_name)

    def test_upload_exception(self):
        file_name = "file_name"
        object_name = "object_name"
        s3_client = MagicMock(spec=client("s3"))
        s3_client.upload_file.side_effect = Exception
        self.client_manager.get_client.return_value = s3_client
        result = self.video_repo.upload(file_name, object_name)
        s3_client.upload_file.assert_called_once_with(
            file_name, "bucket", "video/object_name"
        )
        self.assertIsNone(result)

    def test_download(self):
        object_name = "object_name"
        file_name = "file_name"
        s3_client = MagicMock(spec=client("s3"))
        self.client_manager.get_client.return_value = s3_client
        with patch("os.path.dirname", return_value="dir_name"), patch(
            "os.path.exists", return_value=False
        ), patch("os.makedirs") as mock_makedirs:

            result = self.video_repo.download(object_name, file_name)

            s3_client.download_file.assert_called_once_with(
                "bucket", "video/object_name", file_name
            )
            self.assertEqual(result, file_name)
            mock_makedirs.assert_called_once_with("dir_name", exist_ok=True)

    def test_download_exception(self):
        object_name = "object_name"
        file_name = "file_name"
        s3_client = MagicMock(spec=client("s3"))
        s3_client.download_file.side_effect = Exception
        self.client_manager.get_client.return_value = s3_client

        with patch("os.path.dirname", return_value="dir_name"), patch(
            "os.path.exists", return_value=False
        ), patch("os.makedirs") as mock_makedirs:

            result = self.video_repo.download(object_name, file_name)

            s3_client.download_file.assert_called_once_with(
                "bucket", "video/object_name", file_name
            )
            mock_makedirs.assert_called_once_with("dir_name", exist_ok=True)
            self.assertIsNone(result)

    def test_delete(self):
        object_name = "object_name"
        s3_client = MagicMock(spec=client("s3"))
        self.client_manager.get_client.return_value = s3_client
        result = self.video_repo.delete(object_name)
        s3_client.delete_object.assert_called_once_with(
            Bucket="bucket", Key="video/object_name"
        )
        self.assertEqual(result, object_name)

    def test_delete_exception(self):
        object_name = "object_name"
        s3_client = MagicMock(spec=client("s3"))
        s3_client.delete_object.side_effect = Exception
        self.client_manager.get_client.return_value = s3_client
        result = self.video_repo.delete(object_name)
        s3_client.delete_object.assert_called_once_with(
            Bucket="bucket", Key="video/object_name"
        )
        self.assertIsNone(result)

    def test_get_object_list(self):
        s3_client = MagicMock(spec=client("s3"))
        self.client_manager.get_client.return_value = s3_client
        s3_client.list_objects_v2.return_value = {"Contents": [{"Key": "video/1"}]}
        result = self.video_repo.get_object_list()
        self.assertEqual(result, {"Contents": [{"Key": "video/1"}]})

    def test_get_object_list_exception(self):
        s3_client = MagicMock(spec=client("s3"))
        s3_client.list_objects_v2.side_effect = Exception
        self.client_manager.get_client.return_value = s3_client
        result = self.video_repo.get_object_list()
        self.assertIsNone(result)
