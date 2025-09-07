document.addEventListener('DOMContentLoaded', () => {
    const briefForm = document.getElementById('brief-form');
    const addProductBtn = document.getElementById('add-product-btn');
    const productsContainer = document.getElementById('products-container');
    const submitBtn = document.getElementById('submit-btn');
    const imageGallery = document.getElementById('image-gallery');
    const colorInput = document.getElementById('brand-colors');
    const tagsContainer = document.getElementById('tags-container');
    const notificationContainer = document.getElementById('notification-container');
    
    // --- NEW: Selectors for new UI elements ---
    const addImageBtn = document.getElementById('add-image-btn');
    const addImageButtonContainer = document.getElementById('add-image-button-container');
    const baseImageContainer2 = document.getElementById('base-image-container-2');
    const baseImageFile1 = document.getElementById('base-image-file-1');
    const baseImageFile2 = document.getElementById('base-image-file-2');
    const fileName1 = document.getElementById('file-name-1');
    const fileName2 = document.getElementById('file-name-2');

    let productCount = 1;

    // --- NEW: Event listener to show the second image uploader ---
    addImageBtn.addEventListener('click', () => {
        baseImageContainer2.style.display = 'block';
        addImageButtonContainer.style.display = 'none'; // Hide the button after click
    });

    // --- NEW: Event listeners to update filename display ---
    baseImageFile1.addEventListener('change', () => {
        fileName1.textContent = baseImageFile1.files.length > 0 ? baseImageFile1.files[0].name : 'No file selected';
    });
    baseImageFile2.addEventListener('change', () => {
        fileName2.textContent = baseImageFile2.files.length > 0 ? baseImageFile2.files[0].name : 'No file selected';
    });

    function addNewProduct(name = '', description = '') {
        const productId = productCount;
        const newProductHtml = `
            <div class="field" data-product-id="${productId}">
                <label class="label">Product ${productId}</label>
                <input class="input" type="text" placeholder="Product Name" id="product-name-${productId}" value="${name}" required>
            </div>
            <div class="field">
                <label class="label">Product Description</label>
                <textarea class="textarea" placeholder="Describe the product" id="product-description-${productId}" required>${description}</textarea>
            </div>
            <hr>`;
        productsContainer.insertAdjacentHTML('beforeend', newProductHtml);
        productCount++;
    }

    function setDefaultValues() {
        document.getElementById('campaign-name').value = 'Summer Launch 2025';
        document.getElementById('region').value = 'North America';
        document.getElementById('audience').value = 'Dog owners, pet lovers';
        document.getElementById('message').value = 'The perfect collar for your best friend!';
        productsContainer.innerHTML = '';
        productCount = 1;
        addNewProduct('Dog Collar', 'A durable and stylish collar for medium-sized dogs.');
        tagsContainer.querySelectorAll('.tag').forEach(t => t.remove());
        ['Blue', 'White'].forEach(color => addTag(color));
    }

    setDefaultValues();

    colorInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ',' || e.key === ' ') {
            e.preventDefault();
            const color = colorInput.value.trim();
            if (color) { addTag(color); colorInput.value = ''; }
        }
    });

    function addTag(text) {
        const tag = document.createElement('span');
        tag.className = 'tag';
        tag.innerHTML = `${text}<button class="delete"></button>`;
        tagsContainer.insertBefore(tag, colorInput);
        tag.querySelector('.delete').addEventListener('click', () => tag.remove());
    }
    
    addProductBtn.addEventListener('click', () => {
        addNewProduct();
    });

    briefForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const products = {};
        productsContainer.querySelectorAll('[data-product-id]').forEach(field => {
            const id = field.dataset.productId;
            const name = document.getElementById(`product-name-${id}`).value;
            const description = document.getElementById(`product-description-${id}`).value;
            if (name && description) { products[name] = { description }; }
        });

        if (Object.keys(products).length === 0) {
            showNotification('Please add at least one product with a description.', 'is-danger');
            return;
        }

        const baseImageDesc1 = document.getElementById('base-image-desc-1').value;
        const baseImageDesc2 = document.getElementById('base-image-desc-2').value;

        if (baseImageFile1.files[0] && !baseImageDesc1.trim()) {
            showNotification('Please provide a description for Base Image 1.', 'is-danger');
            return;
        }
        if (baseImageFile2.files[0] && !baseImageDesc2.trim()) {
            showNotification('Please provide a description for Base Image 2.', 'is-danger');
            return;
        }
        
        submitBtn.classList.add('is-loading');
        imageGallery.innerHTML = '';
        notificationContainer.innerHTML = '';

        const brandColors = Array.from(tagsContainer.querySelectorAll('.tag')).map(tag => tag.textContent.trim());
        const brief = {
            campaign_name: document.getElementById('campaign-name').value,
            region: document.getElementById('region').value,
            audience: document.getElementById('audience').value,
            message: document.getElementById('message').value,
            brand_colors: brandColors,
            products: products,
        };
        
        const formData = new FormData();
        formData.append('brief_data', JSON.stringify(brief));

        if (baseImageFile1.files[0] && baseImageDesc1) {
            formData.append('base_image_1', baseImageFile1.files[0]);
            formData.append('base_image_desc_1', baseImageDesc1);
        }
        if (baseImageFile2.files[0] && baseImageDesc2) {
            formData.append('base_image_2', baseImageFile2.files[0]);
            formData.append('base_image_desc_2', baseImageDesc2);
        }

        try {
            const response = await fetch('/process-brief', { method: 'POST', body: formData });
            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || 'An unknown error occurred.');
            }
            
            if (result.image_urls && result.image_urls.length > 0) {
                result.image_urls.forEach(url => {
                    const card = document.createElement('div');
                    card.className = 'card';
                    const filename = new URL(url).pathname.split('/').pop();
                    const prettyFilename = decodeURIComponent(filename);
                    const match = prettyFilename.match(/_(\d+x\d+)_/);
                    const aspectRatioLabel = match ? match[1].replace('x', ':') : 'Creative';
                    
                    card.innerHTML = `
                        <header class="card-header"><p class="card-header-title is-centered">${aspectRatioLabel}</p></header>
                        <div class="card-image"><figure class="image"><img src="${url}" alt="Generated Creative"></figure></div>
                        <footer class="card-footer">
                            <a href="${url.replace('raw=1', 'dl=1')}" class="card-footer-item button is-primary is-fullwidth download-button" download="${prettyFilename}">
                                <span class="icon is-small"><i class="fas fa-download"></i></span>
                                <span>Download</span>
                            </a>
                        </footer>
                    `;
                    imageGallery.appendChild(card);
                });
                showNotification('Assets generated and uploaded successfully!', 'is-success');
            } else {
                showNotification(result.message || 'No images were generated for this brief.', 'is-warning');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification(`An error occurred: ${error.message}`, 'is-danger');
        } finally {
            submitBtn.classList.remove('is-loading');
        }
    });

    function showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `<button class="delete"></button>${message}`;
        notificationContainer.appendChild(notification);
        notification.querySelector('.delete').addEventListener('click', () => notification.remove());
        setTimeout(() => notification.remove(), 8000);
    }
});