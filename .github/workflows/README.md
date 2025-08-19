# GitHub Actions CI/CD

This repository uses GitHub Actions for automated CI/CD with GitOps deployment via ArgoCD.

## Workflows

### 1. CI - Build and Test (`ci.yml`)
**Triggers:** Pull requests and feature branches (excluding `main` and `staging`)

**Jobs:**
- **Lint & Test**: Runs Python linting, type checking, and tests
- **Build Docker**: Builds and pushes Docker image to ECR with feature branch tag
- **Helm Lint**: Validates Helm charts and templates
- **Security Scan**: Runs Trivy vulnerability scanner

### 2. GitOps Deploy (`argocd-gitops.yml`)
**Triggers:** Pushes to `main` or `staging` branches, manual workflow dispatch

**Jobs:**
- Builds and pushes Docker image to ECR
- Creates/updates ArgoCD application
- Waits for deployment sync (optional)
- Verifies deployment status

## Environment Configuration

### Branch Mapping
- `main` branch → **Production** environment
- `staging` branch → **Staging** environment

### Required AWS Resources
- **ECR Repository**: `820976530109.dkr.ecr.ap-southeast-1.amazonaws.com/clickhouse-mcp`
- **IAM Role**: `arn:aws:iam::820976530109:role/polly-stg-clickhouse-mcp-github-actions`
- **EKS Cluster**: `polly-k8s-stg`

### GitHub Secrets & Variables
**Repository Variables:**
- `WAIT_FOR_SYNC`: Set to `'true'` to enable ArgoCD sync waiting
- `ARGOCD_SERVER`: ArgoCD server URL (if using CLI)

**Repository Secrets:**
- `ARGOCD_AUTH_TOKEN`: ArgoCD authentication token (optional)

## Deployment Target
- **Namespace**: `mcp-services`
- **Service Name**: `clickhouse-mcp`
- **Values Files**: 
  - `values.yaml` (base configuration)
  - `values-staging.yaml` (staging overrides)
  - `values-production.yaml` (production overrides)

## Manual Deployment
You can trigger deployments manually using the GitHub Actions UI:
1. Go to Actions tab
2. Select "GitOps Deploy via ArgoCD"
3. Click "Run workflow"
4. Choose environment (staging/production)

## Security
- Uses OIDC for AWS authentication (no long-lived credentials)
- Docker images are scanned for vulnerabilities
- Kubernetes manifests are validated before deployment
- All secrets are managed via AWS Secrets Manager and External Secrets Operator
