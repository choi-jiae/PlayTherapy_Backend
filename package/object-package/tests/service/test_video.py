import unittest
from unittest.mock import patch, MagicMock
from object.repository.video import VideoRepository
from object.service.video import VideoService
from moviepy.editor import VideoFileClip
import os


class TestVideoService(unittest.TestCase):

    def setUp(self):
        self.video_repo = MagicMock(spec=VideoRepository)
        self.video_service = VideoService(self.video_repo)
    
    def test_encode_video(self, video_file, encoded_path):
        self.video_service.encode_video(video_file, encoded_path)

    @patch("object.service.video.VideoFileClip")
    def test_download_and_encode_video(self, mock_video_clip):
        object_name = "object_name"
        file_name = "file_name"
        encoded_path = "encoded_path"
        self.video_repo.download.return_value = file_name

        mock_clip = MagicMock(spec=VideoFileClip)
        mock_video_clip.return_value = mock_clip

        with patch("os.path.dirname", return_value="dir_name"), patch(
            "os.path.exists", return_value=False
        ), patch("os.makedirs") as mock_makedirs:

            result = self.video_service.download_and_encode_video(
                object_name, file_name, encoded_path
            )

            self.video_repo.download.assert_called_once_with(object_name, file_name)
            mock_makedirs.assert_called_once_with("dir_name", exist_ok=True)
            mock_clip.write_videofile.assert_called_once_with(
                encoded_path,
                fps=24,
                threads=os.cpu_count() - 1,
                codec="libx264",
                bitrate="96k",
                audio_codec="aac",
                logger=None,
                audio_bitrate="72k",
                preset="ultrafast",
            )
            self.assertEqual(result, encoded_path)

    @patch("object.service.video.VideoFileClip")
    def test_download_and_encode_video_exception(self, mock_video_clip):
        object_name = "object_name"
        file_name = "file_name"
        encoded_path = "encoded_path"
        self.video_repo.download.return_value = file_name

        mock_clip = MagicMock(spec=VideoFileClip)
        mock_video_clip.return_value = mock_clip
        mock_clip.write_videofile.side_effect = Exception

        with patch("os.path.dirname", return_value="dir_name"), patch(
            "os.path.exists", return_value=False
        ), patch("os.makedirs") as mock_makedirs:

            result = self.video_service.download_and_encode_video(
                object_name, file_name, encoded_path
            )

            self.video_repo.download.assert_called_once_with(object_name, file_name)
            mock_makedirs.assert_called_once_with("dir_name", exist_ok=True)
            mock_clip.write_videofile.assert_called_once_with(
                encoded_path,
                fps=24,
                threads=os.cpu_count() - 1,
                codec="libx264",
                bitrate="96k",
                audio_codec="aac",
                logger=None,
                audio_bitrate="72k",
                preset="ultrafast",
            )
            self.assertIsNone(result)
