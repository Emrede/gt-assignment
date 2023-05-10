#!/bin/bash

BUCKET_NAME="gt-task-bucket-10-05-23"
aws s3 cp example-data/customers_20230510.csv s3://$BUCKET_NAME/input/customers_20230510.csv
aws s3 cp example-data/orders_20230510.csv s3://$BUCKET_NAME/input/orders_20230510.csv
aws s3 cp example-data/items_20230510.csv s3://$BUCKET_NAME/input/items_20230510.csv