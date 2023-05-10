terraform {
  backend "s3" {
    bucket         = "terraform-tfstate-gt"
    key            = "terraform.tfstate"
    region         = "eu-central-1" # Replace with the AWS region where your bucket is located
    encrypt        = true
    # dynamodb_table = "terraform-lock" # Optional: if you want to enable state locking using DynamoDB
  }
}


provider "aws" {
  region = "eu-central-1"
}

resource "aws_s3_bucket" "bucket" {
  bucket = "gt-task-bucket-10-05-23"
}

resource "aws_s3_bucket_policy" "bucket_policy" {
  bucket = aws_s3_bucket.bucket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "s3:GetObject"
        Effect = "Allow"
        Resource = "${aws_s3_bucket.bucket.arn}/*"
        Principal = {
          AWS = aws_iam_role.lambda_role.arn
        }
      }
    ]
  })
}


resource "aws_sqs_queue" "queue" {
name = "queue_name"
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.bucket.id
    lambda_function {
      lambda_function_arn = aws_lambda_function.data_processing.arn
      events              = ["s3:ObjectCreated:*"]
      filter_prefix       = "input/"
    }
  
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

resource "aws_dynamodb_table" "customer_data" {
  name           = "customer_data"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "customer_reference"

  attribute {
    name = "customer_reference"
    type = "S"
  }
}

resource "aws_lambda_function" "data_processing" {
  function_name = "data_processing"
  handler       = "lambda_function.lambda_handler"
  role          = aws_iam_role.lambda_role.arn
  runtime       = "python3.8"

  filename         = "lambda_function.zip"
  source_code_hash = filebase64sha256("lambda_function.zip")
}


resource "aws_iam_role_policy" "lambda_role_policy" {
  name = "lambda_role_policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "sqs:SendMessage",
          "dynamodb:PutItem"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = "lambda:InvokeFunction"
        Effect = "Allow"
        Resource = aws_lambda_function.data_processing.arn
      }
    ]
  })
}

resource "aws_lambda_permission" "allow_bucket_invocation" {
  statement_id  = "AllowS3BucketInvocation"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_processing.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.bucket.arn
}
