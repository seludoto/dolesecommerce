// Image Fallback Handler
function setupImageFallbacks() {
    // Handle missing static images
    document.querySelectorAll('img[src*="static/images"]').forEach(img => {
        img.addEventListener('error', function() {
            console.log('Failed to load image:', this.src);
            
            // Create fallback div
            const fallback = document.createElement('div');
            fallback.className = 'image-fallback no-image-placeholder';
            fallback.style.width = this.width || this.style.width || '100px';
            fallback.style.height = this.height || this.style.height || '100px';
            fallback.innerHTML = 'Image<br>Not Found';
            
            // Replace image with fallback
            this.parentNode.replaceChild(fallback, this);
        });
    });
    
    // Handle missing product images
    document.querySelectorAll('img[src*="product_images"]').forEach(img => {
        img.addEventListener('error', function() {
            console.log('Failed to load product image:', this.src);
            
            // Create product fallback
            const fallback = document.createElement('div');
            fallback.className = 'image-fallback product-placeholder';
            fallback.style.width = this.width || this.style.width || '150px';
            fallback.style.height = this.height || this.style.height || '150px';
            fallback.innerHTML = 'Product<br>Image';
            
            // Replace image with fallback
            this.parentNode.replaceChild(fallback, this);
        });
    });
}

// Run when DOM is loaded
document.addEventListener('DOMContentLoaded', setupImageFallbacks);
