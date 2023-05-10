# GT-Assignment #

## TERRAFORM ##
This Terraform configuration creates an S3 bucket, a Lambda function, an SQS queue, a DynamoDB instance to write the data and the necessary IAM roles and policies for the Lambda function to access the S3 bucket and SQS queue.

Before running Terraform, create a Lambda package with your Lambda function code:

1. Create a ZIP file containing your `lambda_function.py` file.
2. Update the `lambda-function.zip` in the Terraform configuration to match the name of your ZIP file.

Then, run `terraform init` and `terraform apply` to create the resources.

With this setup, the data processing pipeline is ready, and you can test it by uploading CSV files to the S3 bucket. Run copy_csvs_to_bucket.sh to copy needed files to the bucket automatically. Please make sure AWS CLI is configured before running the script. 

Lambda function will be triggered automatically upon file upload and process the data accordingly.


## RESULTS ##
With the Terraform configuration and Lambda function in place, our serverless data processing pipeline is now set up. Here's a discussion of the solution, its scalability, and potential improvements:

The solution leverages AWS Lambda for processing, which is highly scalable and can handle a large number of concurrent executions. Lambda automatically scales with the number of incoming S3 events, and you only pay for the compute time you consume.
The data is stored in Amazon DynamoDB, which is a managed NoSQL database service that provides fast and predictable performance with seamless scalability. DynamoDB can handle more than 10 trillion requests per day and support peaks of more than 20 million requests per second.
Amazon SQS is used for message queuing. It's a fully managed message queuing service that enables you to decouple and scale microservices, distributed systems, and serverless applications. SQS eliminates the complexity and overhead associated with managing and operating message-oriented middleware and can scale to handle an unlimited number of messages.

Potential improvements:

Error handling: Improve error handling by adding more specific checks, logging errors in a separate system like Amazon CloudWatch Logs or sending notifications using Amazon SNS.
Dead Letter Queue: Configure a dead-letter queue for the Lambda function to handle failed executions and avoid processing the same event multiple times when something goes wrong.
Data validation: Add data validation checks and data cleansing steps in the Lambda function to ensure data consistency.
Parallel processing: For large files, split the file into smaller chunks and process them in parallel to improve the overall processing time.
Use AWS Step Functions to orchestrate the data processing pipeline. This enables better error handling, retry mechanisms, and more complex processing workflows if needed in the future.
By implementing these improvements, you can further enhance the performance, scalability, and maintainability of the data processing pipeline.


- Given example data turned into .csv files for test purposes

Terraform Resources: 
- aws
- terraform
- "aws_s3_bucket" "data_bucket"
- "aws_dynamodb_table" "processed_data"
- "aws_sqs_queue" "data_queue"
- "aws_lambda_function" "data_processor"
- "aws_lambda_event_source_mapping" "s3_event"
- "aws_iam_role" "lambda_role"
- "aws_iam_role_policy_attachment" "s3_lambda_access"
- "aws_iam_role_policy_attachment" "dynamodb_lambda_access"
- "aws_iam_role_policy_attachment" "sqs_lambda_access"


Run Lambda function with:
aws lambda invoke --function-name data_processing --payload file://s3_event.json output.txt
