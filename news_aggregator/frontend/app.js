document.addEventListener('DOMContentLoaded', () => {
    // Set current date in the header
    const dateOptions = { weekday: 'long', month: 'long', day: 'numeric' };
    document.getElementById('current-date').textContent = new Date().toLocaleDateString('en-US', dateOptions);

    const articlesContainer = document.getElementById('articles-container');
    const totalArticlesEl = document.getElementById('total-articles');
    const totalSourcesEl = document.getElementById('total-sources');

    let previousDataString = '';

    const renderArticles = (articles) => {
        articlesContainer.innerHTML = ''; 
        
        if (!articles || articles.length === 0) {
            articlesContainer.innerHTML = '<p style="color: #888; font-family: \'Syncopate\';">WAITING FOR DATA SYNC...</p>';
            totalArticlesEl.textContent = '00';
            totalSourcesEl.textContent = '00';
            return;
        }

        // Pad numbers with leading zero for brutalist aesthetic
        const pad = (num) => num.toString().padStart(2, '0');
        
        totalArticlesEl.textContent = pad(articles.length);
        
        // Count unique sources
        const sources = new Set(articles.map(a => a.source));
        totalSourcesEl.textContent = pad(sources.size);

        articles.forEach((article, index) => {
            const card = document.createElement('div');
            card.className = 'article-card';
            card.style.animationDelay = `${index * 0.05}s`; 
            
            // Format sentiment
            const sentiment = article.sentiment_score || 0;
            let sentimentLabel = 'NEUTRAL';
            let sentimentColor = '#fff';
            
            if (sentiment > 0.2) { 
                sentimentLabel = 'POSITIVE'; 
                sentimentColor = '#4ade80'; 
            } else if (sentiment < -0.2) { 
                sentimentLabel = 'NEGATIVE'; 
                sentimentColor = '#f87171'; 
            }

            card.innerHTML = `
                <div class="article-meta">
                    <span class="article-source">${article.source}</span>
                    <span>${article.category || 'NEWS'}</span>
                </div>
                <h3 class="article-title">${article.title}</h3>
                <p class="article-content">${article.content}</p>
                <div class="article-sentiment">
                    <span>AI SENTIMENT</span>
                    <span class="sentiment-badge" style="color: ${sentimentColor}">${sentimentLabel} [${sentiment.toFixed(2)}]</span>
                </div>
            `;
            
            card.style.cursor = 'pointer';
            card.title = 'Click to open original article';
            card.addEventListener('click', () => {
                if (article.url) {
                    const userAgrees = confirm(`Do you want to visit the original source of this article?\n\nTitle: ${article.title}\nSource: ${article.source}`);
                    if (userAgrees) {
                        window.open(article.url, '_blank', 'noopener,noreferrer');
                    }
                } else {
                    alert('Original source URL is not available for this article.');
                }
            });
            
            articlesContainer.appendChild(card);
        });
    };

    const fetchData = async () => {
        try {
            // Fetch the JSON file. Added a timestamp query param to completely bust the browser cache.
            const response = await fetch(`../data/articles_export.json?t=${new Date().getTime()}`);
            
            if (!response.ok) {
                // If 404, it might mean the crawler hasn't finished its first run yet
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Simple check to see if data changed so we don't re-render and trigger animations unnecessarily
            const currentDataString = JSON.stringify(data);
            if (currentDataString !== previousDataString) {
                console.log("New data synced. Updating UI...");
                renderArticles(data);
                previousDataString = currentDataString;
            }
        } catch (error) {
            console.warn("Could not fetch articles. Ensure python server is running and crawler has exported the JSON.", error);
            // If it's the first load and we failed, show empty state
            if (previousDataString === '') {
                 renderArticles([]);
            }
        }
    };

    // Initial fetch
    fetchData();
    
    // Poll for new data every 3 seconds to create a "live" feeling
    setInterval(fetchData, 3000);
});
