"""Тесты нормализации DATABASE_URL (IPv4 hostaddr для Supabase direct)."""

import socket
import unittest
from unittest.mock import patch

from utils.database_url import normalize_database_url


class TestNormalizeDatabaseUrl(unittest.TestCase):
    def test_normalize_supabase_direct_adds_hostaddr(self) -> None:
        url = (
            "postgresql://postgres:secret@db.abc123.supabase.co:5432/postgres"
            "?sslmode=require"
        )
        fake_infos = [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("203.0.113.10", 0),
            )
        ]
        with patch("utils.database_url.socket.getaddrinfo", return_value=fake_infos):
            out = normalize_database_url(url)
        self.assertIsNotNone(out)
        self.assertIn("hostaddr=203.0.113.10", out)

    def test_normalize_skips_when_hostaddr_present(self) -> None:
        url = "postgresql://u:p@db.abc.supabase.co:5432/postgres?hostaddr=1.2.3.4"
        self.assertEqual(normalize_database_url(url), url)

    def test_normalize_non_supabase_unchanged(self) -> None:
        url = "postgresql://u:p@localhost:5432/db"
        self.assertEqual(normalize_database_url(url), url)

    def test_normalize_none(self) -> None:
        self.assertIsNone(normalize_database_url(None))


if __name__ == "__main__":
    unittest.main()
