import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from alternating_qqq_spy_put_cycle_v1 import base


class FakeResponse:
    def __init__(self, status, headers, actions):
        self.status = status
        self.headers = headers
        self.actions = list(actions)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def getcode(self):
        return self.status

    def read(self, size=-1):
        if not self.actions:
            return b""
        item = self.actions.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item


def git_blob_sha(payload):
    prefix = b"blob " + str(len(payload)).encode("ascii") + bytes([0])
    return hashlib.sha1(prefix + payload).hexdigest()


class ResumableDownloadTests(unittest.TestCase):
    def setUp(self):
        self.payload = b"parquet-pinned-data"
        self.sha = git_blob_sha(self.payload)
        self.temp = tempfile.TemporaryDirectory()
        self.cache = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def configure_pin(self):
        pin_patch = patch.object(base, "PINS", {"QQQ": {2024: (len(self.payload), self.sha)}})
        url_patch = patch.object(base, "SOURCE_BASE", "https://raw.githubusercontent.test/dataset/immutable-commit")
        return pin_patch, url_patch

    def test_source_url_uses_immutable_dataset_commit(self):
        self.assertIn(base.SOURCE_COMMIT, base.SOURCE_BASE)

    def test_timeout_resumes_from_partial_offset_and_hash_verifies(self):
        interrupted = FakeResponse(200, {"ETag": '"pin-v1"'}, [self.payload[:7], TimeoutError("read timeout")])
        resumed = FakeResponse(206, {
            "ETag": '"pin-v1"',
            "Content-Range": f"bytes 7-{len(self.payload)-1}/{len(self.payload)}",
        }, [self.payload[7:]])
        pin_patch, url_patch = self.configure_pin()
        with pin_patch:
            with url_patch:
                with patch.object(base.urllib.request, "urlopen", side_effect=[interrupted, resumed]) as opener:
                    with patch.object(base.time, "sleep") as sleeper:
                        path, meta = base.download_verified("QQQ", 2024, self.cache)

        self.assertEqual(path.read_bytes(), self.payload)
        self.assertEqual(base.git_blob_sha_file(path, len(self.payload)), self.sha)
        self.assertEqual(meta["download_attempts"], 2)
        self.assertEqual(meta["resumed_from_bytes"], 7)
        self.assertEqual(opener.call_count, 2)
        second_request = opener.call_args_list[1].args[0]
        self.assertEqual(second_request.get_header("Range"), "bytes=7-")
        self.assertEqual(second_request.get_header("If-range"), '"pin-v1"')
        sleeper.assert_called_once()

    def test_existing_partial_from_previous_run_resumes(self):
        part = self.cache / "options_2024.parquet.part"
        etag = self.cache / "options_2024.parquet.part.etag"
        part.write_bytes(self.payload[:6])
        etag.write_text('"pin-v1"', encoding="utf-8")
        response = FakeResponse(206, {
            "ETag": '"pin-v1"',
            "Content-Range": f"bytes 6-{len(self.payload)-1}/{len(self.payload)}",
        }, [self.payload[6:]])
        pin_patch, url_patch = self.configure_pin()
        with pin_patch:
            with url_patch:
                with patch.object(base.urllib.request, "urlopen", return_value=response) as opener:
                    path, meta = base.download_verified("QQQ", 2024, self.cache)

        self.assertEqual(path.read_bytes(), self.payload)
        self.assertEqual(meta["resumed_from_bytes"], 6)
        self.assertEqual(opener.call_args.args[0].get_header("Range"), "bytes=6-")

    def test_server_ignoring_range_restarts_without_duplicate_bytes(self):
        interrupted = FakeResponse(200, {"ETag": '"pin-v1"'}, [self.payload[:5], TimeoutError("read timeout")])
        full_restart = FakeResponse(200, {"ETag": '"pin-v1"'}, [self.payload])
        pin_patch, url_patch = self.configure_pin()
        with pin_patch:
            with url_patch:
                with patch.object(base.urllib.request, "urlopen", side_effect=[interrupted, full_restart]):
                    with patch.object(base.time, "sleep"):
                        path, meta = base.download_verified("QQQ", 2024, self.cache)

        self.assertEqual(path.read_bytes(), self.payload)
        self.assertEqual(meta["download_attempts"], 2)
        self.assertEqual(meta["resumed_from_bytes"], 0)

    def test_next_invocation_reuses_a_complete_verified_partial(self):
        part = self.cache / "options_2024.parquet.part"
        part.write_bytes(self.payload)
        pin_patch, url_patch = self.configure_pin()
        with pin_patch:
            with url_patch:
                with patch.object(base.urllib.request, "urlopen") as opener:
                    path, meta = base.download_verified("QQQ", 2024, self.cache)

        self.assertEqual(path.read_bytes(), self.payload)
        self.assertEqual(meta["status"], "RESUMED_HASH_VERIFIED")
        opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
