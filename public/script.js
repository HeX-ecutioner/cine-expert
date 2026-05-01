function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-theme') === 'dark';
    html.setAttribute('data-theme', isDark ? 'light' : 'dark');
}

function renderStars(rating) {
    const full = Math.floor(rating);
    const half = rating - full >= 0.5 ? 1 : 0;
    const empty = 5 - full - half;
    return '★'.repeat(full) + (half ? '⯨' : '') + '☆'.repeat(empty);
}

async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        if (res.ok) {
            const data = await res.json();
            document.getElementById('valTotalMovies').innerText = data.total_movies;
            document.getElementById('valTotalRatings').innerText = data.total_ratings;
            document.getElementById('valUniqueUsers').innerText = data.unique_users;

            const tbody = document.getElementById('top5TableBody');
            tbody.innerHTML = '';
            data.top5_movies.forEach(movie => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                            <td>${movie.title}</td>
                            <td>${movie.num_ratings}</td>
                            <td class="stars">${renderStars(movie.avg_rating)}</td>
                        `;
                tbody.appendChild(tr);
            });
        }
    } catch (err) {
        console.error("Failed to load stats", err);
    }
}

async function searchMovies() {
    const movieInput = document.getElementById('movieInput').value.trim() || 'Batman Begins';
    const contentWeight = document.getElementById('weightInput').value;
    const minRating = document.getElementById('ratingInput').value;

    const grid = document.getElementById('movieGrid');
    const detailsBody = document.getElementById('detailsTableBody');
    const wrapper = document.getElementById('resultsWrapper');
    const loading = document.getElementById('loading');
    const errDiv = document.getElementById('errorMessage');

    wrapper.style.display = 'none';
    errDiv.style.display = 'none';
    loading.style.display = 'block';

    try {
        const response = await fetch(`/api/recommend?movie=${encodeURIComponent(movieInput)}&content_weight=${contentWeight}&min_rating=${minRating}&top_n=10`);
        if (!response.ok) throw new Error(await response.text() || 'Failed to fetch');

        const data = await response.json();
        loading.style.display = 'none';

        if (data.recommendations && data.recommendations.length > 0) {
            document.getElementById('resultsTitle').innerText = `Top 5 recommendations for ${movieInput}`;
            document.getElementById('resultsTitle').style.display = 'block';

            // Render Top 5 grid
            grid.innerHTML = '';
            data.recommendations.slice(0, 5).forEach((movie, index) => {
                const card = document.createElement('div');
                card.className = 'movie-card';
                card.style.animationDelay = `${index * 0.1}s`;

                const poster = movie.poster_url
                    ? `<img src="${movie.poster_url}" class="movie-poster">`
                    : `<div class="no-poster">No Image</div>`;

                card.innerHTML = `
                            ${poster}
                            <div class="movie-info">
                                <div class="movie-title">${movie.title}</div>
                                <div class="movie-meta">${movie.genres.join(' | ')}</div>
                                <div class="stars">★★★★☆</div>
                                <div class="match-text">Match: ${(movie.score * 100).toFixed(1)}%</div>
                            </div>
                        `;
                grid.appendChild(card);
            });

            // Render Top 10 table
            detailsBody.innerHTML = '';
            data.recommendations.forEach((movie, index) => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                            <td>${index + 1}</td>
                            <td>${movie.title}</td>
                            <td>${movie.genres.join(' | ')}</td>
                            <td>${(movie.score * 100).toFixed(2)}%</td>
                        `;
                detailsBody.appendChild(tr);
            });

            wrapper.style.display = 'block';
            document.getElementById('detailedView').style.display = 'block';

        } else {
            errDiv.innerText = 'No recommendations found.';
            errDiv.style.display = 'block';
        }

    } catch (err) {
        loading.style.display = 'none';
        errDiv.innerText = err.message;
        errDiv.style.display = 'block';
    }
}

window.addEventListener('DOMContentLoaded', loadStats); // Run stats on load