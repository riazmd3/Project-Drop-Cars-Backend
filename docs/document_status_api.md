# Document Status API Documentation

## Overview

The Document Status API provides functionality to track and manage the verification status of documents uploaded to Google Cloud Storage (GCS). This system allows users to check document statuses and update documents when they are marked as invalid.

## Document Status Enum

```python
class DocumentStatusEnum(enum.Enum):
    PENDING = "Pending"
    VERIFIED = "Verified"
    INVALID = "Invalid"
```

## Database Schema Changes

### New Columns Added

#### Car Details Table
- `rc_front_status` - Status of RC front image
- `rc_back_status` - Status of RC back image  
- `insurance_status` - Status of insurance document
- `fc_status` - Status of FC document
- `car_img_status` - Status of car image

#### Car Driver Table
- `licence_front_status` - Status of license front image

#### Vendor Details Table
- `aadhar_status` - Status of Aadhar document

#### Vehicle Owner Details Table
- `aadhar_status` - Status of Aadhar document

## API Endpoints

### 1. Get Document Status

#### Vendor Document Status
```
GET /api/users/vendor/document-status
```

**Response:**
```json
{
  "entity_id": "uuid",
  "entity_type": "vendor",
  "documents": {
    "aadhar": {
      "document_type": "aadhar",
      "status": "Pending",
      "image_url": "https://storage.googleapis.com/...",
      "updated_at": null
    }
  }
}
```

#### Vehicle Owner Document Status
```
GET /api/users/vehicle-owner/document-status
```

#### Driver Document Status
```
GET /api/users/cardriver/document-status
```

#### Car Document Status
```
GET /api/users/cardetails/{car_id}/document-status
```

### 2. Update Document Status (Admin Only)

#### Update Vendor Document Status
```
PATCH /api/users/vendor/document-status
```

**Request Body:**
```json
{
  "status": "Verified"
}
```

#### Update Vehicle Owner Document Status
```
PATCH /api/users/vehicle-owner/document-status
```

#### Update Driver Document Status
```
PATCH /api/users/cardriver/document-status
```

#### Update Car Document Status
```
PATCH /api/users/cardetails/{car_id}/document-status?document_type=rc_front
```

### 3. Update Document (Upload New Image)

#### Update Vendor Document
```
POST /api/users/vendor/update-document
```

**Form Data:**
- `document_type`: "aadhar"
- `aadhar_image`: File upload

#### Update Vehicle Owner Document
```
POST /api/users/vehicle-owner/update-document
```

**Form Data:**
- `document_type`: "aadhar"
- `aadhar_image`: File upload

#### Update Driver Document
```
POST /api/users/cardriver/update-document
```

**Form Data:**
- `document_type`: "licence"
- `licence_image`: File upload

#### Update Car Document
```
POST /api/users/cardetails/{car_id}/update-document
```

**Form Data:**
- `document_type`: "rc_front" | "rc_back" | "insurance" | "fc" | "car_img"
- `image`: File upload

## Response Models

### DocumentStatusResponse
```json
{
  "document_type": "string",
  "status": "string",
  "image_url": "string",
  "updated_at": "string"
}
```

### DocumentStatusListResponse
```json
{
  "entity_id": "uuid",
  "entity_type": "string",
  "documents": {
    "document_key": DocumentStatusResponse
  }
}
```

### DocumentUpdateResponse
```json
{
  "message": "string",
  "document_type": "string",
  "new_image_url": "string",
  "new_status": "string"
}
```

## Workflow

1. **Document Upload**: When a document is uploaded, its status is automatically set to "Pending"
2. **Admin Review**: Administrators can review documents and update status to "Verified" or "Invalid"
3. **User Notification**: Users can check document status via GET endpoints
4. **Document Update**: If status is "Invalid", users can upload a new document via POST endpoints
5. **Status Reset**: When a new document is uploaded, status is automatically reset to "Pending"

## Error Handling

- **400 Bad Request**: Invalid document type, file format, or file size
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Access denied (trying to access other user's documents)
- **404 Not Found**: Document or entity not found
- **500 Internal Server Error**: Server error during document processing

## File Validation

- **File Type**: Only image files (JPEG, PNG, etc.) are accepted
- **File Size**: Maximum 5MB per file
- **Content Type**: Must start with "image/"

## Authentication

All endpoints require proper authentication:
- Vendor endpoints require vendor authentication
- Vehicle Owner endpoints require vehicle owner authentication
- Driver endpoints require driver authentication
- Car endpoints require vehicle owner authentication (car must belong to authenticated user)

## Migration

Run the SQL migration file to add the new columns and enum type:

```sql
-- Run migration_add_document_status_columns.sql
```

This will:
1. Create the `document_status_enum` type
2. Add status columns to all relevant tables
3. Set existing documents to "Pending" status
