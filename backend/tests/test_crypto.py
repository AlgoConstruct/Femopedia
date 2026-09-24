import pytest
from django.test import override_settings

from apps.accounts import crypto


def test_blind_index_is_stable_and_64_hex_chars():
    digest = crypto.blind_index("her@example.com")
    assert digest == crypto.blind_index("her@example.com")
    assert len(digest) == 64
    assert digest == digest.lower()
    int(digest, 16)  # raises if not hex


def test_blind_index_normalises_case_and_surrounding_whitespace():
    assert crypto.blind_index("  HER@Example.COM ") == crypto.blind_index("her@example.com")


def test_blind_index_differs_for_different_values():
    assert crypto.blind_index("a@example.com") != crypto.blind_index("b@example.com")


def test_blind_index_depends_on_the_pepper():
    baseline = crypto.blind_index("her@example.com")
    with override_settings(IDENTIFIER_PEPPER="a-different-pepper"):
        assert crypto.blind_index("her@example.com") != baseline


def test_encrypt_round_trips_and_hides_the_plaintext():
    ciphertext = crypto.encrypt("her@example.com")
    assert "her@example.com" not in ciphertext
    assert crypto.decrypt(ciphertext) == "her@example.com"


def test_encrypting_twice_gives_different_ciphertext():
    # Fernet includes a random IV, so identical plaintexts must not produce
    # identical ciphertexts — otherwise the column leaks which rows match.
    assert crypto.encrypt("her@example.com") != crypto.encrypt("her@example.com")


def test_decrypt_rejects_a_tampered_token():
    from cryptography.fernet import InvalidToken

    ciphertext = crypto.encrypt("her@example.com")
    tampered = ciphertext[:-2] + ("AA" if not ciphertext.endswith("AA") else "BB")
    with pytest.raises(InvalidToken):
        crypto.decrypt(tampered)
