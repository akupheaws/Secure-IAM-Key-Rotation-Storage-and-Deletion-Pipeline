Secure IAM Key Rotation, Storage, and Deletion Pipeline

This project automates the full lifecycle of IAM access keys using AWS Lambda, EventBridge, Secrets Manager, DynamoDB, and SNS. It rotates access keys every 30 days, deactivates the old ones, updates Secrets Manager with new credentials, deletes keys that remain inactive for 30+ days, and logs all activities to DynamoDB. Real-time notifications are sent via SNS for visibility and accountability.

This pipeline improves security posture by enforcing short-lived credentials, eliminates manual key management, and aligns with AWS best practices.

🔗 Full project guide is available on Medium:https://medium.com/@akupheaws/secure-iam-key-rotation-storage-and-deletion-pipeline-009611fa3e33
