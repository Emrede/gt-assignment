# import boto3
# import csv
# import json
# from io import StringIO
# from datetime import datetime

# s3 = boto3.client('s3')
# sqs = boto3.client('sqs')
# dynamodb = boto3.resource('dynamodb')

# sqs_queue_url = "https://sqs.<region>.amazonaws.com/<account_id>/your_queue_name"
# dynamodb_table = dynamodb.Table('ProcessedData')

# def lambda_handler(event, context):
#     # Get the S3 object and read the file content
#     bucket = event['Records'][0]['s3']['bucket']['name']
#     key = event['Records'][0]['s3']['object']['key']
#     s3_object = s3.get_object(Bucket=bucket, Key=key)
#     file_content = s3_object['Body'].read().decode('utf-8')

#     # Process CSV file
#     data = list(csv.DictReader(StringIO(file_content)))

#     # Determine file type and process accordingly
#     file_type = key.split('_')[0]
#     if file_type == 'customers':
#         process_customers(data)
#     elif file_type == 'orders':
#         process_orders(data)
#     elif file_type == 'items':
#         process_items(data)
#     else:
#         raise ValueError("Invalid file type")

# def process_customers(data):
#     for row in data:
#         customer_reference = row['customer_reference']
#         # Add customer data to DynamoDB
#         dynamodb_table.put_item(Item=row)

#         # Generate customer message and send to SQS queue
#         customer_message = {
#             "type": "customer_message",
#             "customer_reference": customer_reference,
#         }
#         sqs.send_message(QueueUrl=sqs_queue_url, MessageBody=json.dumps(customer_message))

# def process_orders(data):
#     for row in data:
#         order_reference = row['order_reference']
#         customer_reference = row['customer_reference']
        
#         # Add order data to DynamoDB
#         dynamodb_table.put_item(Item=row)

#         # Generate error message for unexpected input
#         if row['order_status'] not in ['Delivered', 'Pending']:
#             error_message = {
#                 "type": "error_message",
#                 "customer_reference": customer_reference,
#                 "order_reference": order_reference,
#                 "message": "Invalid order status"
#             }
#             sqs.send_message(QueueUrl=sqs_queue_url, MessageBody=json.dumps(error_message))

# def process_items(data):
#     orders = {}
#     for row in data:
#         order_reference = row['order_reference']
#         total_price = float(row['total_price'])
        
#         # Add item data to DynamoDB
#         dynamodb_table.put_item(Item=row)

#         # Calculate total_amount_spent and number_of_orders
#         if order_reference in orders:
#             orders[order_reference] += total_price
#         else:
#             orders[order_reference] = total_price

#     for order_reference, total_amount_spent in orders.items():
#         customer_message = {
#             "type": "customer_message",
#             "customer_reference": "unknown",
#             "number_of_orders": 1,
#             "total_amount_spent": total_amount_spent
#         }
       
#         # Get customer reference from DynamoDB using order_reference
#         order_data = dynamodb_table.get_item(Key={'id': order_reference})
#         if 'Item' in order_data:
#             customer_reference = order_data['Item']['customer_reference']
#             customer_message['customer_reference'] = customer_reference

#         # Update customer message with total_amount_spent and number_of_orders
#         response = dynamodb_table.update_item(
#             Key={'id': customer_reference},
#             UpdateExpression="SET number_of_orders = if_not_exists(number_of_orders, :num) + :inc, total_amount_spent = if_not_exists(total_amount_spent, :val) + :total",
#             ExpressionAttributeValues={
#                 ':num': 0,
#                 ':inc': 1,
#                 ':val': 0.0,
#                 ':total': total_amount_spent
#             },
#             ReturnValues="UPDATED_NEW"
#         )

#         # Send the customer message to SQS queue
#         sqs.send_message(QueueUrl=sqs_queue_url, MessageBody=json.dumps(customer_message))



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