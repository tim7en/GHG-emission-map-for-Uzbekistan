# Google Earth Engine Authentication Testing

This repository includes automated testing for Google Earth Engine (GEE) authentication and functionality using GitHub Actions.

## Overview

The authentication testing system validates:
- ✅ Service account authentication with `ee-sabitovty` project
- ✅ Basic API functionality (geometry, computations, collections)
- ✅ Atmospheric satellite data access (Sentinel-5P: NO₂, CO, CH₄)
- ✅ Computational capabilities and quota management
- ✅ Project-specific resource access

## Files

### GitHub Actions Workflow
- **`.github/workflows/gee-auth-check.yml`** - Automated authentication testing
  - Runs on push, pull requests, and daily schedule
  - Tests multiple Python versions (3.9, 3.10, 3.11)
  - Generates comprehensive test reports

### Local Testing
- **`test_gee_authentication.py`** - Comprehensive authentication test script
  - Can be run locally for development
  - Tests all GEE functionality required for atmospheric analysis
  - Generates detailed JSON reports

## Setup Instructions

### 1. GitHub Secrets Configuration

Add the following secret to your GitHub repository:

**`GEE_SERVICE_ACCOUNT_KEY`** - Your Google Earth Engine service account key (JSON format)

To create this secret:
1. Go to your repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `GEE_SERVICE_ACCOUNT_KEY`
4. Value: Paste your service account JSON key (entire file content)

### 2. Service Account Setup

Your service account must have:
- Access to the `ee-sabitovty` Google Cloud project
- Earth Engine API enabled
- Appropriate permissions for atmospheric data analysis

### 3. Local Development

To run tests locally:

```bash
# Activate your environment
conda activate your-environment

# Install dependencies
pip install earthengine-api google-auth google-auth-oauthlib

# Authenticate with GEE (one-time setup)
earthengine authenticate

# Run the test script
python test_gee_authentication.py
```

## Test Results

### Automated Testing
- **Schedule**: Daily at 06:00 UTC
- **Triggers**: Push to main/develop, pull requests
- **Matrix**: Python 3.9, 3.10, 3.11
- **Artifacts**: Test reports and JSON results

### Test Coverage
1. **Authentication Test**: Service account vs user token validation
2. **Basic API Test**: Server communication, geometry operations, date handling
3. **Data Access Test**: Sentinel-5P collections (NO₂, CO, CH₄), Landsat availability
4. **Computation Test**: Real atmospheric data processing with timing
5. **Resource Test**: Project quotas, asset access, large collection handling

### Success Criteria
- ✅ **Excellent**: 80%+ tests pass
- ✅ **Good**: 60-79% tests pass  
- ⚠️ **Limited**: 40-59% tests pass
- ❌ **Poor**: <40% tests pass

## Troubleshooting

### Common Issues

**Authentication Failed**
- Verify `GEE_SERVICE_ACCOUNT_KEY` secret is properly configured
- Ensure service account has access to `ee-sabitovty` project
- Check that Earth Engine API is enabled

**Data Access Limited**
- Some Sentinel-5P data may have restricted access
- Large collections may hit quota limits
- Geographic filtering helps reduce data load

**Computation Timeout**
- Computational tests have 30-second timeout
- Complex operations may need optimization
- Server-side processing is preferred for large datasets

### Local Testing Issues

**Module Import Errors**
```bash
pip install earthengine-api google-auth
```

**Authentication Required**
```bash
earthengine authenticate
```

**Project Access**
```python
ee.Initialize(project='ee-sabitovty')
```

## Integration with Analysis Workflows

This authentication testing supports:
- **High-resolution atmospheric analysis** (`high_resolution_analysis.py`)
- **Multi-year trend analysis** (`comprehensive_analytics_2017_2024.py`)
- **Scientific emission correlation** (`minimal_scientific_analysis.py`)
- **Real-time atmospheric monitoring** (`real_atmospheric_analysis.py`)

## Continuous Integration

The CI/CD pipeline ensures:
- 🔄 **Daily authentication validation**
- 🧪 **Multi-Python version compatibility**
- 📊 **Automated reporting and artifacts**
- 🔒 **Secure credential management**
- 🚀 **Ready-to-deploy validation**

## Links

- [Google Earth Engine API Documentation](https://developers.google.com/earth-engine)
- [Sentinel-5P Data Guide](https://developers.google.com/earth-engine/datasets/catalog/sentinel-5p)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

**Status**: ✅ Automated GEE authentication testing active
**Last Updated**: August 15, 2025
**Environment**: ee-sabitovty project, Sentinel-5P atmospheric data
