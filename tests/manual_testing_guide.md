# Manual Testing Guide - Background Remover API

## Pre-requisites

1. API server running on `http://localhost:8000`
2. Valid API key configured in environment (python -c "import secrets; print('Generated API_KEY: ' + secrets.token_urlsafe(32))")
3. Sample images for testing (JPEG, PNG)
4. Postman or curl installed

## Test Cases

python api_server.py

### 1. Health Check (No Auth Required)

```bash
curl -X GET "http://localhost:8000/api/health"
```

**Expected**: 200 OK with health status

### 2. API Documentation Access

```bash
# Open in browser
http://localhost:8000/docs
http://localhost:8000/redoc
```

**Expected**: Interactive API documentation loads

### 3. Remove Background Endpoint

```bash
# Test with valid image
curl -X POST "http://localhost:8000/api/remove-background" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@test_image.jpg"

# Test with background color
curl -X POST "http://localhost:8000/api/remove-background" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@test_image.jpg" \
  -F "background_color=white"
```

### 4. Pas Foto Endpoint

```bash
# Test basic pas foto
curl -X POST "http://localhost:8000/api/pas-foto" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@test_image.jpg" \
  -F "background_color=white" \
  -F "size=3x4"

# Test with PDF output
curl -X POST "http://localhost:8000/api/pas-foto" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@test_image.jpg" \
  -F "background_color=blue" \
  -F "size=3x4" \
  -F "pdf_count=6"
```

### 5. Error Cases Testing

```bash
# Test without API key
curl -X POST "http://localhost:8000/api/remove-background" \
  -F "file=@test_image.jpg"

# Test with invalid file type
curl -X POST "http://localhost:8000/api/remove-background" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@test_document.pdf"

# Test with oversized file
curl -X POST "http://localhost:8000/api/remove-background" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@large_image.jpg"
```

### 6. Rate Limiting Test

```bash
# Run this script to test rate limiting
for i in {1..35}; do
  curl -X GET "http://localhost:8000/api/health" &
done
wait
```

## Testing Checklist

- [ ] Health endpoint responds correctly
- [ ] API documentation is accessible
- [ ] Authentication works with valid API key
- [ ] Authentication rejects invalid API key
- [ ] Remove background processes images correctly
- [ ] Background color application works
- [ ] Pas foto creation works with all sizes
- [ ] PDF generation works correctly
- [ ] File type validation works
- [ ] File size validation works
- [ ] Rate limiting activates properly
- [ ] Error responses are properly formatted
- [ ] Response times are acceptable (&lt;5s for normal images)
- [ ] CORS headers are present for browser requests
