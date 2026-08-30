from __future__ import annotations

import hashlib
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)


OPERATOR_USER_ID = hashlib.sha256(b"hdp-v6-single-operator").digest()
SESSION_DURATION = timedelta(hours=12)
CHALLENGE_DURATION = timedelta(minutes=5)


def opaque_token() -> str:
    return secrets.token_urlsafe(48)


def token_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def registration_options(
    rp_id: str,
    credential_ids: list[bytes],
) -> tuple[bytes, dict[str, Any]]:
    options = generate_registration_options(
        rp_id=rp_id,
        rp_name="Humanitarian Data Platform",
        user_name="operateur-hdp",
        user_id=OPERATOR_USER_ID,
        user_display_name="Opérateur HDP",
        timeout=300_000,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED,
            require_resident_key=True,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=[PublicKeyCredentialDescriptor(id=value) for value in credential_ids],
    )
    return options.challenge, json.loads(options_to_json(options))


def authentication_options(rp_id: str, credential_ids: list[bytes]) -> tuple[bytes, dict[str, Any]]:
    options = generate_authentication_options(
        rp_id=rp_id,
        timeout=300_000,
        allow_credentials=[PublicKeyCredentialDescriptor(id=value) for value in credential_ids],
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    return options.challenge, json.loads(options_to_json(options))


def verify_registration(
    credential: dict[str, Any],
    challenge: bytes,
    rp_id: str,
    origin: str,
) -> Any:
    return verify_registration_response(
        credential=credential,
        expected_challenge=challenge,
        expected_rp_id=rp_id,
        expected_origin=origin,
        require_user_verification=True,
    )


def verify_authentication(
    credential: dict[str, Any],
    challenge: bytes,
    rp_id: str,
    origin: str,
    public_key: bytes,
    sign_count: int,
) -> Any:
    return verify_authentication_response(
        credential=credential,
        expected_challenge=challenge,
        expected_rp_id=rp_id,
        expected_origin=origin,
        credential_public_key=public_key,
        credential_current_sign_count=sign_count,
        require_user_verification=True,
    )


def credential_id_from_json(credential: dict[str, Any]) -> bytes:
    value = credential.get("rawId") or credential.get("id")
    if not isinstance(value, str) or not value:
        raise ValueError("Identifiant de credential absent")
    return base64url_to_bytes(value)


def expires_at(duration: timedelta, now: datetime | None = None) -> datetime:
    moment = now or datetime.now(UTC)
    return moment + duration
