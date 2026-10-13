# ==============================================================================
# BuildTrust AI - AWS Deployment Automation Script
# ==============================================================================
[CmdletBinding()]
param(
    [string]$AwsRegion = "ap-south-1",
    [string]$Environment = "staging",
    [string]$StackName = "buildtrust-ai-stack"
)

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "     BuildTrust AI - AWS Deployment Script        " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Target Region:      $AwsRegion" -ForegroundColor Yellow
Write-Host "Environment:        $Environment" -ForegroundColor Yellow
Write-Host "CloudFormation:     $StackName" -ForegroundColor Yellow

# Step 1: Check AWS Credentials
Write-Host "`n[Step 1/5] Checking AWS Credentials..." -ForegroundColor Cyan
try {
    $caller = & aws sts get-caller-identity | ConvertFrom-Json
    Write-Host "Authenticated as AWS Account: $($caller.Account) (Arn: $($caller.Arn))" -ForegroundColor Green
} catch {
    Write-Error "AWS Credentials not detected. Please configure via 'aws configure' or export AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY."
    exit 1
}

# Step 2: Deploy CloudFormation / SAM Stack (DynamoDB, S3, IAM, CloudWatch)
Write-Host "`n[Step 2/5] Deploying CloudFormation Stack ($StackName)..." -ForegroundColor Cyan
try {
    & aws cloudformation deploy `
        --template-file infrastructure/aws/template.yaml `
        --stack-name $StackName `
        --parameter-overrides Environment=$Environment AwsRegionParam=$AwsRegion `
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM `
        --region $AwsRegion
    Write-Host "CloudFormation resources successfully deployed!" -ForegroundColor Green
} catch {
    Write-Error "Failed to deploy CloudFormation stack: $_"
    exit 1
}

# Step 3: Retrieve Stack Outputs
Write-Host "`n[Step 3/5] Querying deployed stack outputs..." -ForegroundColor Cyan
$outputs = & aws cloudformation describe-stacks --stack-name $StackName --region $AwsRegion --query "Stacks[0].Outputs" | ConvertFrom-Json

$dynamoTable = ($outputs | Where-Object { $_.OutputKey -eq "DynamoDBTableName" }).OutputValue
$s3Bucket = ($outputs | Where-Object { $_.OutputKey -eq "S3BucketName" }).OutputValue
$instanceRole = ($outputs | Where-Object { $_.OutputKey -eq "AppRunnerInstanceRoleArn" }).OutputValue

Write-Host " -> DynamoDB Table: $dynamoTable" -ForegroundColor Green
Write-Host " -> S3 Vault Bucket: $s3Bucket" -ForegroundColor Green
Write-Host " -> Instance Role:  $instanceRole" -ForegroundColor Green

# Step 4: Container Build & Push to Amazon ECR
Write-Host "`n[Step 4/5] Preparing Backend Container for App Runner..." -ForegroundColor Cyan
$repoName = "buildtrust-backend"
$ecrUri = "$($caller.Account).dkr.ecr.$AwsRegion.amazonaws.com/$repoName"

Write-Host "Logging into Amazon ECR ($ecrUri)..."
& aws ecr get-login-password --region $AwsRegion | docker login --username AWS --password-stdin "$($caller.Account).dkr.ecr.$AwsRegion.amazonaws.com"

# Ensure ECR repo exists
& aws ecr describe-repositories --repository-names $repoName --region $AwsRegion 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating ECR repository '$repoName'..."
    & aws ecr create-repository --repository-name $repoName --region $AwsRegion | Out-Null
}

Write-Host "Building Docker image..."
& docker build -t "$ecrUri`:latest" ./backend

Write-Host "Pushing Docker image to ECR..."
& docker push "$ecrUri`:latest"
Write-Host "Image pushed to $ecrUri`:latest" -ForegroundColor Green

# Step 5: Frontend Hosting
Write-Host "`n[Step 5/5] Building React Dashboard for Production Hosting..." -ForegroundColor Cyan
Set-Location frontend
& npm run build
Set-Location ..

Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "     AWS Deployment Completed Successfully!       " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "To connect your local environment to these AWS resources, set in .env:"
Write-Host "  STORAGE_BACKEND=aws"
Write-Host "  AWS_REGION=$AwsRegion"
Write-Host "  DYNAMODB_TABLE_NAME=$dynamoTable"
Write-Host "  S3_BUCKET_NAME=$s3Bucket"
