provider "aws" {
  region = "eu-central-1"
}

resource "aws_s3_bucket" "data_bucket" {
  bucket = "your-data-bucket"
}

resource "aws_dynamodb_table" "processed_data" {
  name           = "ProcessedData"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"
  read_capacity  = 1
  write_capacity = 1

  attribute {
    name = "id"
    type = "S"
  }
}

resource "aws_sqs_queue" "data_queue" {
  name = "your_queue_name"
}

resource "aws_lambda_function" "data_processor" {
  function_name = "data_processor"
  runtime       = "python3.8"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"

  # Upload the zipped lambda_function.py
  filename = "lambda_function.zip"
}

resource "aws_lambda_event_source_mapping" "s3_event" {
  event_source_arn = aws_s3_bucket.data_bucket.arn
  function_name    = aws_lambda_function.data_processor.function_name
  starting_position = "LATEST"
}

resource "aws_iam_role" "lambda_role" {
  name = "lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "s3_lambda_access" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
  role       = aws_iam_role.lambda_role.name
}

resource "aws_iam_role_policy_attachment" "dynamodb_lambda_access" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
  role       = aws_iam_role.lambda_role.name
}

resource "aws_iam_role_policy_attachment" "sqs_lambda_access" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonSQSFullAccess"
  role       = aws_iam_role.lambda_role.name
}
