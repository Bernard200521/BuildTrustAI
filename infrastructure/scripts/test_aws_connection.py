import os
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def test_connection():
    print("==================================================")
    print("      BuildTrust AI - AWS Credential Verifier     ")
    print("==================================================")

    # 1. Read environment or prompt
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_REGION", "ap-south-1")

    if not access_key or not secret_key:
        print("\nNotice: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY not found in environment.")
        print("To connect programmatically to AWS, an IAM Access Key is required.")
        print("Steps to obtain your Access Key from AWS Console:")
        print("  1. Sign in to https://console.aws.amazon.com")
        print("  2. In the top-right corner, click your account name -> 'Security credentials'")
        print("  3. Scroll down to 'Access keys' and click 'Create access key'")
        print("  4. Copy the Access Key ID (starts with AKIA...) and Secret Access Key\n")
        return False

    print(f"\nTarget Region: {region}")
    print(f"Testing AWS STS Authentication with Access Key: {access_key[:6]}****** ...")

    try:
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        sts = session.client("sts")
        identity = sts.get_caller_identity()

        print("\nSUCCESS! Successfully authenticated with AWS Cloud:")
        print(f"  Account ID: {identity['Account']}")
        print(f"  Caller ARN: {identity['Arn']}")
        print(f"  User ID:    {identity['UserId']}")

        # Test DynamoDB accessibility
        print("\nChecking Amazon DynamoDB connectivity...")
        dynamodb = session.client("dynamodb")
        tables = dynamodb.list_tables().get("TableNames", [])
        print(f"  DynamoDB connected. Found {len(tables)} table(s).")

        # Test S3 accessibility
        print("Checking Amazon S3 connectivity...")
        s3 = session.client("s3")
        buckets = s3.list_buckets().get("Buckets", [])
        print(f"  Amazon S3 connected. Found {len(buckets)} bucket(s).")

        print("\n==================================================")
        print("  AWS Cloud Persistence Ready for BuildTrust AI! ")
        print("==================================================")
        return True

    except NoCredentialsError:
        print("ERROR: AWS credentials could not be located.")
        return False
    except ClientError as e:
        print(f"ERROR: AWS returned error: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected exception: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
