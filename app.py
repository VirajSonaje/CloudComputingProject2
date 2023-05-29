import json
import torch
import torchvision
import torchvision.transforms as transforms
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from models.inception_resnet_v1 import InceptionResnetV1
from urllib.request import urlopen
from PIL import Image
import numpy as np
import build_custom_model
import os
import boto3
import urllib.parse

def handler(event, context):
    print('Loading function')
    AWS_REGION_NAME=''
    AWS_ACCESS_KEY=""
    AWS_SECRET_ACCESS_KEY=""

    s3_client = boto3.client('s3',region_name=AWS_REGION_NAME)
    
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    key=event['frame']
    bucket="first-lambda-output"
    try:
        storage_path = "/tmp/"
        filename = storage_path + str(key)
        response = s3_client.get_object(Bucket=bucket, Key=key)
        s3_client.download_file(Bucket=bucket, Key=key, Filename=filename)

        print("Frame " + str(os.listdir(storage_path)) + " stored!")

    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e
    
    labels_dir = "./checkpoint/labels.json"
    model_path = "./checkpoint/model_vggface2_best.pth"

    img_path = filename

    # read labels
    with open(labels_dir) as f:
        labels = json.load(f)
    #print(f"labels: {labels}")
    #print("List of files : " + str(os.listdir(".")))

    device = torch.device('cpu')
    print("I am here 1")
    model = build_custom_model.build_model(len(labels)).to(device)
    print("I am here 2")
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu'))['model'])
    print("I am here 3")
    model.eval()
    print(f"Best accuracy of the loaded model: {torch.load(model_path, map_location=torch.device('cpu'))['best_acc']}")

    img = Image.open(img_path)
    img_tensor = transforms.ToTensor()(img).unsqueeze_(0).to(device)
    outputs = model(img_tensor)
    _, predicted = torch.max(outputs.data, 1)
    result = labels[np.array(predicted.cpu())[0]]
    print(predicted.data, result)


    img_name = img_path.split("/")[-1]
    img_and_result = f"({img_name}, {result})"
    print(f"Image and its recognition result is: {img_and_result}")

    dynamodb_client = boto3.client('dynamodb')
    dynamodb_table_name = 'student_info'
    data = dynamodb_client.get_item(
            TableName=dynamodb_table_name,
            Key={
                'name': {
                    'S': str(result)
                    }
                }
            )
    
    body = {
        #"message": "Go Serverless v1.0! Your function executed successfully!",
        "recognition_result": img_and_result,
        "dynamoDB_info": data['Item'],
        "input": event
    }

    print("DynamoDB result: " + str(data['Item']))

    output_filename = key.split(".")[0] + ".json"
    #with open(storage_path + output_filename, 'w') as fp:
    #    json.dump(data['Item'], fp)

    #print("Files in storage: " + str(os.listdir(storage_path)))

    output_bucket = "dynamooutputbucketcc"
    
    #for f in os.listdir(storage_path):
    #    if f.endswith('.json'):
    #        print(f)
    #        s3_upload_response = s3_client.upload_file(storage_path + f, output_bucket, f)

    json_object=json.dumps(data['Item'])
        
    s3_client.put_object(
        Body=json_object,
        Bucket=output_bucket,
        Key=output_filename
    )

    #INPUT_QUEUE_URL="https://sqs.us-east-1.amazonaws.com/791725755823/output.fifo"  
    INPUT_QUEUE_URL="https://sqs.us-east-1.amazonaws.com/791725755823/saiqueue2"
    sqs = boto3.client("sqs",region_name=AWS_REGION_NAME, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    sqs.send_message(
                QueueUrl=INPUT_QUEUE_URL,
                DelaySeconds=10,
                MessageBody=(json_object)
            )
    
    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response
