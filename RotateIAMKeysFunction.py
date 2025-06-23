import boto3, json, traceback
from datetime import datetime, timezone

iam      = boto3.client('iam')
secrets  = boto3.client('secretsmanager')
sns      = boto3.client('sns')
dynamo   = boto3.resource('dynamodb').Table('KeyRotationHistory')

SNS_TOPIC_ARN = '<Region>:<Account Number>:iam-key-rotation-notify'

def notify(subject, message):
    sns.publish(TopicArn=SNS_TOPIC_ARN,
                Subject=subject,
                Message=json.dumps(message, indent=2))

def put_history(username, old_id, new_id):
    dynamo.put_item(Item={
        'Username':           username,
        'RotationTimestamp':  datetime.now(timezone.utc).isoformat(),
        'OldKeyId':           old_id,
        'NewKeyId':           new_id
    })

def lambda_handler(event, context):
    try:
        for user in iam.list_users()['Users']:
            username = user['UserName']
            keys = iam.list_access_keys(UserName=username)['AccessKeyMetadata']

            # --- 1. De-activate the current active key (if any) -------------
            active_keys = [k for k in keys if k['Status'] == 'Active']
            old_key_id  = None
            if active_keys:
                # pick the newest active key to deactivate
                to_deactivate = sorted(active_keys, key=lambda x: x['CreateDate'])[-1]
                iam.update_access_key(UserName=username,
                                      AccessKeyId=to_deactivate['AccessKeyId'],
                                      Status='Inactive')
                old_key_id = to_deactivate['AccessKeyId']

            # Refresh key list after the status change
            keys = iam.list_access_keys(UserName=username)['AccessKeyMetadata']

            # --- 2. Ensure we have < 2 keys before creating a new one -------
            if len(keys) >= 2:
                inactive_keys = [k for k in keys if k['Status'] == 'Inactive']
                # Delete the oldest inactive key to free a slot
                oldest = sorted(inactive_keys, key=lambda x: x['CreateDate'])[0]
                iam.delete_access_key(UserName=username, AccessKeyId=oldest['AccessKeyId'])

            # --- 3. Create the new access key -------------------------------
            new_key = iam.create_access_key(UserName=username)['AccessKey']

            # --- 4. Store/Update secret in Secrets Manager ------------------
            secret_name = f"{username}-api-keys"
            secret_body = json.dumps({
                "AccessKeyId":     new_key['AccessKeyId'],
                "SecretAccessKey": new_key['SecretAccessKey']
            })
            try:
                secrets.put_secret_value(SecretId=secret_name,
                                         SecretString=secret_body)
            except secrets.exceptions.ResourceNotFoundException:
                secrets.create_secret(Name=secret_name,
                                      SecretString=secret_body)

            # --- 5. Audit log & notification -------------------------------
            put_history(username, old_key_id, new_key['AccessKeyId'])
            notify(
                subject=f"🔄 IAM key rotated for {username}",
                message={
                    "user":      username,
                    "oldKey":    old_key_id,
                    "newKey":    new_key['AccessKeyId'],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

        return {"status": "rotation completed"}

    except Exception as e:
        traceback.print_exc()
        notify(
            subject="❌ Key rotation failed",
            message={"error": str(e), "event": event}
        )
        raise e
