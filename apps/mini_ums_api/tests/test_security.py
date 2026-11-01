from mini_ums_api.security import hash_password, new_session_token, token_hash, verify_password


def test_hash_and_verify() -> None:
    stored = hash_password("Demo@1234")
    assert stored.startswith("scrypt$")
    assert verify_password("Demo@1234", stored)
    assert not verify_password("demo@1234", stored)
    assert not verify_password("", stored)


def test_salts_differ_unless_given() -> None:
    assert hash_password("x") != hash_password("x")
    assert hash_password("x", salt=b"0" * 16) == hash_password("x", salt=b"0" * 16)


def test_malformed_hashes_never_verify() -> None:
    for stored in ["", "plain", "md5$abc", "scrypt$1$2", "scrypt$x$y$z$salt$hash"]:
        assert not verify_password("anything", stored)


def test_tokens_are_random_and_only_hashes_are_stored() -> None:
    a, b = new_session_token(), new_session_token()
    assert a != b and len(a) >= 40
    assert token_hash(a) != a and len(token_hash(a)) == 64
