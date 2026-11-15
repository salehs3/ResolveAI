import requests
from openai import OpenAI
from dotenv import  load_dotenv


def get_order(order_id: int):
    request = requests.get(f"http://127.0.0.1:8001/orders/{order_id}", timeout=5)

    request.raise_for_status()
    return(request.json())

def get_shipping(order_id: int):
    request = requests.get(f"http://127.0.0.1:8002/shipments/{order_id}",timeout=5)
    request.raise_for_status()
    return(request.json())

tools = [
    {
        "type":"function",
        "name":"get_order",
        "description": "Get Order Details",
         "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type":"integer",
                    "description": "The unique ID of the order"
                }
                },
            "required": ["order_id"],
            "additionalProperties": False
        },
        "strict": True
    },
     {
            "type":"function",
            "name":"get_shipping",
            "description": "Get Shipping Details",
             "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type":"integer",
                        "description": "The unique ID of the order"
                    }
                    },
                "required": ["order_id"],
                "additionalProperties": False
            },
            "strict": True
        }
]



if __name__ == "__main__":
    print(get_order(1))
    print(get_shipping(1))