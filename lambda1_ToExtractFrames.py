import json
import os
import urllib
import boto3
import time

def lambda_handler(event, context):
    
    key=event['key']
    bucket=event['bucket']
    s3 = boto3.client('s3',region_name='us-east-1')
    lambda_client = boto3.client("lambda",region_name='us-east-1')
    
    path = "/tmp/"
    video_file_path = path+key
    print(video_file_path)
    
    response = s3.get_object(Bucket=bucket, Key=key)
    s3.download_file(bucket, key, video_file_path)
    print("Downloaded files " , os.listdir(path))
    os.system("/opt/ffmpeglib/ffmpeg -i " + str(video_file_path) + " -frames:v 1 -s 160X160 " +  str(path) + "image-%03d.png")
    print(os.listdir(path))

    for filename in os.listdir(path):
        if filename.endswith('.png'):
            f=key.split(".")[0]+"_"+filename.split("-")[1]
            print(f)
            s3.upload_file(path+filename,"first-lambda-output",f)
    
            print("Extracted files" , os.listdir(path))
        
            lambda_payload={"frame":f}
    
            response = lambda_client.invoke(
                FunctionName='image_recogniton_second_lambda',
                InvocationType='RequestResponse',
                Payload=bytes(json.dumps(lambda_payload),encoding='utf-8')
            )
    
            print("Lambda response : ",response)
            response_payload=json.loads(response['Payload'].read())
            body=response_payload.get("body")
            print("body",body)
        
            return {
                'statusCode': 200,
                'message': "response from image_recogniton_second_lambda",
                'body': body
            }
    