from fastapi import FastAPI, HTTPException, Depends
app = FastAPI()

orders = {
    1 : {
        "order_id" : 1,
        "item":"Laptop",
        "price":1500,
        "status":"shipped"
    },
    2 : {
            "order_id" : 2,
            "item":"Computer",
            "price":2000,
            "status":"shipped"
    },
    3 : {
            "order_id" : 3,
            "item":"PS5",
            "price":2300,
            "status":"shipped"
    }
}

@app.get("/orders/{order_id}")
def getorder(order_id:int):
    if order_id not in orders:
        raise HTTPException(status_code=404 , detail="Order not found")
    return orders[order_id]