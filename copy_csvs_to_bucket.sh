#!/bin/bash

aws s3 cp example-data/customers_20230510.csv s3://gt-task-bucket-10-05-23/customers_20230510.csv
aws s3 cp example-data/orders_20230510.csv s3://gt-task-bucket-10-05-23/orders_20230510.csv
aws s3 cp example-data/items_20230510.csv s3://gt-task-bucket-10-05-23/items_20230510.csv