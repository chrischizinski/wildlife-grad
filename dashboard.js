// Wildlife Jobs Dashboard JavaScript

class WildlifeJobsDashboard {
    constructor() {
        this.data = null;
        this.filteredJobs = [];
        this.displayedJobs = [];
        this.jobsPerPage = 12;
        this.currentPage = 0;
        
        this.init();
    }
    
    async init() {
        try {
            await this.loadData();
            this.hideLoading();
            this.setupEventListeners();
            this.renderDashboard();
        } catch (error) {
            this.showError('Failed to load job data: ' + error.message);
        }
    }
    
    async loadData() {
        try {
            const response = await fetch('./data.json');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            this.data = await response.json();
            this.filteredJobs = [...this.data.recent_jobs];
        } catch (error) {
            // Fallback: try to load from GitHub raw URL
            const repoUrl = this.getRepoUrl();
            if (repoUrl) {
                const fallbackUrl = `${repoUrl}/data/jobs_latest.json`;
                const response = await fetch(fallbackUrl);
                if (response.ok) {
                    const jobs = await response.json();
                    this.data = {
                        total_jobs: jobs.length,
                        last_updated: new Date().toISOString(),
                        recent_jobs: jobs,
                        degree_types: this.analyzeDegreeTypes(jobs),
                        locations: this.analyzeLocations(jobs),
                        salary_ranges: this.analyzeSalaryRanges(jobs),
                        research_areas: this.analyzeResearchAreas(jobs),
                        historical_data: []
                    };
                    this.filteredJobs = [...jobs];
                } else {
                    throw error;
                }
            } else {
                throw error;
            }
        }
    }
    
    getRepoUrl() {
        // Try to determine GitHub repository URL from the current page
        const hostname = window.location.hostname;
        if (hostname.includes('github.io')) {
            const parts = hostname.split('.');
            if (parts.length >= 3) {
                const username = parts[0];
                const repoName = window.location.pathname.split('/')[1] || parts[1];
                return `https://raw.githubusercontent.com/${username}/${repoName}/main`;
            }
        }
        return null;
    }
    
    // Fallback analysis methods
    analyzeDegreeTypes(jobs) {
        const counts = { PhD: 0, Masters: 0, Graduate: 0, Unspecified: 0 };
        jobs.forEach(job => {
            const title = job.title.toLowerCase();
            if (title.includes('phd') || title.includes('doctoral')) {
                counts.PhD++;
            } else if (title.includes('master') || title.includes('ms ') || title.includes('ma ')) {
                counts.Masters++;
            } else if (title.includes('graduate')) {
                counts.Graduate++;
            } else {
                counts.Unspecified++;
            }
        });
        return counts;
    }
    
    analyzeLocations(jobs) {
        const counts = {};
        jobs.forEach(job => {
            const location = job.location;
            if (location && location !== 'N/A') {
                const state = location.match(/\\b([A-Z]{2})\\b/);
                const key = state ? state[1] : location;
                counts[key] = (counts[key] || 0) + 1;
            }
        });
        return counts;
    }
    
    analyzeSalaryRanges(jobs) {
        const counts = { 'Under $20K': 0, '$20K-$30K': 0, '$30K-$40K': 0, '$40K+': 0, 'Not Listed': 0 };
        jobs.forEach(job => {
            const salary = job.salary;
            if (!salary || salary === 'N/A') {
                counts['Not Listed']++;
                return;
            }
            
            const match = salary.match(/\\$(\\d{1,3}(?:,\\d{3})*)/);
            if (match) {
                const amount = parseInt(match[1].replace(/,/g, ''));
                if (amount < 20000) counts['Under $20K']++;
                else if (amount < 30000) counts['$20K-$30K']++;
                else if (amount < 40000) counts['$30K-$40K']++;
                else counts['$40K+']++;
            } else {
                counts['Not Listed']++;
            }
        });
        return counts;
    }
    
    analyzeResearchAreas(jobs) {
        const areas = {
            'Wildlife': ['wildlife', 'animal', 'mammal', 'bird'],
            'Fisheries': ['fish', 'fisheries', 'aquatic', 'marine'],
            'Ecology': ['ecology', 'ecological', 'ecosystem'],
            'Conservation': ['conservation', 'preserve', 'protect']
        };
        
        const counts = {};
        jobs.forEach(job => {
            const text = `${job.title} ${job.tags}`.toLowerCase();
            Object.entries(areas).forEach(([area, keywords]) => {
                if (keywords.some(keyword => text.includes(keyword))) {
                    counts[area] = (counts[area] || 0) + 1;
                }
            });
        });
        return counts;
    }
    
    hideLoading() {
        document.getElementById('loading').classList.add('d-none');
        document.getElementById('main-content').classList.remove('d-none');
    }
    
    showError(message) {
        document.getElementById('loading').classList.add('d-none');
        document.getElementById('error-message').textContent = message;
        document.getElementById('error').classList.remove('d-none');
    }
    
    setupEventListeners() {
        // Search functionality
        document.getElementById('job-search').addEventListener('input', (e) => {
            this.filterJobs();
        });
        
        // Filter functionality
        document.getElementById('location-filter').addEventListener('change', (e) => {
            this.filterJobs();
        });
        
        document.getElementById('degree-filter').addEventListener('change', (e) => {
            this.filterJobs();
        });
        
        // Load more button
        document.getElementById('load-more').addEventListener('click', () => {
            this.loadMoreJobs();
        });
        
        // Download links
        const repoUrl = this.getRepoUrl();
        if (repoUrl) {
            document.getElementById('download-json').href = `${repoUrl}/data/jobs_latest.json`;
            document.getElementById('download-csv').href = `${repoUrl}/data/jobs_latest.csv`;
        }
    }
    
    renderDashboard() {
        this.renderOverview();
        this.renderCharts();
        this.renderJobListings();
        this.populateFilters();
    }
    
    renderOverview() {
        document.getElementById('total-jobs').textContent = this.data.total_jobs || 0;
        document.getElementById('new-jobs').textContent = this.data.total_jobs || 0;
        document.getElementById('locations-count').textContent = Object.keys(this.data.locations || {}).length;
        
        const lastUpdated = this.data.last_updated ? 
            new Date(this.data.last_updated).toLocaleDateString() : 'Never';
        document.getElementById('last-updated').textContent = lastUpdated;
    }
    
    renderCharts() {
        this.renderDegreeChart();
        this.renderResearchChart();
        this.renderLocationChart();
        this.renderSalaryChart();
        this.renderTrendChart();
    }
    
    renderDegreeChart() {
        const ctx = document.getElementById('degree-chart').getContext('2d');
        const data = this.data.degree_types || {};
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(data),
                datasets: [{
                    data: Object.values(data),
                    backgroundColor: [
                        '#2e7d32',
                        '#4caf50',
                        '#81c784',
                        '#c8e6c9'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    renderResearchChart() {
        const ctx = document.getElementById('research-chart').getContext('2d');
        const data = this.data.research_areas || {};
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(data),
                datasets: [{
                    label: 'Number of Jobs',
                    data: Object.values(data),
                    backgroundColor: '#4caf50'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    renderLocationChart() {
        const ctx = document.getElementById('location-chart').getContext('2d');
        const data = this.data.locations || {};
        const sortedData = Object.entries(data)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 10);
        
        new Chart(ctx, {
            type: 'horizontalBar',
            data: {
                labels: sortedData.map(([label]) => label),
                datasets: [{
                    label: 'Number of Jobs',
                    data: sortedData.map(([, value]) => value),
                    backgroundColor: '#2196f3'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    renderSalaryChart() {
        const ctx = document.getElementById('salary-chart').getContext('2d');
        const data = this.data.salary_ranges || {};
        
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: Object.keys(data),
                datasets: [{
                    data: Object.values(data),
                    backgroundColor: [
                        '#ff9800',
                        '#ff5722',
                        '#f44336',
                        '#e91e63',
                        '#9c27b0'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    renderTrendChart() {
        const ctx = document.getElementById('trend-chart').getContext('2d');
        const data = this.data.historical_data || [];
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.date),
                datasets: [{
                    label: 'Job Count',
                    data: data.map(d => d.job_count),
                    borderColor: '#2e7d32',
                    backgroundColor: 'rgba(46, 125, 50, 0.1)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    populateFilters() {
        const locationFilter = document.getElementById('location-filter');
        const locations = Object.keys(this.data.locations || {}).sort();
        
        locations.forEach(location => {
            const option = document.createElement('option');
            option.value = location;
            option.textContent = location;
            locationFilter.appendChild(option);
        });
    }
    
    filterJobs() {
        const searchTerm = document.getElementById('job-search').value.toLowerCase();
        const locationFilter = document.getElementById('location-filter').value;
        const degreeFilter = document.getElementById('degree-filter').value;
        
        this.filteredJobs = this.data.recent_jobs.filter(job => {
            const matchesSearch = !searchTerm || 
                job.title.toLowerCase().includes(searchTerm) ||
                job.organization.toLowerCase().includes(searchTerm) ||
                job.tags.toLowerCase().includes(searchTerm);
            
            const matchesLocation = !locationFilter || 
                job.location.includes(locationFilter);
            
            const matchesDegree = !degreeFilter || 
                job.title.toLowerCase().includes(degreeFilter);
            
            return matchesSearch && matchesLocation && matchesDegree;
        });
        
        this.currentPage = 0;
        this.renderJobListings();
    }
    
    renderJobListings() {
        const container = document.getElementById('job-listings');
        const startIndex = this.currentPage * this.jobsPerPage;
        const endIndex = startIndex + this.jobsPerPage;
        
        if (this.currentPage === 0) {
            container.innerHTML = '';
            this.displayedJobs = [];
        }
        
        const jobsToShow = this.filteredJobs.slice(startIndex, endIndex);
        this.displayedJobs.push(...jobsToShow);
        
        jobsToShow.forEach(job => {
            const jobCard = this.createJobCard(job);
            container.appendChild(jobCard);
        });
        
        // Show/hide load more button
        const loadMoreBtn = document.getElementById('load-more');
        if (endIndex < this.filteredJobs.length) {
            loadMoreBtn.classList.remove('d-none');
        } else {
            loadMoreBtn.classList.add('d-none');
        }
    }
    
    createJobCard(job) {
        const div = document.createElement('div');
        div.className = 'col-lg-6 col-xl-4 mb-4';
        
        div.innerHTML = `
            <div class="card job-card h-100">
                <div class="card-body">
                    <h5 class="job-title">${this.escapeHtml(job.title)}</h5>
                    <p class="job-organization">${this.escapeHtml(job.organization)}</p>
                    
                    <div class="job-details">
                        <div class="job-detail-item">
                            <i class="fas fa-map-marker-alt text-muted"></i>
                            ${this.escapeHtml(job.location)}
                        </div>
                        <div class="job-detail-item">
                            <i class="fas fa-dollar-sign text-muted"></i>
                            ${this.escapeHtml(job.salary)}
                        </div>
                        <div class="job-detail-item">
                            <i class="fas fa-calendar text-muted"></i>
                            Starts: ${this.escapeHtml(job.starting_date)}
                        </div>
                        <div class="job-detail-item">
                            <i class="fas fa-clock text-muted"></i>
                            Posted: ${this.escapeHtml(job.published_date)}
                        </div>
                    </div>
                    
                    <div class="job-tags">
                        ${this.renderJobTags(job.tags)}
                    </div>
                </div>
            </div>
        `;
        
        return div;
    }
    
    renderJobTags(tags) {
        if (!tags || tags === 'N/A') return '';
        
        return tags.split(',')
            .map(tag => tag.trim())
            .filter(tag => tag)
            .slice(0, 3) // Limit to 3 tags
            .map(tag => `<span class="job-tag">${this.escapeHtml(tag)}</span>`)
            .join('');
    }
    
    loadMoreJobs() {
        this.currentPage++;
        this.renderJobListings();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new WildlifeJobsDashboard();
});