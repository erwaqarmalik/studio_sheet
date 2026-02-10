/**
 * Client-side background removal using TensorFlow.js and Body Segmentation
 * Fast, runs directly in the browser without server overhead
 */

// Global model cache
let backgroundRemovalModel = null;
let modelLoading = false;

/**
 * Wait for libraries to be available on window object
 */
async function waitForLibraries(maxWaitTime = 30000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < maxWaitTime) {
        if (typeof window.bodySegmentation !== 'undefined') {
            console.log('body-segmentation library is ready');
            return;
        }
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    throw new Error('Timeout waiting for body-segmentation library to load');
}

/**
 * Load the background removal model (one-time initialization)
 */
async function loadBackgroundRemovalModel() {
    if (backgroundRemovalModel) {
        console.log('Model already loaded');
        return backgroundRemovalModel;
    }
    
    if (modelLoading) {
        console.log('Model loading in progress, waiting...');
        // Wait for loading to complete
        while (modelLoading) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        return backgroundRemovalModel;
    }
    
    modelLoading = true;
    try {
        // Wait for libraries to be loaded
        console.log('Waiting for body-segmentation library...');
        await waitForLibraries();
        
        if (typeof window.bodySegmentation === 'undefined') {
            throw new Error('body-segmentation library not available after loading');
        }
        
        console.log('Loading background removal model...');
        // Load the segmentation model using the new body-segmentation package
        backgroundRemovalModel = await window.bodySegmentation.createSegmenter(
            window.bodySegmentation.SupportedModels.BodyPix,
            {
                architecture: 'MobileNetV1',
                outputStride: 16,
                multiplier: 0.75,
                quantBytes: 2,
            }
        );
        console.log('Model loaded successfully');
        return backgroundRemovalModel;
    } catch (error) {
        console.error('Failed to load model:', error);
        modelLoading = false;
        throw error;
    } finally {
        modelLoading = false;
    }
}

/**
 * Perform background removal on an image
 * @param {string} imageDataUrl - Base64 data URL of the image
 * @param {string} bgColor - Hex color for background (e.g., '#FFFFFF')
 * @param {Function} progressCallback - Optional callback for progress updates
 * @returns {Promise<string>} - Data URL of processed image
 */
async function removeBackgroundClientSide(imageDataUrl, bgColor = '#FFFFFF', progressCallback = null) {
    try {
        // Load model if not already loaded
        if (!backgroundRemovalModel) {
            if (progressCallback) progressCallback('Loading AI model...');
            await loadBackgroundRemovalModel();
        }
        
        if (progressCallback) progressCallback('Processing image...');
        
        // Load image into canvas
        const img = new Image();
        img.crossOrigin = 'anonymous';
        
        return new Promise((resolve, reject) => {
            img.onload = async () => {
                try {
                    // Create canvas and draw image
                    const canvas = document.createElement('canvas');
                    canvas.width = img.width;
                    canvas.height = img.height;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0);
                    
                    if (progressCallback) progressCallback('Segmenting person...');
                    
                    // Perform segmentation with proper config
                    // multiSegmentation: false = all people in one output
                    // segmentBodyParts: false = only foreground/background segmentation
                    const segmentationConfig = {
                        multiSegmentation: false,
                        segmentBodyParts: false,
                        flipHorizontal: false,
                        internalResolution: 'medium',
                        segmentationThreshold: 0.5,
                    };
                    
                    console.log('Calling segmentPeople with config:', segmentationConfig);
                    const people = await backgroundRemovalModel.segmentPeople(canvas, segmentationConfig);
                    
                    console.log('Segmentation result:', people);
                    
                    if (!people || !people.length) {
                        throw new Error('Invalid segmentation result: ' + JSON.stringify(people));
                    }
                    
                    if (progressCallback) progressCallback('Applying background...');
                    
                    // Create output canvas
                    const outputCanvas = document.createElement('canvas');
                    outputCanvas.width = img.width;
                    outputCanvas.height = img.height;
                    const outputCtx = outputCanvas.getContext('2d');
                    
                    // Parse background color
                    const bgRgb = hexToRgb(bgColor);
                    
                    // Fill background with chosen color
                    outputCtx.fillStyle = bgColor;
                    outputCtx.fillRect(0, 0, img.width, img.height);
                    
                    // Get image data
                    const imageData = ctx.getImageData(0, 0, img.width, img.height);
                    
                    // Get segmentation mask from first person (all people when multiSegmentation=false)
                    const segmentation = people[0];
                    
                    if (!segmentation || !segmentation.mask) {
                        throw new Error('No mask in segmentation');
                    }
                    
                    // Convert mask to ImageData
                    const maskImageData = await segmentation.mask.toImageData();
                    const maskData = maskImageData.data;
                    
                    // Create output image data
                    const outputImageData = outputCtx.createImageData(img.width, img.height);
                    
                    // Apply segmentation mask
                    // mask value 0 in red channel = background, >0 = person (green and blue are 0)
                    for (let i = 0; i < maskData.length; i += 4) {
                        const pixelIndex = i;
                        const redChannel = maskData[pixelIndex]; // Mask value in red channel
                        
                        if (redChannel === 0) {
                            // Background - use chosen color
                            outputImageData.data[pixelIndex] = bgRgb.r;
                            outputImageData.data[pixelIndex + 1] = bgRgb.g;
                            outputImageData.data[pixelIndex + 2] = bgRgb.b;
                            outputImageData.data[pixelIndex + 3] = 255;
                        } else {
                            // Foreground (person) - copy from original with alpha from mask
                            outputImageData.data[pixelIndex] = imageData.data[pixelIndex];
                            outputImageData.data[pixelIndex + 1] = imageData.data[pixelIndex + 1];
                            outputImageData.data[pixelIndex + 2] = imageData.data[pixelIndex + 2];
                            // Use alpha channel from mask for soft edges
                            outputImageData.data[pixelIndex + 3] = maskData[pixelIndex + 3];
                        }
                    }
                    
                    outputCtx.putImageData(outputImageData, 0, 0);
                    
                    if (progressCallback) progressCallback('Complete!');
                    
                    // Return as data URL
                    const resultDataUrl = outputCanvas.toDataURL('image/jpeg', 0.95);
                    resolve(resultDataUrl);
                    
                } catch (error) {
                    reject(error);
                }
            };
            
            img.onerror = () => {
                reject(new Error('Failed to load image'));
            };
            
            img.src = imageDataUrl;
        });
        
    } catch (error) {
        console.error('Background removal error:', error);
        throw error;
    }
}

/**
 * Convert hex color to RGB
 * @param {string} hex - Hex color (e.g., '#FFFFFF')
 * @returns {Object} - {r, g, b}
 */
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : { r: 255, g: 255, b: 255 };
}

/**
 * Check if client-side background removal is available
 * @returns {boolean}
 */
function isClientSideRemovalAvailable() {
    return typeof window.bodySegmentation !== 'undefined';
}

/**
 * Initialize background removal - libraries should be pre-loaded in HTML
 */
function initializeBackgroundRemoval(onReady, onError) {
    // Libraries are pre-loaded in HTML, just verify they're available
    if (typeof window.bodySegmentation !== 'undefined') {
        console.log('body-segmentation already loaded');
        if (onReady) onReady();
        return;
    }
    
    // Wait for libraries
    waitForLibraries()
        .then(() => {
            console.log('Libraries loaded');
            if (onReady) onReady();
        })
        .catch((error) => {
            console.error('Failed to load libraries:', error);
            if (onError) onError(error.message);
        });
}
