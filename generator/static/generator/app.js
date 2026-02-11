document.addEventListener("DOMContentLoaded", () => {

    /* =====================================
       LOAD CONFIG DEFAULTS
    ===================================== */
    const configEl = document.getElementById("passport-config-data");
    if (!configEl) {
        console.error("passport-config-data not found");
        return;
    }
    const CONFIG = JSON.parse(configEl.textContent);


    /* =====================================
       LOAD PAPER SIZES
    ===================================== */
    const jsonEl = document.getElementById("paper-sizes-data");
    if (!jsonEl) {
        console.error("paper-sizes-data not found");
        return;
    }
    const PAPER_SIZES = JSON.parse(jsonEl.textContent);

    /* =====================================
       LOAD PHOTO SIZES
    ===================================== */
    const photoSizesEl = document.getElementById("photo-sizes-data");
    if (!photoSizesEl) {
        console.error("photo-sizes-data not found");
        return;
    }
    const PHOTO_SIZES = JSON.parse(photoSizesEl.textContent);


    /* =====================================
       CONSTANTS & DYNAMIC PHOTO DIMENSIONS
    ===================================== */
    let PHOTO_W;
    let PHOTO_H;

    /* =====================================
       ELEMENTS
    ===================================== */
    const input = document.getElementById("photoInput");
    const preview = document.getElementById("preview");
    const form = document.getElementById("passportForm");
    const submitBtn = document.getElementById("submitBtn");
    const submitText = document.getElementById("submitText");
    const submitLoader = document.getElementById("submitLoader");
    const uploadZone = document.getElementById("uploadZone");

    // Debug: Check if critical elements exist




    
    if (!input || !preview || !uploadZone) {
        console.error('Missing critical elements!');
        if (!input) console.error('photoInput not found');
        if (!preview) console.error('preview not found');
        if (!uploadZone) console.error('uploadZone not found');
        return;
    }

    const paperSize = document.getElementById("paperSize");
    const orientation = document.getElementById("orientation");
    const margin = document.getElementById("margin");
    const colGap = document.getElementById("colGap");
    const rowGap = document.getElementById("rowGap");
    const stats = document.getElementById("stats");
    const statRows = document.getElementById("statRows");
    const statCols = document.getElementById("statCols");
    const statTotal = document.getElementById("statTotal");

    const defaultPhotoSize = document.getElementById("defaultPhotoSize");
    const customSizeContainer = document.getElementById("customSizeContainer");
    const customWidthInput = document.getElementById("customWidth");
    const customHeightInput = document.getElementById("customHeight");
    const uploadSizeHint = document.getElementById("uploadSizeHint");

    // Debug: Check if elements exist
    if (!defaultPhotoSize) console.warn("defaultPhotoSize not found");
    if (!customSizeContainer) console.warn("customSizeContainer not found");
    if (!customWidthInput) console.warn("customWidthInput not found");
    if (!customHeightInput) console.warn("customHeightInput not found");
    if (!uploadSizeHint) console.warn("uploadSizeHint not found");

    /* =====================================
       CROP MODAL ELEMENTS
    ===================================== */
    const cropModal = document.getElementById("cropModal");
    const cropImage = document.getElementById("cropImage");
    const cropModalClose = document.getElementById("cropModalClose");
    const cropCancel = document.getElementById("cropCancel");
    const cropApply = document.getElementById("cropApply");
    const cropAspectRatio = document.getElementById("cropAspectRatio");
    
    // Background removal modal elements
    const bgRemovalModal = document.getElementById("bgRemovalModal");
    const bgRemovalImage = document.getElementById("bgRemovalImage");
    const bgRemovalModalClose = document.getElementById("bgRemovalModalClose");
    const bgRemovalCancel = document.getElementById("bgRemovalCancel");
    const bgRemovalApply = document.getElementById("bgRemovalApply");
    const bgRemovalColorPicker = document.getElementById("bgRemovalColorPicker");
    const bgColorPreview = document.getElementById("bgColorPreview");
    
    let cropper = null;
    let currentCropIndex = null;
    let currentCropModalUrl = null; // Store object URL for modal cleanup
    let currentBgRemovalIndex = null; // Track which file is being processed for BG removal
    let currentBgRemovalDataUrl = null; // Store image data URL for BG removal
    let currentPhotoSize = 'passport'; // Track current photo size for crop modal

    /* =====================================
       FILE MANAGEMENT
    ===================================== */
    // Store files with their data URLs for preview and deletion
    let fileList = [];
    let fileDataMap = new Map(); // Map to store file data URLs
    let croppedFilesMap = new Map(); // Map to store cropped File objects (index -> File)
    let bgRemovedFilesMap = new Map(); // Map to store background-removed File objects (index -> File)
    let bgRemovedMap = new Map(); // Map to track which images have background removed (index -> true/false)
    let objectUrlMap = new Map(); // Map to store object URLs for cleanup (index -> objectURL)

    /* =====================================
       DRAG & DROP FUNCTIONALITY
    ===================================== */
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadZone.addEventListener(eventName, () => {
            uploadZone.classList.add('drag-over');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, () => {
            uploadZone.classList.remove('drag-over');
        }, false);
    });

    uploadZone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        addFiles(Array.from(files));
    }

    // Fix: Only trigger file input when clicking on the upload zone, not on the browse link
    uploadZone.addEventListener('click', (e) => {
        // Don't trigger if clicking on the browse link (it has its own handler)
        if (e.target.closest('.browse-link')) {
            return;
        }
        // Only trigger if clicking on the upload zone itself
        if (e.target === uploadZone || e.target.closest('.upload-content')) {
            input.click();
        }
    }, false);

    // Handle browse link click separately
    const browseLink = uploadZone.querySelector('.browse-link');
    if (browseLink) {
        browseLink.addEventListener('click', (e) => {
            e.stopPropagation();
            input.click();
        });
    }

    /* =====================================
       APPLY DEFAULTS FROM CONFIG
    ===================================== */
    paperSize.value = CONFIG.default_paper_size;
    orientation.value = CONFIG.default_orientation;

    margin.value = CONFIG.default_margin_cm;
    colGap.value = CONFIG.default_col_gap_cm;
    rowGap.value = CONFIG.default_row_gap_cm;

    const cutLineTypeEl = document.querySelector('[name="cut_line_type"]');
    if (cutLineTypeEl) {
        cutLineTypeEl.value = CONFIG.default_cut_lines ? "full" : "none";
    }

    document.querySelector('[name="output_type"]').value =
        CONFIG.default_output_type;

    /* =====================================
       PHOTO SIZE SELECTION HANDLER
    ===================================== */
    function updatePhotoSize() {
        currentPhotoSize = defaultPhotoSize.value;
        let customWidth, customHeight;
        
        if (currentPhotoSize === 'custom') {
            // Show custom size inputs
            customSizeContainer.style.display = 'block';
            
            // Get values or use defaults
            customWidth = parseFloat(customWidthInput.value) || 3.5;
            customHeight = parseFloat(customHeightInput.value) || 4.5;
            
            // Set default values if empty
            if (!customWidthInput.value) customWidthInput.value = '3.5';
            if (!customHeightInput.value) customHeightInput.value = '4.5';
            
            PHOTO_W = customWidth;
            PHOTO_H = customHeight;
        } else {
            // Hide custom size inputs
            customSizeContainer.style.display = 'none';
            const sizeInfo = PHOTO_SIZES[currentPhotoSize];
            if (sizeInfo) {
                PHOTO_W = sizeInfo.width;
                PHOTO_H = sizeInfo.height;
            }
        }
        
        // Update upload hint
        if (uploadSizeHint) {
            uploadSizeHint.textContent = `Auto-cropped to ${PHOTO_W}×${PHOTO_H} cm`;
        }
        
        calculateGrid();

    }

    defaultPhotoSize.addEventListener('change', updatePhotoSize);
    customWidthInput.addEventListener('input', updatePhotoSize);
    customHeightInput.addEventListener('input', updatePhotoSize);






    
    // Initialize photo size
    updatePhotoSize();

    /* =====================================
       BACKGROUND REMOVAL
    ===================================== */
    async function removeBackgroundAPI(imageDataUrl, bgColor) {
        try {
            const formData = new FormData();
            formData.append('image', imageDataUrl);
            formData.append('bg_color', bgColor);
            
            const response = await fetch('/api/remove-background/', {
                method: 'POST',
                body: formData,
                signal: AbortSignal.timeout(120000) // 2 minute timeout
            });
            
            if (!response.ok) {
                let errorMsg = 'Background removal failed';
                try {
                    const error = await response.json();
                    errorMsg = error.error || errorMsg;
                } catch (e) {
                    if (response.status === 503) {
                        errorMsg = 'Background removal service is unavailable. Please try again in a moment.';
                    } else if (response.status === 502 || response.status === 504) {
                        errorMsg = 'Server error. Please try again later.';
                    }
                }
                throw new Error(errorMsg);
            }
            
            const result = await response.json();
            if (!result.success && !result.task_id) {
                throw new Error(result.error || 'Background removal failed');
            }

            if (result.task_id) {
                return await waitForBackgroundTask(result.task_id);
            }

            return result.image;
        } catch (error) {
            console.error('API error:', error);
            throw error;
        }
    }

    async function waitForBackgroundTask(taskId) {
        const maxAttempts = 60;
        const delayMs = 2000;

        for (let attempt = 0; attempt < maxAttempts; attempt++) {
            const res = await fetch(`/api/remove-background/status/${taskId}/`);
            const data = await res.json();

            if (data.status === 'completed' && data.image) {
                return data.image;
            }

            if (data.status === 'failed') {
                throw new Error(data.error || 'Background removal failed');
            }

            await new Promise(resolve => setTimeout(resolve, delayMs));
        }

        throw new Error('Background removal timed out. Please try again.');
    }

    /* =====================================
       HELPERS
    ===================================== */

    function safeNum(el, fallback) {
        const v = parseFloat(el.value);
        return Number.isFinite(v) ? v : fallback;
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    /* =====================================
       FILE MANAGEMENT FUNCTIONS
    ===================================== */
    function addFiles(newFiles) {

        newFiles.forEach(file => {
            // Check file size
            const maxSize = 10 * 1024 * 1024; // 10MB
            if (file.size > maxSize) {
                alert(`File "${file.name}" is too large. Maximum size is 10MB.`);
                return;
            }

            // Check if file already exists (by name and size)
            const exists = fileList.some(f => f.name === file.name && f.size === file.size);
            if (exists) {

                return; // Skip duplicate files
            }

            fileList.push(file);


            // Read file and store data URL
            const reader = new FileReader();
            reader.onload = e => {

                fileDataMap.set(file.name + file.size, e.target.result);

                renderPreview();
                updateFileInput();
            };
            reader.onerror = err => {
                console.error('Error reading file:', file.name, err);
            };
            reader.readAsDataURL(file);
        });
    }

    function removeFile(fileIndex) {
        const file = fileList[fileIndex];
        if (file) {
            fileList.splice(fileIndex, 1);
            fileDataMap.delete(file.name + file.size);
            croppedFilesMap.delete(fileIndex);
            bgRemovedFilesMap.delete(fileIndex);
            bgRemovedMap.delete(fileIndex);
            
            // Update indices in croppedFilesMap
            const newCroppedMap = new Map();
            croppedFilesMap.forEach((value, key) => {
                if (key < fileIndex) {
                    newCroppedMap.set(key, value);
                } else if (key > fileIndex) {
                    newCroppedMap.set(key - 1, value);
                }
            });
            croppedFilesMap = newCroppedMap;
            
            // Update indices in bgRemovedFilesMap
            const newBgRemovedFilesMap = new Map();
            bgRemovedFilesMap.forEach((value, key) => {
                if (key < fileIndex) {
                    newBgRemovedFilesMap.set(key, value);
                } else if (key > fileIndex) {
                    newBgRemovedFilesMap.set(key - 1, value);
                }
            });
            bgRemovedFilesMap = newBgRemovedFilesMap;
            
            // Update indices in bgRemovedMap
            const newBgRemovedMap = new Map();
            bgRemovedMap.forEach((value, key) => {
                if (key < fileIndex) {
                    newBgRemovedMap.set(key, value);
                } else if (key > fileIndex) {
                    newBgRemovedMap.set(key - 1, value);
                }
            });
            bgRemovedMap = newBgRemovedMap;
            
            renderPreview();
            updateFileInput();
        }
    }

    function renderPreview() {


        
        // Clean up previous object URLs
        objectUrlMap.forEach(url => URL.revokeObjectURL(url));
        objectUrlMap.clear();
        
        preview.innerHTML = "";
        fileList.forEach((file, index) => {

            // Use cropped image first, then background-removed, then original
            let dataUrl;
            if (croppedFilesMap.has(index)) {
                const objectUrl = URL.createObjectURL(croppedFilesMap.get(index));
                objectUrlMap.set(index, objectUrl);
                dataUrl = objectUrl;

            } else if (bgRemovedFilesMap.has(index)) {
                const objectUrl = URL.createObjectURL(bgRemovedFilesMap.get(index));
                objectUrlMap.set(index, objectUrl);
                dataUrl = objectUrl;

            } else {
                dataUrl = fileDataMap.get(file.name + file.size);

            }
            if (!dataUrl) {
                console.warn('No dataUrl for file:', file.name, 'skipping');
                return; // Skip if data URL not ready yet
            }

            const card = document.createElement("div");
            card.className = "preview-card";
            const isCropped = croppedFilesMap.has(index);
            const isBgRemoved = bgRemovedMap.get(index) || false;
            card.innerHTML = `
                <button type="button" class="delete-btn" data-index="${index}" aria-label="Delete photo">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
                ${isCropped ? '<span class="crop-badge">✓ Cropped</span>' : ''}
                ${isBgRemoved ? '<span class="crop-badge bg-removed-badge">✓ BG Removed</span>' : ''}
                <img src="${dataUrl}" alt="${file.name}">
                <div class="preview-actions">
                    <button type="button" class="crop-btn" data-index="${index}" aria-label="Crop photo">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                            <line x1="9" y1="3" x2="9" y2="21"></line>
                            <line x1="3" y1="9" x2="21" y2="9"></line>
                        </svg>
                        <span>Crop</span>
                    </button>
                    <button type="button" class="bg-remove-btn" data-index="${index}" aria-label="Remove background">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                            <path d="M2 17l10 5 10-5"/>
                            <path d="M2 12l10 5 10-5"/>
                        </svg>
                        <span>Remove BG</span>
                    </button>
                </div>
                <div class="file-info">${formatFileSize(file.size)}</div>
                <input type="number"
                       name="copies[]"
                       min="1"
                       value="${CONFIG.default_copies}"
                       placeholder="Copies">
            `;
            preview.appendChild(card);
        });

        // Add delete button event listeners
        preview.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = parseInt(btn.getAttribute('data-index'));
                removeFile(index);
            });
        });

        // Add crop button event listeners
        preview.querySelectorAll('.crop-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = parseInt(btn.getAttribute('data-index'));
                openCropModal(index);
            });
        });
        
        // Add background removal button event listeners
        preview.querySelectorAll('.bg-remove-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = parseInt(btn.getAttribute('data-index'));
                openBgRemovalModal(index);
            });
        });
    }

    /* =====================================
       FILE INPUT CHANGE HANDLER
    ===================================== */
    input.addEventListener("change", (e) => {


        // Prevent double-triggering by checking if files are already being processed
        if (e.target.files && e.target.files.length > 0) {

            addFiles(Array.from(e.target.files));
            // Reset input value to allow selecting the same file again if needed
            e.target.value = '';
        } else {
            console.warn('No files in input.files');
        }
    });

    /* =====================================
       GRID CALCULATION
    ===================================== */
    function calculateGrid() {
        const key = paperSize.value;
        if (!PAPER_SIZES[key]) return;

        let pw = Number(PAPER_SIZES[key].width_cm);
        let ph = Number(PAPER_SIZES[key].height_cm);

        if (orientation.value === "landscape") {
            [pw, ph] = [ph, pw];
        }

        const m = safeNum(margin, CONFIG.default_margin_cm);
        const cg = safeNum(colGap, CONFIG.default_col_gap_cm);
        const rg = safeNum(rowGap, CONFIG.default_row_gap_cm);

        const cols = Math.max(
            1,
            Math.floor((pw - 2 * m + cg) / (PHOTO_W + cg))
        );
        const rows = Math.max(
            1,
            Math.floor((ph - 2 * m + rg) / (PHOTO_H + rg))
        );

        const total = rows * cols;

        // Update stats with animation
        if (statRows) statRows.textContent = rows;
        if (statCols) statCols.textContent = cols;
        if (statTotal) statTotal.textContent = total;
    }

    [paperSize, orientation, margin, colGap, rowGap]
        .forEach(el => el.addEventListener("change", calculateGrid));

    calculateGrid(); // run once with config defaults

    /* =====================================
       CROP MODAL FUNCTIONALITY
    ===================================== */
    function openCropModal(fileIndex) {
        const file = fileList[fileIndex];
        if (!file) return;

        currentCropIndex = fileIndex;
        const originalDataUrl = fileDataMap.get(file.name + file.size);
        
        // Clean up previous modal object URL if exists
        if (currentCropModalUrl) {
            URL.revokeObjectURL(currentCropModalUrl);
            currentCropModalUrl = null;
        }

        // Destroy previous cropper if exists
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }

        // Use cropped image first, then background-removed, then original
        let imageUrl;
        if (croppedFilesMap.has(fileIndex)) {
            currentCropModalUrl = URL.createObjectURL(croppedFilesMap.get(fileIndex));
            imageUrl = currentCropModalUrl;
        } else if (bgRemovedFilesMap.has(fileIndex)) {
            currentCropModalUrl = URL.createObjectURL(bgRemovedFilesMap.get(fileIndex));
            imageUrl = currentCropModalUrl;
        } else {
            imageUrl = originalDataUrl;
        }

        // Show modal first
        cropModal.classList.add('active');
        
        // Update crop aspect ratio display
        if (cropAspectRatio) {
            const sizeLabel = currentPhotoSize === 'custom' 
                ? `Custom (${PHOTO_W}×${PHOTO_H} cm)`
                : PHOTO_SIZES[currentPhotoSize]?.label || `${PHOTO_W}×${PHOTO_H} cm`;
            cropAspectRatio.textContent = sizeLabel;
        }
        
        // Set image source and wait for it to load before initializing cropper
        cropImage.src = '';
        
        // Remove any existing onload handlers
        cropImage.onload = null;
        
        // Disable Apply button while loading
        cropApply.disabled = true;
        cropApply.textContent = 'Loading...';
        
        // Check if Cropper.js is loaded
        if (typeof Cropper === 'undefined') {
            console.error('Cropper.js library not loaded');
            alert('Crop tool library failed to load. Please refresh the page and try again.');
            cropApply.disabled = false;
            cropApply.textContent = 'Apply Crop';
            closeCropModal();
            return;
        }
        
        // Wait for image to load before initializing cropper
        const initCropper = function() {
            // Verify image is loaded and has dimensions
            if (!cropImage.complete || cropImage.naturalWidth === 0) {
                console.error('Image not fully loaded');
                alert('Image failed to load. Please try again.');
                cropApply.disabled = false;
                cropApply.textContent = 'Apply Crop';
                return;
            }
            
            // Verify container is visible and has dimensions
            const container = cropImage.parentElement;
            const modalContent = cropModal.querySelector('.crop-modal-content');
            if (!modalContent || container.offsetWidth === 0 || container.offsetHeight === 0) {
                console.warn('Container not ready, retrying...', {
                    containerWidth: container.offsetWidth,
                    containerHeight: container.offsetHeight,
                    modalVisible: cropModal.classList.contains('active')
                });
                setTimeout(initCropper, 100);
                return;
            }
            
            // Calculate aspect ratio using current photo size
            const aspectRatio = PHOTO_W / PHOTO_H;
            
            // Destroy any existing cropper first
            if (cropper) {
                try {
                    cropper.destroy();
                } catch (e) {
                    console.warn('Error destroying previous cropper:', e);
                }
                cropper = null;
            }
            
            // Initialize cropper with passport photo aspect ratio
            try {
                cropper = new Cropper(cropImage, {
                    aspectRatio: aspectRatio,
                    viewMode: 1, // Restrict crop box within canvas
                    dragMode: 'move',
                    autoCropArea: 0.8,
                    restore: false,
                    guides: true,
                    center: true,
                    highlight: false,
                    cropBoxMovable: true,
                    cropBoxResizable: true,
                    toggleDragModeOnDblclick: false,
                    minCropBoxWidth: 100,
                    minCropBoxHeight: 100,
                    ready: function() {

                        // Enable Apply button when cropper is ready
                        cropApply.disabled = false;
                        cropApply.textContent = 'Apply Crop';
                    },
                    cropstart: function() {

                    },
                    cropend: function() {

                    }
                });
            } catch (error) {
                console.error('Error initializing cropper:', error);
                console.error('Error details:', error.message, error.stack);
                alert('Failed to initialize crop tool: ' + error.message + '. Please try refreshing the page.');
                cropApply.disabled = false;
                cropApply.textContent = 'Apply Crop';
                closeCropModal();
            }
        };
        
        cropImage.onload = function() {
            // Ensure image is fully rendered and container is ready
            setTimeout(function() {
                // Double check image dimensions
                if (cropImage.naturalWidth > 0 && cropImage.naturalHeight > 0) {
                    initCropper();
                } else {
                    console.error('Image has invalid dimensions');
                    alert('Image failed to load properly. Please try again.');
                    cropApply.disabled = false;
                    cropApply.textContent = 'Apply Crop';
                }
            }, 200);
        };
        
        cropImage.onerror = function() {
            console.error('Error loading image');
            alert('Failed to load image. Please check the image file and try again.');
            cropApply.disabled = false;
            cropApply.textContent = 'Apply Crop';
            closeCropModal();
        };
        
        // Set image source after setting handlers
        cropImage.src = imageUrl;
        
        // Fallback in case image is already cached
        if (cropImage.complete && cropImage.naturalWidth > 0 && cropImage.naturalHeight > 0) {
            cropImage.onload();
        }
    }

    function closeCropModal() {
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
        // Clean up object URL if it was created
        if (currentCropModalUrl) {
            URL.revokeObjectURL(currentCropModalUrl);
            currentCropModalUrl = null;
        }
        cropModal.classList.remove('active');
        currentCropIndex = null;
        cropImage.src = '';
        cropImage.onload = null;
        cropImage.onerror = null;
        // Reset Apply button state
        cropApply.disabled = false;
        cropApply.textContent = 'Apply Crop';
    }

    cropModalClose.addEventListener('click', closeCropModal);
    cropCancel.addEventListener('click', closeCropModal);

    // Close modal when clicking outside
    cropModal.addEventListener('click', (e) => {
        if (e.target === cropModal) {
            closeCropModal();
        }
    });

    cropApply.addEventListener('click', async () => {
        if (!cropper || currentCropIndex === null) {
            console.error('Cropper not initialized or no file selected');
            if (!cropper) {
                alert('Please wait for the image to load and the crop tool to initialize.');
            } else {
                alert('No file selected for cropping.');
            }
            return;
        }

        if (cropApply.disabled) {
            return; // Prevent clicking while loading
        }

        // Disable button while processing
        cropApply.disabled = true;
        cropApply.textContent = 'Processing...';

        try {
            // Calculate dimensions using current photo size at 300 DPI
            const targetWidth = Math.round((PHOTO_W / 2.54) * 300);
            const targetHeight = Math.round((PHOTO_H / 2.54) * 300);

            // Get cropped canvas
            let canvas = cropper.getCroppedCanvas({
                width: targetWidth,
                height: targetHeight,
                imageSmoothingEnabled: true,
                imageSmoothingQuality: 'high',
                fillColor: '#fff',
            });

            if (!canvas) {
                console.error('Failed to get cropped canvas');
                alert('Failed to crop image. Please try again.');
                cropApply.disabled = false;
                cropApply.textContent = 'Apply Crop';
                return;
            }

            // Convert canvas to blob
            canvas.toBlob((blob) => {
                if (!blob) {
                    console.error('Failed to create blob from canvas');
                    alert('Failed to process cropped image. Please try again.');
                    cropApply.disabled = false;
                    cropApply.textContent = 'Apply Crop';
                    return;
                }

                // Create a File object from the blob
                const file = fileList[currentCropIndex];
                const fileName = file.name;
                const croppedFile = new File([blob], fileName, { 
                    type: 'image/jpeg',
                    lastModified: Date.now()
                });

                // Store cropped file
                croppedFilesMap.set(currentCropIndex, croppedFile);
                
                // Update preview
                renderPreview();
                updateFileInput();
                
                // Close modal
                closeCropModal();
            }, 'image/jpeg', 0.95); // High quality JPEG
        } catch (error) {
            console.error('Error applying crop:', error);
            alert('An error occurred while applying the crop. Please try again.');
            cropApply.disabled = false;
            cropApply.textContent = 'Apply Crop';
        }
    });

    /* =====================================
       BACKGROUND REMOVAL MODAL
    ===================================== */
    function openBgRemovalModal(fileIndex) {
        const file = fileList[fileIndex];
        if (!file) return;

        // Use cropped file if available, otherwise use original
        let sourceFile = croppedFilesMap.has(fileIndex) ? croppedFilesMap.get(fileIndex) : file;
        
        currentBgRemovalIndex = fileIndex;
        
        // Read file and display in modal
        const reader = new FileReader();
        reader.onload = (e) => {
            currentBgRemovalDataUrl = e.target.result;
            bgRemovalImage.src = currentBgRemovalDataUrl;
            bgRemovalColorPicker.value = '#FFFFFF';
            bgColorPreview.style.backgroundColor = '#FFFFFF';
            bgRemovalModal.classList.add('active');
        };
        reader.onerror = () => {
            alert('Failed to read image file');
        };
        reader.readAsDataURL(sourceFile);
    }
    
    function closeBgRemovalModal() {
        bgRemovalModal.classList.remove('active');
        currentBgRemovalIndex = null;
        currentBgRemovalDataUrl = null;
    }
    
    // Background removal modal event listeners
    bgRemovalModalClose.addEventListener('click', closeBgRemovalModal);
    bgRemovalCancel.addEventListener('click', closeBgRemovalModal);
    
    bgRemovalModal.addEventListener('click', (e) => {
        if (e.target === bgRemovalModal) {
            closeBgRemovalModal();
        }
    });
    
    // Handle quick color buttons
    const colorBtnQuicks = document.querySelectorAll('.color-btn-quick');
    const colorNames = {
        '#FFFFFF': 'White',
        '#E8F4F8': 'Light Blue',
        '#F0F0F0': 'Light Gray',
        '#FFF5E6': 'Cream',
        '#000000': 'Black'
    };
    
    colorBtnQuicks.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const color = this.getAttribute('data-color');
            if (bgRemovalColorPicker) bgRemovalColorPicker.value = color;
            if (bgColorPreview) {
                bgColorPreview.style.backgroundColor = color;
                bgColorPreview.style.color = (color === '#FFFFFF' || color === '#FFE4B5' || color === '#F0F0F0' || color === '#E8F4F8') ? '#333' : '#fff';
            }
        });
    });
    
    // Handle custom color picker button - opens native color picker
    // Note: Color input is overlaid on button, so it opens automatically when clicked
    
    // Handle color picker change (after user confirms in native dialog)
    if (bgRemovalColorPicker) {
        bgRemovalColorPicker.addEventListener('change', function() {
            if (bgColorPreview) {
                bgColorPreview.style.backgroundColor = this.value;
                bgColorPreview.style.color = (this.value === '#FFFFFF' || this.value === '#FFE4B5' || this.value === '#F0F0F0' || this.value === '#E8F4F8') ? '#333' : '#fff';
            }
        });
        
        // Also update on input for real-time preview
        bgRemovalColorPicker.addEventListener('input', function() {
            if (bgColorPreview) {
                bgColorPreview.style.backgroundColor = this.value;
                bgColorPreview.style.color = (this.value === '#FFFFFF' || this.value === '#FFE4B5' || this.value === '#F0F0F0' || this.value === '#E8F4F8') ? '#333' : '#fff';
            }
        });
    }
    
    bgRemovalApply.addEventListener('click', async () => {
        if (currentBgRemovalIndex === null || !currentBgRemovalDataUrl) {
            alert('No image selected');
            return;
        }
        
        bgRemovalApply.disabled = true;
        bgRemovalApply.textContent = 'Processing...';
        
        try {
            const bgColor = bgRemovalColorPicker.value;
            let processedDataUrl;
            let isClientSide = false;
            
            // Try client-side first (fast, in browser)
            try {
                bgRemovalApply.textContent = 'Processing (client-side)...';
                isClientSide = true;
                processedDataUrl = await removeBackgroundClientSide(currentBgRemovalDataUrl, bgColor);
                console.log('Client-side background removal succeeded');
            } catch (clientError) {
                // Fall back to server-side if client-side fails
                console.warn('Client-side failed, falling back to server:', clientError);
                isClientSide = false;
                bgRemovalApply.textContent = 'Processing (server)...';
                processedDataUrl = await removeBackgroundAPI(currentBgRemovalDataUrl, bgColor);
            }

            // Convert data URL to blob
            const response = await fetch(processedDataUrl);
            const blob = await response.blob();
            
            // Create new file
            const file = fileList[currentBgRemovalIndex];
            const processedFile = new File([blob], file.name, {
                type: 'image/jpeg',
                lastModified: Date.now()
            });

            // Store processed file
            // If photo was cropped, store in croppedFilesMap to preserve both edits
            // Otherwise, store in bgRemovedFilesMap
            if (croppedFilesMap.has(currentBgRemovalIndex)) {
                // Photo was already cropped, update the cropped version with BG removed
                croppedFilesMap.set(currentBgRemovalIndex, processedFile);
            } else {
                // No crop applied yet, store in background removal map
                bgRemovedFilesMap.set(currentBgRemovalIndex, processedFile);
            }
            bgRemovedMap.set(currentBgRemovalIndex, true);

            // Update preview
            renderPreview();
            updateFileInput();
            
            // Close modal
            closeBgRemovalModal();

        } catch (error) {
            console.error('Background removal failed:', error);
            alert(`Failed to remove background: ${error.message || 'Please try again.'}`);
        } finally {
            bgRemovalApply.disabled = false;
            bgRemovalApply.textContent = 'Remove Background';
        }
    });

    /* =====================================
       UPDATE FILE INPUT WITH CROPPED FILES
    ===================================== */
    function updateFileInput() {
        // Create a new DataTransfer object to update the file input
        const dataTransfer = new DataTransfer();
        fileList.forEach((file, index) => {
            // Priority: cropped file > background removed file > original
            let fileToAdd;
            if (croppedFilesMap.has(index)) {
                fileToAdd = croppedFilesMap.get(index);
            } else if (bgRemovedFilesMap.has(index)) {
                fileToAdd = bgRemovedFilesMap.get(index);
            } else {
                fileToAdd = file;
            }
            dataTransfer.items.add(fileToAdd);
        });
        input.files = dataTransfer.files;
    }

    /* =====================================
       FORM SUBMISSION LOADING STATE
    ===================================== */
    form.addEventListener("submit", (e) => {
        // Ensure file input has cropped images
        updateFileInput();
        
        submitBtn.disabled = true;
        submitText.textContent = "Generating...";
        submitLoader.style.display = "inline-block";
    });
});
