ASU CSE 546-Project 

Members of the Project

1) Alekhya Vellanki
2) Sai Kumar Reddy Chandupatla
3) Viraj Sonaje


Lambda1 Name - image_recogniton_first_lambda 
Lambda2 Name - image_recogniton_second_lambda

Video  Bucket-image-recognition-input-bucket
Frames Bucket - first-lambda-output
Dynamo DB Name - student_info


Steps to run and install .

Create all the above resources. 

In order to run our application, we have 3 main parts.
Pi
Lambda1
Lambda2

On Pi
Install boto3 library by doing “ pip3 install boto3”
Run the command: “ python3 parallelProcessing.py”  to start the capture process.

Lambda1
The ffpmeg library should be added as a layer on the lambda function. This can be done by performing a wget of the static tar xz file in a separate EC2 instance. 
Then do a tar command and copy the ffpmeg folder to a different directory . Then zip the ffmpeg folder and using the aws cli , push the layer to a S3 bucket.
Finally the layer can be made out by linking to the s3 object and finally adding it to our lambda1 function.
Have the lambda1 code and paste in the function editor using the create new function  option to get the lambda1 running.

Lambda2
	
Create a folder having the required 8 files as mentioned in Section2 .  Then perform the following commands to build the docker image,  tag the image and push the image to the AWS ECR respectively.
docker build -t docker-lambda .
docker	tagadocker-lambda 791725755823.dkr.ecr.us-east-1.amazonaws.com/docker-lambda latest
docker push 791725755823.dkr.ecr.us-east-1.amazonaws.com/docker-lambda:latest

Create a new lambda function out of the above container image to obtain the functionality of lambda2.

