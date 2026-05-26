# Biometric App

Owns fingerprint template hashes and verification attempt logs.

## Files

- `models.py`: `BiometricTemplate`, `BiometricVerificationLog`
- `serializers.py`: enrollment and verification payload validation
- `views.py`: enroll and verify endpoints
- `admin.py`: admin registration

## Endpoints

| Method | Path | Purpose | Permission |
|---|---|---|---|
| `POST` | `/api/biometric/enroll/` | Register/update a student fingerprint hash | Admin or Officer |
| `POST` | `/api/biometric/verify/` | Match live scan hash to a student | Authenticated staff/officer/admin |

## Enrollment Body

```json
{
  "reg_number": "220229358370",
  "template_hash": "64_hex_character_sha256_hash",
  "finger_used": "right_index",
  "quality_score": 0.94
}
```

## Verification Body

```json
{
  "template_hash": "64_hex_character_sha256_hash",
  "workstation_id": "lab-terminal-01"
}
```

## Important Rules

- Never store raw fingerprint images.
- `template_hash` must be a 64-character hex value.
- A student has only one active `BiometricTemplate`.
- Every verification attempt should create a `BiometricVerificationLog`.
- Unknown fingerprints are logged with `student=null`.

## Common Changes

- If the scanner SDK returns non-SHA256 templates, update serializer validation and document the format.
- If you add real match scores, pass `match_score` from the scanner agent into the verification log.
- If multi-finger enrollment is required, replace the one-to-one student relation with a foreign key and enforce uniqueness per student/finger.
