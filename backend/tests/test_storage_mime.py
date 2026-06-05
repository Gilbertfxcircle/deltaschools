"""File MIME-consistency validation tests (section 10)."""

import unittest

from app.services.storage import is_mime_consistent


class TestMimeConsistency(unittest.TestCase):
    def test_matching_types(self):
        self.assertTrue(is_mime_consistent("report.pdf", "application/pdf"))
        self.assertTrue(is_mime_consistent("photo.PNG", "image/png"))
        self.assertTrue(is_mime_consistent("scan.jpeg", "image/jpeg"))

    def test_mismatch_rejected(self):
        self.assertFalse(is_mime_consistent("malware.pdf", "image/png"))
        self.assertFalse(is_mime_consistent("fake.png", "application/x-msdownload"))

    def test_unknown_extension_allowed(self):
        self.assertTrue(is_mime_consistent("archive.xyz", "application/octet-stream"))


if __name__ == "__main__":
    unittest.main()
