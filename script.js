// Update counts from backend later by calling updateCounts({ in, out, present })
function updateCounts(values){
    if(!values) return;
    // set in/out if provided
    if(typeof values.in !== 'undefined') document.getElementById('in-count').textContent = values.in;
    if(typeof values.out !== 'undefined') document.getElementById('out-count').textContent = values.out;

    // present is always IN - OUT
    if(typeof values.in !== 'undefined' && typeof values.out !== 'undefined'){
        const present = Math.max(0, values.in - values.out);
        document.getElementById('present-count').textContent = present;
    }
}

// Fetch live counts from Flask backend running on localhost:8000
const BACKEND_URL = 'http://localhost:8000/api/counts';
const UPDATE_INTERVAL = 300; // update every 300ms for faster real-time feedback

async function fetchCountsFromBackend(){
    try {
        // Add timeout for fetch (3 seconds max)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);
        
        const response = await fetch(BACKEND_URL, {
            signal: controller.signal,
            cache: 'no-cache'
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        
        console.log('Data from backend:', data);
        
        // Update the display with real data from backend
        updateCounts({ 
            in: data.in, 
            out: data.out, 
            present: data.present 
        });
        
        console.log('Updated UI - IN:', data.in, 'OUT:', data.out, 'PRESENT:', (data.in - data.out));
        
        // Restore opacity when connected
        document.body.style.opacity = '1';
    } catch (error){
        if (error.name !== 'AbortError') {
            console.error('Failed to fetch from backend:', error);
        }
        // Dim the dashboard to indicate connection issue
        document.body.style.opacity = '0.6';
    }
}

// Fetch counts immediately (wait for DOM)
function initializeDashboard() {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeDashboard);
        return;
    }
    
    // Fetch initial data
    fetchCountsFromBackend();
    
    // Update counts periodically from backend (faster interval)
    const _backendInterval = setInterval(fetchCountsFromBackend, UPDATE_INTERVAL);
    
    // Fetch again when tab becomes visible
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            fetchCountsFromBackend();
        }
    });
    
    // Expose helpers to window for debugging
    window.updateCounts = updateCounts;
    window.fetchCountsFromBackend = fetchCountsFromBackend;
    window._backendInterval = _backendInterval;
    
    console.log('Dashboard initialized. Fetching from:', BACKEND_URL);
}

// Start initialization
initializeDashboard();