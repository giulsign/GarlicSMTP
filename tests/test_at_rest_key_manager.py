import pytest

from cryptography.exceptions import InvalidTag
from garlicsmtp.security.at_rest_key_manager import AtRestKeyManager
from garlicsmtp.security.at_rest_cipher import AtRestCipher


def test_password_wrap_roundtrip_preserves_dek():
    manager = AtRestKeyManager()
    dek = manager.generate_dek()

    wrapped = manager.wrap_dek(
        dek=dek,
        secret="Garlic1!",
        purpose="password",
    )

    assert len(dek) == 32
    assert wrapped != dek
    assert dek not in wrapped

    assert manager.unwrap_dek(
        wrapped=wrapped,
        secret="Garlic1!",
        purpose="password",
    ) == dek


def test_password_wrap_rejects_wrong_password():
    manager = AtRestKeyManager()
    dek = manager.generate_dek()

    wrapped = manager.wrap_dek(
        dek=dek,
        secret="Garlic1!",
        purpose="password",
    )

    with pytest.raises(InvalidTag):
        manager.unwrap_dek(
            wrapped=wrapped,
            secret="Wrong2!",
        )


def test_recovery_key_is_random_and_distinct():
    manager = AtRestKeyManager()

    first = manager.generate_recovery_key()
    second = manager.generate_recovery_key()

    assert isinstance(first, str)
    assert first != second
    assert len(first) >= 32


def test_same_dek_can_be_unwrapped_with_password_or_recovery():
    manager = AtRestKeyManager()
    dek = manager.generate_dek()
    recovery_key = manager.generate_recovery_key()

    password_wrapped = manager.wrap_dek(
        dek=dek,
        secret="Garlic1!",
        purpose="password",
    )
    recovery_wrapped = manager.wrap_dek(
        dek=dek,
        secret=recovery_key,
        purpose="recovery",
    )

    assert password_wrapped != recovery_wrapped

    assert manager.unwrap_dek(
        wrapped=password_wrapped,
        secret="Garlic1!",
        purpose="password",
    ) == dek

    assert manager.unwrap_dek(
        wrapped=recovery_wrapped,
        secret=recovery_key,
        purpose="recovery",
    ) == dek

    with pytest.raises((ValueError, InvalidTag)):
        manager.unwrap_dek(
            wrapped=recovery_wrapped,
            secret=recovery_key,
            purpose="password",
        )


def test_password_reset_preserves_decryption_of_existing_data():
    manager = AtRestKeyManager()
    dek = manager.generate_dek()
    recovery_key = manager.generate_recovery_key()

    plaintext = b"Message encrypted before password reset"
    encrypted_message = AtRestCipher(dek).encrypt(plaintext)

    recovery_wrapped = manager.wrap_dek(
        dek=dek,
        secret=recovery_key,
        purpose="recovery",
    )

    recovered_dek = manager.unwrap_dek(
        wrapped=recovery_wrapped,
        secret=recovery_key,
        purpose="recovery",
    )

    new_password_wrapped = manager.wrap_dek(
        dek=recovered_dek,
        secret="NewGarlic2!",
        purpose="password",
    )

    unlocked_dek = manager.unwrap_dek(
        wrapped=new_password_wrapped,
        secret="NewGarlic2!",
        purpose="password",
    )

    assert unlocked_dek == dek
    assert AtRestCipher(unlocked_dek).decrypt(encrypted_message) == plaintext


def test_recovery_rotation_invalidates_old_key_for_current_wrapping():
    manager = AtRestKeyManager()
    dek = manager.generate_dek()

    old_recovery_key = manager.generate_recovery_key()
    new_recovery_key = manager.generate_recovery_key()

    current_recovery_wrapped = manager.wrap_dek(
        dek=dek,
        secret=new_recovery_key,
        purpose="recovery",
    )

    with pytest.raises(InvalidTag):
        manager.unwrap_dek(
            wrapped=current_recovery_wrapped,
            secret=old_recovery_key,
            purpose="recovery",
        )

    assert manager.unwrap_dek(
        wrapped=current_recovery_wrapped,
        secret=new_recovery_key,
        purpose="recovery",
    ) == dek