import boto3, json, traceback
from datetime import datetime, timezone

# Initialize AWS clients
iam = boto3.client('iam')
sns = boto3.client('sns')

# Update with your actual SNS topic ARN for deletion alerts
SNS_TOPIC_ARN = 'arn:aws:sns:<Region>:<Account Number>:iam-key-deletion-notify'

# Threshold in days to decide when to delete an unused inactive key
THRESHOLD_DAYS = 30


def notify(subject, message):
    """Publish a message to SNS."""
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=subject,
        Message=json.dumps(message, indent=2)
    )


def lambda_handler(event, context):
    try:
        now = datetime.now(timezone.utc)
        deleted_keys = []

        # Iterate through all IAM users
        for user in iam.list_users()['Users']:
            username = user['UserName']
            keys = iam.list_access_keys(UserName=username)['AccessKeyMetadata']

            for key in keys:
                # Skip keys that are still Active
                if key['Status'] != 'Inactive':
                    continue

                # Check last used date for the key
                last_used_info = iam.get_access_key_last_used(AccessKeyId=key['AccessKeyId'])
                last_used_date = last_used_info['AccessKeyLastUsed'].get('LastUsedDate')

                # Decide whether to delete the key
                if (last_used_date is None) or ((now - last_used_date).days > THRESHOLD_DAYS):
                    iam.delete_access_key(UserName=username, AccessKeyId=key['AccessKeyId'])
                    deleted_keys.append({
                        'user': username,
                        'keyId': key['AccessKeyId'],
                        'lastUsed': str(last_used_date)
                    })

        # Notify success via SNS
        notify(
            subject="✅ IAM inactive keys deleted",
            message={
                'timestamp': now.isoformat(),
                'deletedKeys': deleted_keys or 'No inactive keys found.'
            }
        )

        return {
            'status': 'completed',
            'deleted': deleted_keys
        }

    except Exception as e:
        # Log full stack trace and notify failure
        traceback.print_exc()
        notify(
            subject="❌ Inactive key deletion failed",
            message={
                'error': str(e),
                'event': event
            }
        )
        raise e