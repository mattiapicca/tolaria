"""
Simple health check endpoint for Vercel
"""

def handler(request):
    return {
        "statusCode": 200,
        "body": {
            "status": "healthy",
            "message": "Tolaria API is running"
        }
    }
