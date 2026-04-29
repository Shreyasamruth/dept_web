document.addEventListener('DOMContentLoaded', () => {
    
    // File Input UI Update
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileName = this.files[0] ? this.files[0].name : 'Choose a PDF file...';
            const label = this.previousElementSibling.querySelector('#file-chosen');
            if (label) {
                label.textContent = fileName;
                // Add a little highlight animation
                label.style.color = '#34d399';
                setTimeout(() => {
                    label.style.color = '';
                }, 1000);
            }
        });
    });

    // Client-side PDF Validation
    const uploadForms = document.querySelectorAll('#uploadForm, #editForm');
    uploadForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const fileInput = this.querySelector('input[type="file"]');
            
            // If editing, file might be empty which is allowed
            if (this.id === 'editForm' && (!fileInput.files || fileInput.files.length === 0)) {
                return; // Let it submit without file
            }

            // If uploading, file is required
            if (fileInput && fileInput.files.length > 0) {
                const file = fileInput.files[0];
                const fileName = file.name;
                const fileExt = fileName.split('.').pop().toLowerCase();
                
                if (fileExt !== 'pdf') {
                    e.preventDefault();
                    alert('Please upload a valid PDF file. Other formats are not supported.');
                    // Reset input
                    fileInput.value = '';
                    const label = this.querySelector('#file-chosen');
                    if (label) label.textContent = 'Choose a PDF file...';
                }
                
                // Check file size (16MB)
                if (file.size > 16 * 1024 * 1024) {
                    e.preventDefault();
                    alert('File size exceeds 16MB limit. Please compress your PDF.');
                }
            }
        });
    });

    // Auto-dismiss Flash Messages
    const flashes = document.querySelectorAll('.flash');
    if (flashes.length > 0) {
        setTimeout(() => {
            flashes.forEach(flash => {
                flash.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                flash.style.opacity = '0';
                flash.style.transform = 'translateY(-10px)';
                setTimeout(() => {
                    flash.remove();
                }, 500);
            });
        }, 5000); // Remove after 5 seconds
    }
});
