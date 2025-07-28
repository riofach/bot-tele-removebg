# Background Remover API Documentation

## 🚀 **Quick Start for Next.js Integration**

### Base URLs

- **Development**: `http://localhost:8000`
- **Production**: `https://your-api-domain.com`

### Authentication

All endpoints require API key in Authorization header:

```javascript
headers: {
  'Authorization': 'Bearer YOUR_API_KEY'
}
```

---

## 📋 **API Endpoints**

### 1. **Health Check**

```
GET /api/health
```

**Purpose**: Check API server status (no authentication required)

**Response**:

```json
{
	"success": true,
	"message": "Background Remover API is healthy",
	"service": "background-remover-api",
	"version": "1.0.0",
	"status": "operational"
}
```

---

### 2. **Remove Background**

```
POST /api/remove-background
```

**Purpose**: Remove background from uploaded image

**Parameters**:

- `file` (required): Image file (multipart/form-data)
- `background_color` (optional): Color name or hex code (#ff0000)

**Supported File Types**: JPEG, PNG, JPG
**Max File Size**: 10MB

**Response**: Returns processed image file with headers:

```
Content-Type: image/png
X-Processing-Time: 2.341
X-Original-Filename: original.jpg
```

---

### 3. **Passport Photo Creator**

```
POST /api/pas-foto
```

**Purpose**: Create passport photos with custom size and background

**Parameters**:

- `file` (required): Image file (multipart/form-data)
- `background_color` (optional): `white`, `blue`, `red`, or hex code
- `size` (optional): `2x3`, `3x4`, `4x6`, `2R`, `3R`, `4R`, `5R`
- `pdf_count` (optional): Number of photos in PDF layout (1-50)

**Response Options**:

- Single photo: Returns PNG image file
- Multiple photos: Returns PDF file with multiple photos

**Response Headers**:

```
X-Processing-Time: 3.124
X-Photo-Size: 3x4
X-Background-Color: white
X-Photo-Count: 6 (if PDF)
```

---

## 🔧 **Next.js Integration Examples**

### **1. API Client Setup**

```javascript
// utils/backgroundRemoverAPI.js
class BackgroundRemoverAPI {
	constructor(baseURL, apiKey) {
		this.baseURL = baseURL;
		this.apiKey = apiKey;
	}

	async removeBackground(file, backgroundColor = null) {
		const formData = new FormData();
		formData.append('file', file);

		if (backgroundColor) {
			formData.append('background_color', backgroundColor);
		}

		try {
			const response = await fetch(`${this.baseURL}/api/remove-background`, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${this.apiKey}`,
				},
				body: formData,
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail?.error || 'Failed to remove background');
			}

			// Return blob for image download
			return await response.blob();
		} catch (error) {
			console.error('Background removal failed:', error);
			throw error;
		}
	}

	async createPasPhoto(file, options = {}) {
		const formData = new FormData();
		formData.append('file', file);

		// Default options
		const { backgroundColor = 'white', size = '3x4', pdfCount = 1 } = options;

		formData.append('background_color', backgroundColor);
		formData.append('size', size);
		formData.append('pdf_count', pdfCount.toString());

		try {
			const response = await fetch(`${this.baseURL}/api/pas-foto`, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${this.apiKey}`,
				},
				body: formData,
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail?.error || 'Failed to create passport photo');
			}

			return {
				blob: await response.blob(),
				processingTime: response.headers.get('X-Processing-Time'),
				photoSize: response.headers.get('X-Photo-Size'),
				backgroundColor: response.headers.get('X-Background-Color'),
				photoCount: response.headers.get('X-Photo-Count'),
			};
		} catch (error) {
			console.error('Passport photo creation failed:', error);
			throw error;
		}
	}

	async checkHealth() {
		try {
			const response = await fetch(`${this.baseURL}/api/health`);
			return await response.json();
		} catch (error) {
			console.error('Health check failed:', error);
			throw error;
		}
	}
}

// Initialize API client
const api = new BackgroundRemoverAPI(
	process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
	process.env.NEXT_PUBLIC_API_KEY
);

export default api;
```

### **2. React Component Example**

```jsx
// components/BackgroundRemover.jsx
import { useState } from 'react';
import api from '@/utils/backgroundRemoverAPI';

export default function BackgroundRemover() {
	const [file, setFile] = useState(null);
	const [result, setResult] = useState(null);
	const [loading, setLoading] = useState(false);
	const [backgroundColor, setBackgroundColor] = useState('');

	const handleFileChange = (e) => {
		const selectedFile = e.target.files[0];
		if (selectedFile && selectedFile.type.startsWith('image/')) {
			setFile(selectedFile);
		} else {
			alert('Please select a valid image file');
		}
	};

	const handleRemoveBackground = async () => {
		if (!file) return;

		setLoading(true);
		try {
			const resultBlob = await api.removeBackground(file, backgroundColor || null);

			// Create download URL
			const url = URL.createObjectURL(resultBlob);
			setResult(url);
		} catch (error) {
			alert(`Error: ${error.message}`);
		} finally {
			setLoading(false);
		}
	};

	const downloadResult = () => {
		if (result) {
			const a = document.createElement('a');
			a.href = result;
			a.download = `removed_bg_${file.name}`;
			a.click();
		}
	};

	return (
		<div className="p-6 max-w-md mx-auto bg-white rounded-lg shadow-lg">
			<h2 className="text-2xl font-bold mb-4">Background Remover</h2>

			<div className="mb-4">
				<label className="block text-sm font-medium mb-2">Select Image:</label>
				<input
					type="file"
					accept="image/*"
					onChange={handleFileChange}
					className="w-full p-2 border rounded"
				/>
			</div>

			<div className="mb-4">
				<label className="block text-sm font-medium mb-2">Background Color (optional):</label>
				<input
					type="text"
					value={backgroundColor}
					onChange={(e) => setBackgroundColor(e.target.value)}
					placeholder="e.g., white, #ff0000"
					className="w-full p-2 border rounded"
				/>
			</div>

			<button
				onClick={handleRemoveBackground}
				disabled={!file || loading}
				className="w-full bg-blue-500 text-white p-2 rounded disabled:bg-gray-300"
			>
				{loading ? 'Processing...' : 'Remove Background'}
			</button>

			{result && (
				<div className="mt-4">
					<img src={result} alt="Result" className="w-full rounded" />
					<button
						onClick={downloadResult}
						className="w-full mt-2 bg-green-500 text-white p-2 rounded"
					>
						Download Result
					</button>
				</div>
			)}
		</div>
	);
}
```

### **3. Passport Photo Component**

```jsx
// components/PasPhotoCreator.jsx
import { useState } from 'react';
import api from '@/utils/backgroundRemoverAPI';

export default function PasPhotoCreator() {
	const [file, setFile] = useState(null);
	const [options, setOptions] = useState({
		backgroundColor: 'white',
		size: '3x4',
		pdfCount: 1,
	});
	const [result, setResult] = useState(null);
	const [loading, setLoading] = useState(false);

	const sizes = ['2x3', '3x4', '4x6', '2R', '3R', '4R', '5R'];
	const colors = ['white', 'blue', 'red'];

	const handleCreate = async () => {
		if (!file) return;

		setLoading(true);
		try {
			const response = await api.createPasPhoto(file, options);

			const url = URL.createObjectURL(response.blob);
			setResult({
				url,
				...response,
			});
		} catch (error) {
			alert(`Error: ${error.message}`);
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="p-6 max-w-md mx-auto bg-white rounded-lg shadow-lg">
			<h2 className="text-2xl font-bold mb-4">Passport Photo Creator</h2>

			<div className="mb-4">
				<label className="block text-sm font-medium mb-2">Select Image:</label>
				<input
					type="file"
					accept="image/*"
					onChange={(e) => setFile(e.target.files[0])}
					className="w-full p-2 border rounded"
				/>
			</div>

			<div className="mb-4">
				<label className="block text-sm font-medium mb-2">Background Color:</label>
				<select
					value={options.backgroundColor}
					onChange={(e) => setOptions({ ...options, backgroundColor: e.target.value })}
					className="w-full p-2 border rounded"
				>
					{colors.map((color) => (
						<option key={color} value={color}>
							{color}
						</option>
					))}
				</select>
			</div>

			<div className="mb-4">
				<label className="block text-sm font-medium mb-2">Photo Size:</label>
				<select
					value={options.size}
					onChange={(e) => setOptions({ ...options, size: e.target.value })}
					className="w-full p-2 border rounded"
				>
					{sizes.map((size) => (
						<option key={size} value={size}>
							{size}
						</option>
					))}
				</select>
			</div>

			<div className="mb-4">
				<label className="block text-sm font-medium mb-2">PDF Count:</label>
				<input
					type="number"
					min="1"
					max="50"
					value={options.pdfCount}
					onChange={(e) => setOptions({ ...options, pdfCount: parseInt(e.target.value) })}
					className="w-full p-2 border rounded"
				/>
			</div>

			<button
				onClick={handleCreate}
				disabled={!file || loading}
				className="w-full bg-purple-500 text-white p-2 rounded disabled:bg-gray-300"
			>
				{loading ? 'Creating...' : 'Create Passport Photo'}
			</button>

			{result && (
				<div className="mt-4">
					<img src={result.url} alt="Passport Photo" className="w-full rounded" />
					<div className="mt-2 text-sm text-gray-600">
						<p>Processing Time: {result.processingTime}s</p>
						<p>Size: {result.photoSize}</p>
						<p>Background: {result.backgroundColor}</p>
						{result.photoCount && <p>Photos in PDF: {result.photoCount}</p>}
					</div>
					<a
						href={result.url}
						download={`passport_photo_${options.size}_${Date.now()}.${
							result.photoCount > 1 ? 'pdf' : 'png'
						}`}
						className="w-full mt-2 bg-green-500 text-white p-2 rounded block text-center"
					>
						Download Result
					</a>
				</div>
			)}
		</div>
	);
}
```

---

## ⚙️ **Environment Configuration**

### **Next.js Environment Variables**

Create `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=your-api-key-here
```

### **Production Configuration**

```env
NEXT_PUBLIC_API_URL=https://your-production-api.com
NEXT_PUBLIC_API_KEY=your-production-api-key
```

---

## 🚨 **Error Handling**

### **Common Error Responses**

#### Authentication Error (401)

```json
{
	"detail": {
		"success": false,
		"error": "Invalid API key",
		"error_code": "INVALID_API_KEY"
	}
}
```

#### Rate Limit Error (429)

```json
{
	"detail": {
		"success": false,
		"error": "Rate limit exceeded",
		"error_code": "RATE_LIMIT_EXCEEDED",
		"details": {
			"remaining_requests": 0,
			"limit_per_minute": 30
		}
	}
}
```

#### File Validation Error (400)

```json
{
	"detail": {
		"success": false,
		"error": "File type 'application/pdf' not allowed",
		"error_code": "INVALID_FILE_TYPE",
		"details": {
			"allowed_types": ["image/jpeg", "image/png", "image/jpg"]
		}
	}
}
```

#### File Size Error (413)

```json
{
	"detail": {
		"success": false,
		"error": "File too large. Maximum size: 10MB",
		"error_code": "FILE_TOO_LARGE",
		"details": {
			"max_size_mb": 10,
			"received_size_mb": 15.2
		}
	}
}
```

---

## 🔒 **Security Best Practices**

1. **API Key Protection**:

   - Store API key in environment variables
   - Never expose API key in client-side code
   - Use server-side API routes in Next.js when possible

2. **File Upload Security**:

   - Validate file types on client-side before upload
   - Handle file size limits gracefully
   - Show progress indicators for large uploads

3. **Error Handling**:
   - Implement proper error boundaries
   - Show user-friendly error messages
   - Log errors for debugging

---

## 📊 **Performance Optimization**

1. **File Optimization**:

   - Compress images before upload
   - Use appropriate image formats
   - Implement client-side image resizing for very large files

2. **User Experience**:

   - Show loading states during processing
   - Implement progress indicators
   - Cache results when appropriate

3. **Rate Limiting**:
   - Implement client-side rate limiting
   - Show remaining requests to users
   - Handle rate limit errors gracefully

---

## 🧪 **Testing Your Integration**

### **1. Basic Connectivity Test**

```javascript
// Test API connectivity
const testConnection = async () => {
	try {
		const health = await api.checkHealth();
		console.log('API Status:', health);
	} catch (error) {
		console.error('API connection failed:', error);
	}
};
```

### **2. File Upload Test**

```javascript
// Test with a small image
const testFileUpload = async () => {
	const canvas = document.createElement('canvas');
	canvas.width = 100;
	canvas.height = 100;

	canvas.toBlob(async (blob) => {
		try {
			const result = await api.removeBackground(blob);
			console.log('Upload successful, result size:', result.size);
		} catch (error) {
			console.error('Upload failed:', error);
		}
	}, 'image/jpeg');
};
```

---

## 📞 **Support & Troubleshooting**

### **Common Issues**

1. **CORS Errors**:

   - Ensure API server is running with correct CORS configuration
   - Check that your domain is in allowed origins

2. **File Upload Fails**:

   - Verify file size and type restrictions
   - Check API key authentication

3. **Slow Response Times**:
   - Large images take longer to process
   - Consider implementing timeout handling

### **Debug Mode**

Enable debug mode in your API client:

```javascript
const api = new BackgroundRemoverAPI(baseURL, apiKey, { debug: true });
```

This will log all API requests and responses to the console.

---

## 🚀 **Integration Checklist**

- [ ] API client setup complete
- [ ] Environment variables configured
- [ ] Authentication working
- [ ] File upload component implemented
- [ ] Error handling implemented
- [ ] Loading states added
- [ ] Result download functionality working
- [ ] CORS configuration verified
- [ ] Rate limiting handled
- [ ] Production deployment tested

**Happy coding! 🎉**
