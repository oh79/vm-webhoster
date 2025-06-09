# API Overview

This document summarizes the main API endpoints of the web hosting service.

## Authentication

### Register
- **Endpoint**: `POST /api/v1/auth/register`
- **Description**: Create a new user account.
- **Body Example**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "username": "myuser"
}
```

### Login
- **Endpoint**: `POST /api/v1/auth/login`
- **Description**: Obtain a JWT token.
- **Form Fields**: `username` (email) and `password`.

## Hosting Management

### Create Hosting
- **Endpoint**: `POST /api/v1/hosting`
- **Description**: Create a VM for the authenticated user.
- **Auth**: Bearer token required.

### Get My Hosting
- **Endpoint**: `GET /api/v1/hosting/my`
- **Description**: Retrieve the current user hosting details.
- **Auth**: Bearer token required.

### Delete My Hosting
- **Endpoint**: `DELETE /api/v1/hosting/my`
- **Description**: Remove the current user hosting and delete the VM.
- **Auth**: Bearer token required.

## Health Check

### Basic Health Check
- **Endpoint**: `GET /health`
- **Description**: Returns `{"status": "healthy"}` if the service is running.

### Detailed Health Check
- **Endpoint**: `GET /health/detailed`
- **Description**: Includes database status and environment information.

