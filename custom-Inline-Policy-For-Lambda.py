{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "IAMAccessKeyManagement",
      "Effect": "Allow",
      "Action": [
        "iam:ListUsers",
        "iam:ListAccessKeys",
        "iam:GetAccessKeyLastUsed",
        "iam:UpdateAccessKey",
        "iam:CreateAccessKey",
        "iam:DeleteAccessKey"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowSnsPublishingRotation",
      "Effect": "Allow",
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:<region>:<account-id>:iam-key-rotation-notify"
    },
    {
      "Sid": "AllowSnsPublishingDeletion",
      "Effect": "Allow",
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:<Region>:<Account Number>:iam-key-deletion-notify"
    }
  ]
}