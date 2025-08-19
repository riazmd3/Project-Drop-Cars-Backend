## New Orders (Oneway) API

### Setup
- Set environment variable: `GOOGLE_MAPS_API_KEY` (required for distance lookups)
- Confirm routes are mounted under `/api/orders`

### 1) Create Oneway Quote (No DB Write)
- Method: POST
- URL: `/api/orders/oneway/quote`
- Auth: Not required

Request body:
```json
{
  "vendor_id": "83a93a3f-2f6e-4bf6-9f78-1c3f9f42b7b1",
  "trip_type": "Oneway",
  "car_type": "Sedan",
  "pickup_drop_location": {
    "0": "Chennai",
    "1": "Bangalore"
  },
  "start_date_time": "2025-08-13T12:00:00Z",
  "customer_name": "Arun",
  "customer_number": "+919876543210",
  "cost_per_km": 12,
  "extra_cost_per_km": 0,
  "driver_allowance": 300,
  "extra_driver_allowance": 0,
  "permit_charges": 0,
  "hill_charges": 0,
  "toll_charges": 150,
  "pickup_notes": "Handle with care"
}
```

Notes:
- `pickup_drop_location` is an object mapping indices to location names. Index 0 is the source, highest index is the destination.
- Distance is computed via Google Distance Matrix API between the source and destination.

Example curl:
```bash
curl -X POST 'http://localhost:8000/api/orders/oneway/quote' \
  -H 'Content-Type: application/json' \
  -d '{
        "vendor_id": "83a93a3f-2f6e-4bf6-9f78-1c3f9f42b7b1",
        "trip_type": "Oneway",
        "car_type": "Sedan",
        "pickup_drop_location": {"0": "Chennai", "1": "Bangalore"},
        "start_date_time": "2025-08-13T12:00:00Z",
        "customer_name": "Arun",
        "customer_number": "+919876543210",
        "cost_per_km": 12,
        "extra_cost_per_km": 0,
        "driver_allowance": 300,
        "extra_driver_allowance": 0,
        "permit_charges": 0,
        "hill_charges": 0,
        "toll_charges": 150,
        "pickup_notes": "Handle with care"
      }'
```

Response body:
```json
{
  "fare": {
    "total_km": 70,
    "base_km_amount": 840,
    "driver_allowance": 300,
    "extra_driver_allowance": 0,
    "permit_charges": 0,
    "hill_charges": 0,
    "toll_charges": 150,
    "total_amount": 1290
  },
  "echo": { "...request fields..." }
}
```

### 2) Confirm Oneway Order (DB Write)
- Method: POST
- URL: `/api/orders/oneway/confirm`
- Auth: Bearer token (Vendor). Uses the authenticated vendor's `id` as `vendor_id`.
Example curl:
```bash
curl -X POST 'http://localhost:8000/api/orders/oneway/confirm' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
        "vendor_id": "83a93a3f-2f6e-4bf6-9f78-1c3f9f42b7b1",
        "trip_type": "Oneway",
        "car_type": "Sedan",
        "pickup_drop_location": {"0": "Chennai", "1": "Bangalore"},
        "start_date_time": "2025-08-13T12:00:00Z",
        "customer_name": "Arun",
        "customer_number": "+919876543210",
        "cost_per_km": 12,
        "extra_cost_per_km": 0,
        "driver_allowance": 300,
        "extra_driver_allowance": 0,
        "permit_charges": 0,
        "hill_charges": 0,
        "toll_charges": 150,
        "pickup_notes": "Handle with care",
        "send_to": "NEAR_CITY",
        "near_city": "Chennai"
      }'
```


Additional fields in request:
- `send_to`: `ALL` or `NEAR_CITY`
- `near_city`: required when `send_to` is `NEAR_CITY`; stored as `pick_near_city` in DB; otherwise stored as `ALL`.

Response body:
```json
{
  "order_id": 123,
  "trip_status": "CONFIRMED",
  "pick_near_city": "ALL",
  "fare": {
    "total_km": 70,
    "base_km_amount": 840,
    "driver_allowance": 300,
    "extra_driver_allowance": 0,
    "permit_charges": 0,
    "hill_charges": 0,
    "toll_charges": 150,
    "total_amount": 1290
  }
}
```

### Model Fields Stored
- vendor_id, trip_type, car_type, pickup_drop_location, start_date_time, customer_name, customer_number, cost_per_km, extra_cost_per_km, driver_allowance, extra_driver_allowance, permit_charges, hill_charges, toll_charges, pickup_notes, trip_status (set to `CONFIRMED`), pick_near_city.

### Error Cases
- 422 when `near_city` missing while `send_to`=`NEAR_CITY`
- 400 for invalid fare calculation input


