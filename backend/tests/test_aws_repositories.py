import io
import boto3
import pytest
from moto import mock_aws
from backend.app.repositories.dynamodb_repository import DynamoDBRepository
from backend.app.repositories.s3_repository import S3Repository
from backend.app.schemas.project import ProjectCreate, ProjectPolicy
from backend.app.schemas.release import ReleaseCreate, ArtifactDescriptor

@mock_aws
def test_dynamodb_repository_workflow():
    region = "ap-south-1"
    table_name = "TestBuildTrustRecords"
    
    # Create DynamoDB table
    dynamodb = boto3.resource("dynamodb", region_name=region)
    dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST"
    )

    repo = DynamoDBRepository(table_name=table_name, region_name=region)

    # 1. Create project
    proj = repo.create_project(
        ProjectCreate(project_id="aws-proj-1", name="AWS Project", policy=ProjectPolicy()),
        creator="aws-tester"
    )
    assert proj.project_id == "aws-proj-1"

    # 2. Get project
    fetched = repo.get_project("aws-proj-1")
    assert fetched is not None
    assert fetched.name == "AWS Project"

    # 3. Create release
    rel = repo.create_release(
        ReleaseCreate(
            project_id="aws-proj-1",
            release_id="aws-rel-1",
            version="1.0.0",
            source_commit="commit-aws-123",
            artifact=ArtifactDescriptor(
                filename="aws-artifact.zip",
                expected_sha256="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
            )
        ),
        creator="aws-tester"
    )
    assert rel.release_id == "aws-rel-1"

    # 4. List releases
    releases = repo.list_releases(project_id="aws-proj-1")
    assert len(releases) == 1

@mock_aws
def test_s3_repository_upload_and_download():
    region = "ap-south-1"
    bucket_name = "test-buildtrust-bucket"

    s3 = boto3.client("s3", region_name=region)
    s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": region}
    )

    s3_repo = S3Repository(bucket_name=bucket_name, region_name=region)

    data = b"Encrypted release package content"
    key = "artifacts/proj1/1.0.0/release.zip"
    
    uri = s3_repo.upload_artifact_bytes(key, data)
    assert f"s3://{bucket_name}/{key}" == uri

    # Download
    downloaded = s3_repo.get_artifact_bytes(key)
    assert downloaded == data
