# 🧪 Background Remover API - Postman Testing Guide

## 📋 **File yang Dibuat**

1. **`Background_Remover_API_Collection.postman_collection.json`** - Complete API test collection
2. **`Background_Remover_API_Environment.postman_environment.json`** - Environment variables
3. **`POSTMAN_TESTING_GUIDE.md`** - Panduan testing (file ini)

## 🚀 **Cara Import ke Postman**

### **Step 1: Import Collection**

1. Buka aplikasi Postman
2. Click **Import** di top-left
3. Drag & drop file `Background_Remover_API_Collection.postman_collection.json`
4. Click **Import**

### **Step 2: Import Environment**

1. Click **Import** lagi
2. Drag & drop file `Background_Remover_API_Environment.postman_environment.json`
3. Click **Import**
4. Pilih environment "Background Remover API - Development Environment" di top-right dropdown

## 📁 **Sample Files yang Dibutuhkan**

Untuk testing yang optimal, siapkan file-file berikut di folder yang mudah diakses:

### **Required Files:**

- **`sample-image.jpg`** - Gambar normal untuk background removal (500KB - 2MB)
- **`portrait-photo.jpg`** - Foto portrait untuk passport photo testing (JPG/PNG)
- **`large-image.jpg`** - File besar untuk testing limit (mendekati 10MB)

### **File Properties yang Ideal:**

```
sample-image.jpg:
- Size: 1-3MB
- Format: JPEG/PNG
- Dimensions: 1920x1080 atau similar
- Content: Object dengan background jelas

portrait-photo.jpg:
- Size: 500KB-2MB
- Format: JPEG/PNG
- Dimensions: Minimal 800x600
- Content: Portrait dengan wajah terlihat jelas

large-image.jpg:
- Size: 8-10MB (untuk test file limit)
- Format: JPEG/PNG
- High resolution image
```

## 🧪 **Test Collection Overview**

### **1. 🏥 Health Checks**

- **Root Health Check** - Test endpoint "/"
- **Detailed Health Check** - Test endpoint "/health"

### **2. 🎯 Background Removal API**

- **Remove Background - Success** - Basic background removal
- **Remove Background - With Background Color** - Apply solid color
- **Remove Background - Hex Color** - Test hex color format

### **3. 📸 Passport Photo API**

- **Create Passport Photo - Default** - Default 3x4 white background
- **Create Passport Photo - Custom Settings** - Custom size, color, PDF count
- **Create Passport Photo - All Sizes Test** - Test different size formats

### **4. 🔐 Authentication Tests**

- **No API Key - Should Fail** - Test without authorization
- **Invalid API Key - Should Fail** - Test with wrong API key

### **5. 🚨 Error Handling Tests**

- **No File Upload - Should Fail** - Test missing file
- **Invalid Color Format - Should Fail** - Test invalid color
- **Invalid PDF Count - Should Fail** - Test PDF count > 50

### **6. ⚡ Performance Tests**

- **Large File Upload Test** - Test file size limits
- **Rate Limit Test** - Test 30 requests/minute limit

## 🎯 **Systematic Testing Workflow**

### **Phase 1: Basic Functionality** ✅

```
1. Start API server: python run_server.py
2. Run Health Checks folder
3. Test Remove Background - Success
4. Test Passport Photo - Default
```

### **Phase 2: Feature Testing** 🧪

```
1. Test all Background Removal variations
2. Test all Passport Photo variations
3. Verify different color formats work
4. Test different photo sizes
```

### **Phase 3: Security & Error Handling** 🔒

```
1. Run Authentication Tests folder
2. Run Error Handling Tests folder
3. Verify all error responses are properly formatted
4. Check API key validation works
```

### **Phase 4: Performance & Limits** ⚡

```
1. Test large file uploads
2. Test rate limiting (run Rate Limit Test multiple times)
3. Verify response times are acceptable
4. Test concurrent requests
```

## 📊 **Expected Results**

### **Success Responses (200 OK):**

```json
{
	"success": true,
	"message": "Background removed successfully",
	"data": {
		"processed_image": "base64-encoded-string",
		"original_filename": "sample-image.jpg",
		"processing_info": {
			"background_applied": true,
			"background_color": "white"
		}
	},
	"processing_time": 2.34
}
```

### **Error Responses:**

```json
{
	"success": false,
	"message": "Invalid or missing API key",
	"error_code": "INVALID_API_KEY",
	"details": {
		"required_format": "Authorization: Bearer YOUR_API_KEY"
	}
}
```

## 🔧 **Troubleshooting**

### **Common Issues:**

1. **401 Unauthorized**

   - Check API key in environment variables
   - Verify Authorization header format

2. **404 Not Found**

   - Ensure API server is running on localhost:8000
   - Check endpoint URLs are correct

3. **422 Unprocessable Entity**

   - Verify file is attached in form-data
   - Check file format (JPG/PNG only)

4. **Rate Limit Exceeded (429)**
   - Wait 1 minute before retrying
   - This is expected behavior after 30 requests

## 📈 **Advanced Testing Tips**

### **Custom Test Scripts:**

Collection sudah include automatic test scripts yang akan:

- Validate response status codes
- Check response structure
- Verify processing times
- Log detailed information

### **Environment Switching:**

Buat environment baru untuk production testing:

```json
{
	"BASE_URL": "https://your-production-domain.com",
	"API_KEY": "your-production-api-key"
}
```

### **Batch Testing:**

Use Collection Runner untuk menjalankan semua tests sekaligus:

1. Click Collection name
2. Click "Run"
3. Select environment
4. Click "Run Background Remover API"

## 🎉 **Success Indicators**

API testing berhasil jika:

- ✅ All health checks pass
- ✅ File uploads process successfully
- ✅ Authentication works properly
- ✅ Error handling returns proper error codes
- ✅ Rate limiting functions correctly
- ✅ Response times < 30 seconds
- ✅ All image processing features work

Selamat testing, Rio! 🚀
