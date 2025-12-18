"""
KubeServe Inference Server
A generic FastAPI application that loads and serves any scikit-learn model.

The model is loaded from /model/model.joblib at startup.
Requirements are installed dynamically via start.sh if needed.
"""

import os
import joblib
import time
from typing import List, Any, Dict
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Histogram, Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="KubeServe Inference Server",
    description="Generic ML model inference endpoint",
    version="1.0.0"
)

# Add Prometheus metrics
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# Custom Prometheus metrics for prediction latency
prediction_latency_histogram = Histogram(
    'prediction_latency_ms',
    'Prediction latency in milliseconds',
    buckets=[10, 50, 100, 200, 500, 1000, 2000, 5000]  # ms buckets
)

prediction_counter = Counter(
    'predictions_total',
    'Total number of predictions',
    ['status']  # 'success' or 'error'
)

# Global model variable (loaded at startup)
model = None
model_loaded = False


class PredictionRequest(BaseModel):
    """Request schema for model predictions."""
    data: List[Any] = Field(..., description="Input data for prediction (array or list of arrays)")

    class Config:
        json_schema_extra = {
            "example": {
                "data": [[1.0, 2.0, 3.0, 4.0]]
            }
        }


class PredictionResponse(BaseModel):
    """Response schema for model predictions."""
    predictions: List[Any] = Field(..., description="Model predictions")
    model_loaded: bool = Field(..., description="Whether model was successfully loaded")


def load_model():
    """
    Load the model from /model/model.joblib.
    
    Raises:
        FileNotFoundError: If model file doesn't exist
        Exception: If model loading fails
    """
    global model, model_loaded
    
    model_path = "/model/model.joblib"
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")
    
    try:
        logger.info(f"Loading model from {model_path}")
        model = joblib.load(model_path)
        model_loaded = True
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        model_loaded = False
        raise


@app.on_event("startup")
async def startup_event():
    """Load model when application starts."""
    try:
        load_model()
    except FileNotFoundError:
        logger.warning("Model file not found at startup. Will attempt to load on first request.")
    except Exception as e:
        logger.error(f"Failed to load model at startup: {str(e)}")


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "model_loaded": model_loaded
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "KubeServe Inference Server",
        "version": "1.0.0",
        "model_loaded": model_loaded,
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "docs": "/docs"
        }
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Make predictions using the loaded model.
    
    Args:
        request: Prediction request with input data
        
    Returns:
        PredictionResponse: Model predictions
        
    Raises:
        HTTPException: If model not loaded or prediction fails
    """
    start_time = time.time()
    
    if not model_loaded or model is None:
        # Try to load model if not loaded
        try:
            load_model()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Model not available: {str(e)}"
            )
    
    try:
        # Convert input to numpy array if needed
        import numpy as np
        input_data = np.array(request.data)
        
        # Handle single sample vs batch
        if input_data.ndim == 1:
            input_data = input_data.reshape(1, -1)
        
        # Make prediction
        predictions = model.predict(input_data).tolist()
        
        # Calculate and record prediction latency
        latency_ms = (time.time() - start_time) * 1000
        prediction_latency_histogram.observe(latency_ms)
        prediction_counter.labels(status='success').inc()
        
        logger.info(f"Prediction completed in {latency_ms:.2f}ms")
        
        return PredictionResponse(
            predictions=predictions,
            model_loaded=model_loaded
        )
    except Exception as e:
        # Record error in metrics
        latency_ms = (time.time() - start_time) * 1000
        prediction_latency_histogram.observe(latency_ms)
        prediction_counter.labels(status='error').inc()
        
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)

