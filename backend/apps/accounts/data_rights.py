"""Export and deletion.

EXPORTED_MODELS is the list every model touching an Account must appear in.
A test enumerates Django's model registry and fails when something references
Account without being listed here, so the export cannot quietly stop being
complete as later phases add conversations, tracking and care artefacts.
"""

EXPORTED_MODELS = (
    "accounts.Account",
    "accounts.Identifier",
    "accounts.Device",
)


def build_export(account) -> dict:
    """Everything held about this account, in plain JSON-serialisable form.

    Password hashes and device token hashes are excluded deliberately: they are
    credentials rather than her data, and handing them over in a file would put
    her account at risk if the file were read by someone else.
    """
    return {
        "account": {
            "id": str(account.id),
            "created_at": account.created_at.isoformat(),
        },
        "identifiers": [
            {
                "kind": identifier.kind,
                "value": identifier.value,
                "verified_at": (
                    identifier.verified_at.isoformat()
                    if identifier.verified_at
                    else None
                ),
            }
            for identifier in account.identifiers.order_by("created_at")
        ],
        "devices": [
            {
                "id": str(device.id),
                "label": device.label,
                "locale": device.locale,
                "created_at": device.created_at.isoformat(),
                "bound_at": device.bound_at.isoformat() if device.bound_at else None,
                "last_seen": device.last_seen.isoformat(),
            }
            for device in account.devices.order_by("created_at")
        ],
    }
