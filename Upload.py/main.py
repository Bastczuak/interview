# serverless.yml
# downloadToEc2FromS3:
#   handler: download_to_ec2_from_s3
#   events:
#     - http:
#         path: /upload/{stack}/s3
#         method: POST
# generateS3UploadUrl:
#   handler: generate_s3_upload_url
#   events:
#     - http:
#         path: /upload/{stack}
#         method: POST
# notifyTeamsAfterUpload:
#   handler: on_event_notify_teams_after_upload
#   events:
#     - sns:
#         arn: arn:aws:sns:eu-west-1:${self:custom.account_id}:ssmCommandUploadFinished
#         topicName: ssmCommandUploadFinished

# order of API calls
# 1. POST /upload/stack-1234
# 2. POST /upoad/stack-1234/s3

import json_http_response
import boto3
import re
import os
import Instance
import extract_region
import publish_alert
import ClientApiException


def generate_s3_upload_url(event, _):
  instance = Instance.get(stack_name=event['pathParameters']['id'])
  required_keys = [
    'MIB/', 'devicetemplates/', 'lookups/custom/', 'snmplibs/',
    'webroot/icons/devices/'
  ]
  files = event['body']
  missing_keys = [key for key in required_keys if key not in files]

  if missing_keys:
    print(f'Missing keys {missing_keys} in body parameter "files" found!'
          'This should never happened so something is wrong in the frontend!')
    raise ClientApiException(
      'Could not upload because of missing required parameters!', 422)

  s3 = boto3.client('s3')
  upload_urls = {}
  reject_big_files = []
  FILE_SIZE_LIMIT_1MB = 1048576
  for key in required_keys:
    for file in files[key]:
      if file['content_length'] > FILE_SIZE_LIMIT_1MB:
        reject_big_files.append(file['name'])
        continue

      name = file['name']
      path = f'{instance.stack_name}/{key}{name}'
      upload_url = s3.generate_presigned_url(
        'put_object', {
          'Bucket': os.environ['S3_BUCKET'],
          'Key': path,
          'ContentType': file['content_type'],
          'ContentLength': file['content_length'],
          'ContentMD5': file['md5_base64'],
        },
        ExpiresIn=60)
      upload_urls[f'{key}{name}'] = upload_url

  if reject_big_files:
    raise ClientApiException(
      f'Could not upload files because {", ".join(reject_big_files)} are '
      f'exceeding the maximum file size of 1MB!', 422)

  return json_http_response(upload_urls)


def download_to_ec2_from_s3(event, _):
  instance = Instance.get(stack_name=event['pathParameters']['id'])
  prefix = f'{instance.stack_name}/'
  s3 = boto3.client('s3')
  s3_objects = s3.list_objects_v2(Bucket=os.environ['S3_BUCKET'],
                                  Prefix=prefix)
  downloads = []
  for content in s3_objects.get('Contents', []):
    bucket = os.environ['S3_BUCKET']
    key = content['Key']
    url = s3.generate_presigned_url('get_object', 
      {
        'Bucket': bucket,
        'Key': key,
      },
      ExpiresIn=60
    )
    downloads.append(
      f'@{{Url="{url}"; Output="D:/uploads/{key.replace(prefix, "")}";}}'
    )

  region = extract_region(instance.stack_name)
  ssm = boto3.client('ssm', region_name=region)
  result = ssm.send_command(
    DocumentName='AWS-RunPowerShellScript',
    InstanceIds=[instance.instance_id],
    NotificationConfig={
      'NotificationArn':
      f'arn:aws:sns:{region}:{os.environ["AWS_ACCOUNT_ID"]}:ssmCommandUploadFinished',
      'NotificationEvents': ['Success', 'Failed'],
      'NotificationType': 'Command',
    },
    OutputS3BucketName=os.environ['SSM_COMMAND_RESULTS_BUCKET'],
    OutputS3KeyPrefix='AWS-RunPowerShellScript',
    Parameters={
      'commands': [
        s.strip() for s in f"""
              $ErrorActionPreference = "Stop"
              [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
              $downloads = @({', '.join(downloads)})
              foreach($download in $downloads) {{
                New-Item -Path $download['Output'] -Force
                (New-Object System.Net.WebClient).DownloadFile($download['Url'], $download['Output'])
              }}
              dir -Path D:/uploads/ -Recurse
            """.strip().split('\n')
      ]
    },
    ServiceRoleArn=os.environ['SNS_PUBLISH_IAM_ROLE'],
    TimeoutSeconds=300,
  )

  return json_http_response(result['Command']['CommandId'])


def on_event_notify_teams_after_download(event, _):
  json_dump = json.loads(event["Records"][0]["Sns"]["Message"])
  status = json_dump["status"]
  region = re.sub(r"^(?:[^:]+:){3}([^:]+).*", "\\1",
                  event["Records"][0]["EventSubscriptionArn"])
  instance_id = json_dump["instanceIds"][0]
  ec2 = boto3.resource("ec2", region_name=region).Instance(instance_id)
  ec2_tags = {tag["Key"]: tag["Value"] for tag in ec2.tags or []}
  subscription_id, stack_name = (
    ec2_tags.get(key)
    for key in ["subscription_id", "aws:cloudformation:stack-name"])
  prefix = (f"{json_dump['outputS3KeyPrefix']}/{json_dump['commandId']}/"
            f"{instance_id}/awsrunPowerShellScript/0.awsrunPowerShellScript/")

  message = {
    "subscription":
    subscription_id,
    "instance_id":
    instance_id,
    "stack_name":
    f"https://app.my-prtg.com/support?search={stack_name}",
    "result_bucket":
    (f"https://s3.console.aws.amazon.com/s3/buckets/{json_dump['outputS3BucketName']}"
     f"?prefix={prefix}"),
    "target_bucket":
    (f"https://s3.console.aws.amazon.com/s3/buckets/{os.environ['S3_BUCKET']}"
     f"?prefix={stack_name}/"),
  }

  if status == "Success":
    publish_alert(
      sns_topic="team-cloud-file-upload-alerting",
      reason=(f"Successfully uploaded files from {upload_source} via SSM."
              f'\n\nTarget bucket is {message["target_bucket"]}.'
              f'\n\nLogs are stored here {message["result_bucket"]}.'),
      message=message,
      description=
      f"This occurs when the Powershell script for uploading files from {upload_source}"
      f" to EC2 ran successful.",
      subject=f"{upload_source} File Upload",
    )
  elif status == "Failed":
    publish_alert(
      sns_topic="team-cloud-alerting2",
      reason=f"Failed to upload files from {upload_source} via SSM.\n\nLogs are"
      f' stored here {message["result_bucket"]}',
      message=message,
      description=(
        f"This occurs when there was an error while running Powershell scripts for uploading"
        f" files from {upload_source} to EC2."),
      subject=f"{upload_source} File Upload",
    )
