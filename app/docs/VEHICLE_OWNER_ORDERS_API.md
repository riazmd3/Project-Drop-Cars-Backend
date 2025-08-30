# Vehicle Owner Orders API Documentation

## Overview
This document describes the APIs for vehicle owners to manage order assignments, view pending orders, and get available resources (drivers and cars).

## Base URLs
- Pending Orders: `/api/orders/vehicle_owner/pending`
- Order Assignments: `/api/assignments/`
- Available Resources: `/api/assignments/available-drivers` and `/api/assignments/available-cars`

## Authentication
All endpoints require Bearer token authentication with vehicle owner credentials. The vehicle_owner_id is automatically extracted from the JWT token.

---

## 1. Get Pending Orders

### Endpoint
```
GET /api/orders/vehicle_owner/pending
```

### Description
Retrieves pending orders for the authenticated vehicle owner based on business rules:
1. Orders that are not in the assignment table (never assigned)
2. Orders that have been cancelled in the assignment table (available for reassignment)

### Authentication
- Requires Bearer token
- vehicle_owner_id is automatically extracted from the JWT token

### Response
```json
[
  {
    "id": null, // null for unassigned orders, assignment_id for cancelled orders
    "order_id": 123,
    "vehicle_owner_id": "550e8400-e29b-41d4-a716-446655440000",
    "driver_id": null,
    "car_id": null,
    "assignment_status": "PENDING",
    "assigned_at": null,
    "expires_at": null,
    "cancelled_at": null,
    "completed_at": null,
    "created_at": "2024-01-15T10:30:00Z",
    "vendor_id": "550e8400-e29b-41d4-a716-446655440001",
    "trip_type": "Oneway",
    "car_type": "Sedan",
    "pickup_drop_location": {
      "pickup": "Location A",
      "drop": "Location B"
    },
    "start_date_time": "2024-01-16T09:00:00Z",
    "customer_name": "John Doe",
    "customer_number": "+1234567890",
    "cost_per_km": 15,
    "extra_cost_per_km": 20,
    "driver_allowance": 500,
    "extra_driver_allowance": 750,
    "permit_charges": 100,
    "extra_permit_charges": 150,
    "hill_charges": 200,
    "toll_charges": 300,
    "pickup_notes": "Near main gate",
    "trip_status": "pending",
    "pick_near_city": "Mumbai",
    "trip_distance": 120,
    "trip_time": "3 hours",
    "platform_fees_percent": 10,
    "estimated_price": 2000,
    "vendor_price": 1800,
    "order_created_at": "2024-01-15T10:30:00Z"
  }
]
```

### Error Responses
- `401 Unauthorized`: Invalid or missing authentication token

---

## 2. Accept Order (Updated with Duplicate Prevention)

### Endpoint
```
POST /api/assignments/acceptorder
```

### Description
Accepts an order and creates an assignment. Updated with duplicate prevention logic to prevent creating multiple active assignments for the same order.

### Request Body
```json
{
  "order_id": 123
}
```

### Business Rules
- Cannot create a new assignment if the order already has an active assignment (status != CANCELLED)
- Can create a new assignment if:
  - Order has never been assigned
  - Order's previous assignment was cancelled

### Response
```json
{
  "id": 456,
  "order_id": 123,
  "vehicle_owner_id": "550e8400-e29b-41d4-a716-446655440000",
  "driver_id": null,
  "car_id": null,
  "assignment_status": "PENDING",
  "assigned_at": null,
  "expires_at": "2024-01-15T11:30:00Z",
  "cancelled_at": null,
  "completed_at": null,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Error Responses
- `400 Bad Request`: Order already has an active assignment
- `401 Unauthorized`: Invalid authentication

---

## 3. Get Available Drivers

### Endpoint
```
GET /api/assignments/available-drivers
```

### Description
Retrieves all drivers with "ONLINE" status for the authenticated vehicle owner.

### Authentication
- Requires Bearer token
- vehicle_owner_id is automatically extracted from the JWT token

### Response
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "vehicle_owner_id": "550e8400-e29b-41d4-a716-446655440000",
    "organization_id": "org_123",
    "full_name": "Driver Name",
    "primary_number": "+1234567890",
    "secondary_number": "+1234567891",
    "licence_number": "DL123456789",
    "licence_front_img": "https://storage.googleapis.com/bucket/license_front.jpg",
    "address": "Driver Address",
    "driver_status": "ONLINE",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### Error Responses
- `401 Unauthorized`: Invalid authentication

---

## 4. Get Available Cars

### Endpoint
```
GET /api/assignments/available-cars
```

### Description
Retrieves all cars with "ONLINE" status for the authenticated vehicle owner.

### Authentication
- Requires Bearer token
- vehicle_owner_id is automatically extracted from the JWT token

### Response
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "vehicle_owner_id": "550e8400-e29b-41d4-a716-446655440000",
    "organization_id": "org_123",
    "car_name": "Toyota Camry",
    "car_type": "SEDAN",
    "car_number": "MH01AB1234",
    "rc_front_img_url": "https://storage.googleapis.com/bucket/rc_front.jpg",
    "rc_back_img_url": "https://storage.googleapis.com/bucket/rc_back.jpg",
    "insurance_img_url": "https://storage.googleapis.com/bucket/insurance.jpg",
    "fc_img_url": "https://storage.googleapis.com/bucket/fc.jpg",
    "car_img_url": "https://storage.googleapis.com/bucket/car.jpg",
    "car_status": "ONLINE",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### Error Responses
- `401 Unauthorized`: Invalid authentication

---

## Status Enums

### Assignment Status
- `PENDING`: Assignment created but not yet confirmed
- `ASSIGNED`: Assignment confirmed with driver/car
- `CANCELLED`: Assignment cancelled
- `COMPLETED`: Assignment completed
- `DRIVING`: Currently in progress

### Driver Status
- `ONLINE`: Available for assignments
- `DRIVING`: Currently busy with an assignment
- `BLOCKED`: Not available for assignments

### Car Status
- `ONLINE`: Available for assignments
- `DRIVING`: Currently busy with an assignment
- `BLOCKED`: Not available for assignments

---

## Business Logic Summary

### Pending Orders Logic
1. **Rule 1**: Orders not in assignment table are shown as pending
2. **Rule 2**: Orders with cancelled assignments are shown as pending (available for reassignment)
3. Orders with active assignments (PENDING, ASSIGNED, COMPLETED, DRIVING) are NOT shown as pending

### Duplicate Prevention Logic
1. Before creating a new assignment, check if order already has an active assignment
2. Active assignments are those with status != CANCELLED
3. If active assignment exists, throw error
4. If no active assignment or only cancelled assignments exist, allow new assignment creation

### Resource Availability
1. **Available Drivers**: Only drivers with status = "ONLINE"
2. **Available Cars**: Only cars with status = "ONLINE"
3. Resources with "DRIVING" or "BLOCKED" status are not returned

### Authentication & Authorization
1. All endpoints use Bearer token authentication
2. vehicle_owner_id is automatically extracted from the JWT token
3. No need to pass vehicle_owner_id in the request path
4. Users can only access their own data

---

## Usage Examples

### Get Pending Orders
```bash
curl -X GET \
  "https://api.example.com/api/orders/vehicle_owner/pending" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Accept Order
```bash
curl -X POST \
  "https://api.example.com/api/assignments/acceptorder" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"order_id": 123}'
```

### Get Available Drivers
```bash
curl -X GET \
  "https://api.example.com/api/assignments/available-drivers" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Available Cars
```bash
curl -X GET \
  "https://api.example.com/api/assignments/available-cars" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Security Notes

- All endpoints require valid JWT Bearer token
- vehicle_owner_id is automatically extracted from the token's subject claim
- No manual vehicle_owner_id parameter required
- Users can only access their own data
- Token expiration and validation are handled automatically
