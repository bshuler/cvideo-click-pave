# GitHub Actions Setup Instructions

## Required Repository Secrets

To enable the GitHub Actions workflow, you need to configure the following secrets in your repository:

### How to Add Secrets

1. Go to your GitHub repository: <https://github.com/bshuler/cvideo-click-pave>
2. Click on **Settings** (top menu)
3. In the left sidebar, click **Secrets and variables** → **Actions**  
4. Click **New repository secret** for each of the following:

### Required Secrets

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AWS_ACCESS_KEY_ID` | `YOUR_BOOTSTRAP_ACCESS_KEY_ID` | Bootstrap user access key for AWS API calls |
| `AWS_SECRET_ACCESS_KEY` | `YOUR_BOOTSTRAP_SECRET_ACCESS_KEY` | Bootstrap user secret key for AWS API calls |
| `AWS_REGION` | `us-east-1` | AWS region for deployment |

### Security Notes

- These credentials provide **full administrator access** to the AWS account
- Only use these for infrastructure deployment in this repository
- The credentials are scoped to the `admin-user-ef47b899` IAM user
- Consider rotating these keys periodically
- Never commit these values to code - only use as repository secrets

### After Setup

Once you've added all three secrets:

1. The workflow will automatically run on pushes to the `main` branch
2. You can also manually trigger it from the Actions tab
3. The workflow will authenticate to AWS and deploy/update the infrastructure
4. Check the Actions tab for workflow run status and logs

### Troubleshooting

- If the workflow fails with authentication errors, verify all three secrets are set correctly
- If you see permission errors, ensure the `admin-user-ef47b899` user still exists and has admin permissions
- Check the Actions tab for detailed error logs

### Current Infrastructure State

- Admin User: `admin-user-ef47b899`
- Developer User: `developer-user-ef47b899`  
- CICD Role: `CICDDeploymentRole-ef47b899`
- State Bucket: `pave-tf-state-bucket-***-ef47b899`

The workflow is now configured to use access key authentication instead of OIDC, making it suitable for this infrastructure bootstrap repository.
