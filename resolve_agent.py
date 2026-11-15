from openai import OpenAI
from dotenv import  load_dotenv
from agent_tools import get_order, get_shipping, tools
import json
import requests

load_dotenv()
client = OpenAI()

def ask_resolveai(question: str):
    inputmsg = [
        {
            "role":"user",
            "content":question
        }
    ]


    for i in range(5):
        response = client.responses.create(
            model = "gpt-4o-mini",
            input = inputmsg,
            instructions=(
                "You are a customer support assistant. "
                "Use tools to retrieve order and shipping details. "
                "Never invent order statuses, tracking information, or delivery dates."
                ),
            tools= tools
        )
        inputmsg.extend(response.output)

        made_call = False

        # The model may return several items (e.g. two function calls) in one response
        for rout in response.output:
            if rout.type != "function_call":
                continue

            made_call = True
            try:
                args = json.loads(rout.arguments)
                order_id = args["order_id"]

                if rout.name == "get_order":
                    tool_results = get_order(order_id)
                elif rout.name == "get_shipping":
                    tool_results = get_shipping(order_id)
                else:
                    tool_results = {"error": f"Unknown function: {rout.name}"}
            except (json.JSONDecodeError, KeyError):
                tool_results = {"error": "Invalid tool arguments"}
            except requests.HTTPError as e:
                status = e.response.status_code
                if status == 404:
                    tool_results = {"error": "Order or shipment not found", "status_code": 404}
                else:
                    tool_results = {"error": "External service returned an error", "status_code": 502}
            except requests.Timeout:
                tool_results = {"error": "External service unavailable", "status_code": 504}
            except requests.ConnectionError:
                tool_results = {"error": "External service timed out", "status_code": 503}
            
            inputmsg.append({
                "type":"function_call_output",
                "call_id":rout.call_id,
                "output":json.dumps(tool_results)
            })
        if not made_call:
            return response.output_text

    return "Unable to complete the request within the tool-call limit."


if __name__ == "__main__":
      
    print(ask_resolveai("What is the status of order 1?"))

