# 🔌 NETtap API Documentation

Base URL: `https://your-domain.com/api`

## Authentication

```
POST /api/auth/login
Body: {"username": "admin", "password": "pass"}
Response: {"access_token": "...", "token_type": "bearer"}
```

All protected endpoints require: `Authorization: Bearer <token>`

## Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/users/ | List all users |
| POST | /api/users/ | Create user |
| PATCH | /api/users/{id} | Update user |
| DELETE | /api/users/{id} | Delete user |
| POST | /api/users/{id}/block | Block user |
| POST | /api/users/{id}/unblock | Unblock user |
| POST | /api/users/{id}/reset | Reset timer |

## Sellers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/sellers/ | List sellers |
| POST | /api/sellers/ | Add seller |
| DELETE | /api/sellers/{id} | Remove seller |
| POST | /api/sellers/trigger-update | Update all subs |

## Configs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/configs/ | List configs |
| GET | /api/configs/stats | Get statistics |
| POST | /api/configs/{id}/pin | Toggle pin |
| POST | /api/configs/pin-all | Pin all |
| POST | /api/configs/scan-all | Full scan |
| POST | /api/configs/scan-ping | Ping test |
| DELETE | /api/configs/{id} | Delete config |

## Groups

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/groups/ | List groups |
| POST | /api/groups/ | Create group |
| DELETE | /api/groups/{id} | Delete group |
| POST | /api/groups/{id}/assign-configs | Assign configs |

## Plans

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/plans/ | List plans |
| GET | /api/plans/public | Public plans |
| POST | /api/plans/ | Create plan |
| PATCH | /api/plans/{id} | Update plan |
| DELETE | /api/plans/{id} | Delete plan |
| POST | /api/plans/seed-defaults | Seed defaults |

## Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/settings/ | All settings |
| GET | /api/settings/public | Public settings |
| PATCH | /api/settings/{key} | Update setting |
| POST | /api/settings/bulk-update | Bulk update |

## Subscription

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /sub/{token} | Get subscription (auto-detects browser vs VPN client) |
| GET | /sub/{token}?format=raw | Raw config output |