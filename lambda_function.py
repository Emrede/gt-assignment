import boto3
import csv
import json
from io import StringIO
from decimal import Decimal

s3 = boto3.client("s3")
sqs = boto3.client("sqs")

def lambda_handler(event, context):
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]

    data = load_s3_data(bucket, key)
    messages = process_data(data)

    for message in messages:
        send_message(message)

def load_s3_data(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    content = obj["Body"].read().decode("utf-8")
    return content

def process_data(data):
    messages = []

    customers, orders, items = parse_csv_data(data)
    messages.extend(generate_customer_messages(customers, orders, items))
    messages.extend(generate_error_messages(orders, items))

    return messages

def parse_csv_data(data):
    customers = {}
    orders = {}
    items = {}

    for line in data.strip().split("\n"):
        fields = line.split(";")

        if len(fields) == 5:
            if fields[0].isdigit():
                customers[int(fields[0])] = {
                    "first_name": fields[1],
                    "last_name": fields[2],
                    "customer_reference": fields[3],
                    "status": fields[4]
                }
            elif fields[1].isdigit():
                orders[int(fields[0])] = {
                    "customer_reference": fields[1],
                    "order_status": fields[2],
                    "order_reference": fields[3],
                    "order_timestamp": int(fields[4])
                }
            else:
                items[int(fields[0])] = {
                    "order_reference": fields[1],
                    "item_name": fields[2],
                    "quantity": int(fields[3]),
                    "total_price": Decimal(fields[4].replace(",", "."))
                }

    return customers, orders, items

def generate_customer_messages(customers, orders, items):
    customer_messages = []

    for customer_id, customer in customers.items():
        customer_orders = [order for order in orders.values() if order["customer_reference"] == customer["customer_reference"]]
        total_amount_spent = sum([item["total_price"] for item in items.values() if item["order_reference"] in [order["order_reference"] for order in customer_orders]])

        customer_messages.append({
            "type": "customer_message",
            "customer_reference": customer["customer_reference"],
            "number_of_orders": len(customer_orders),
            "total_amount_spent": float(total_amount_spent)
        })

    return customer_messages

def generate_error_messages(orders, items):
    error_messages = []

    for item_id, item in items.items():
        if item["order_reference"] not in orders:
            error_messages.append({
                "type": "error_message",
                "customer_reference": None,
                "order_reference": item["order_reference"],
                "message": "Something went wrong!"
            })

    return error_messages

def send_message(message):
    sqs.send_message(QueueUrl="your_sqs_queue_url", MessageBody=json.dumps(message))

def store_data(customer_message):
    table = dynamodb.Table("customer_data")
    table.put_item(
        Item={
            "customer_reference": customer_message["customer_reference"],
            "number_of_orders": customer_message["number_of_orders"],
            "total_amount_spent": customer_message["total_amount_spent"]
        }
    )