import os
import time
from threading import Thread
from picamera import PiCamera
import boto3
import json
from pprint import pprint

srcFilePath = "/home/pi/projVideos/"
destFilePath = "/home/pi/projFrames/"

AWS_REGION=""
AWS_ACCESS_KEY=""
AWS_SECRET_ACCESS_KEY=""

VIDEO_BUCKET="image-recognition-input-bucket"
FRAME_BUCKET="first-lambda-output"

s3 = boto3.resource("s3",region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
video_bucket = s3.Bucket(VIDEO_BUCKET)
frame_bucket = s3.Bucket(FRAME_BUCKET)

lambda_client = boto3.client("lambda",region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    
global_ctr = 0

def sendToS3(videoFileName):
    
    #print("Inside sendVideoToS3 for : ",videoFileName)
    
    if videoFileName in os.listdir(srcFilePath):
            try:
                newVideoFileName = "video_" + str(round(time.time_ns())).split(".")[0] + ".h264"
                
                video_bucket_obj = video_bucket.Object(newVideoFileName)
                with open(srcFilePath + videoFileName, 'rb') as vid:
                    vid.seek(0)
                    video_bucket_obj.upload_fileobj(vid) 
                
                #print(videoFileName + " ::: File upload to S3 Video Bucket : Success")

                lambda_payload={"key":newVideoFileName, "bucket":VIDEO_BUCKET}
                
                t1 = time.time_ns()
                response = lambda_client.invoke(
                    FunctionName='image_recogniton_first_lambda',
                    InvocationType='RequestResponse',
                    Payload=bytes(json.dumps(lambda_payload),encoding='utf-8')
                )
                et = int(time.time_ns())
                latency2 = (et - t1) // 1000000000
                
                response_payload=json.loads(response['Payload'].read())
                body=response_payload.get("body")
                str_dict=json.loads(body)
                #pprint(str_dict)
                
                global global_ctr
                global_ctr += 1

                final_output={}
                final_output['name']= str_dict['dynamoDB_info']['name']['S']
                final_output['major']= str_dict['dynamoDB_info']['major']['S']
                final_output['year']= str_dict['dynamoDB_info']['year']['S']
                #print(final_output)
                
                st = int(str_dict["recognition_result"].split(".png")[0].split("_")[1])
                latency = (et - st) // 1000000000
                
                #print("====================================")
                #print("Body : ",body)
                #print("Latency : ",latency)
                #print("====================================")
                
                print(f"The {global_ctr} person recognized: {final_output['name']},{final_output['major']},{final_output['year']}")
                print(f"Latency: {latency} seconds.")
                print("====================================")
                
            except Exception as e:
                pass
            
            finally:
                os.system('rm ' + srcFilePath + videoFileName)
                #print("Exiting sendVideoToS3 for : ",videoFileName)
    
def recordVideo():
    #print("Inside recordVideo...")
    
    camera = PiCamera()
    camera.rotation = 180
    #camera.resolution=(160,160)

    start_time = time.time()
    while int(time.time()-start_time) <= 300:  
        videoFileName = "video_" + str(round(time.time_ns())).split(".")[0] + ".h264"
        start_loop_time=time.time()
        
        #camera.start_preview(fullscreen=False, window = (0, 0, 640, 480))
        camera.start_recording(srcFilePath + videoFileName)
        camera.wait_recording(0.5 - (abs(time.time()-start_loop_time)))
        camera.stop_recording()
        #camera.stop_preview()
        
        #print("====================================")
        #print(videoFileName + " recorded")
        #print("====================================")
        
        t = Thread(target=sendToS3,args=(videoFileName,))
        t.start()
        
    #print("Exiting recordVideo")
        
if __name__=='__main__':
    os.system('rm -r ' + srcFilePath + '*')
    os.system('rm -r ' + destFilePath + '*')
    recordVideo()
