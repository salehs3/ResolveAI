from fastapi import FastAPI,HTTPException
app = FastAPI()

shipments = {
    1 : {
        "order_id" : 1,
        "tracking_id":"TK1234",
        "carrier":"FedEx",
        "shipping_status":"in transit",
        "estimated_delivery":"2026-11-06"
    },
    2 : {
            "order_id" : 2,
            "tracking_id":"TK34567",
            "carrier":"UPS",
            "shipping_status":"in transit",
            "estimated_delivery":"2026-12-05"
    },
    3 : {
            "order_id" : 3,
            "tracking_id":"TK0183",
            "carrier":"USPS",
            "shipping_status":"in transit",
            "estimated_delivery":"2026-12-13"
    }
}

@app.get("/shipments/{order_id}")
def get_shipment(order_id:int):
    if order_id not in shipments:
        raise HTTPException(status_code=404,detail="Shipment not found")
    return shipments[order_id]