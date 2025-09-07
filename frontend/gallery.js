document.addEventListener('DOMContentLoaded', async () => {
    const galleryContainer = document.getElementById('gallery-container');
    const loadingMessage = document.getElementById('loading-message');

    try {
        const response = await fetch('/list-campaigns');
        const campaigns = await response.json();

        if (!response.ok) {
            throw new Error(campaigns.detail || 'Failed to fetch campaign data.');
        }

        loadingMessage.style.display = 'none';

        if (Object.keys(campaigns).length === 0) {
            galleryContainer.innerHTML = '<p class="has-text-centered is-size-4">No campaigns found. Go generate some creatives!</p>';
            return;
        }

        for (const campaignName in campaigns) {
            const campaignSection = document.createElement('div');
            campaignSection.className = 'mb-6';

            const imageGrid = document.createElement('div');
            imageGrid.className = 'image-gallery'; 
            
            campaigns[campaignName].forEach(asset => {
                const card = document.createElement('div');
                card.className = 'card';
                card.innerHTML = `
                    <div class="card-image">
                        <figure class="image">
                            <img src="${asset.url}" alt="${asset.filename}">
                        </figure>
                    </div>
                    <footer class="card-footer">
                        <a href="${asset.url.replace('raw=1', 'dl=1')}" class="card-footer-item button is-primary is-fullwidth download-button" download="${asset.filename}">
                            <span class="icon is-small"><i class="fas fa-download"></i></span>
                            <span>Download</span>
                        </a>
                    </footer>
                `;
                imageGrid.appendChild(card);
            });

            if (campaigns[campaignName].length > 0) {
                 campaignSection.innerHTML = `
                    <h2 class="title is-4 is-capitalized">${campaignName}</h2>
                    <div class="is-divider" style="border-top: 1px solid #dbdbdb; height: 1px; margin: 1.5rem 0;"></div>
                `;
                campaignSection.appendChild(imageGrid);
                galleryContainer.appendChild(campaignSection);
            }
        }
    } catch (error) {
        loadingMessage.className = 'notification is-danger';
        loadingMessage.innerHTML = `<strong>Error:</strong> ${error.message}`;
        console.error('Error fetching campaigns:', error);
    }
});