
function updateCounts(values){
    if(!values) return;
    if(typeof values.in !== 'undefined') document.getElementById('in-count').textContent = values.in;
    if(typeof values.out !== 'undefined') document.getElementById('out-count').textContent = values.out;

    if(typeof values.in !== 'undefined' && typeof values.out !== 'undefined'){
        const present = Math.max(0, values.in - values.out);
        document.getElementById('present-count').textContent = present;
    }
}


const BACKEND_URL = 'http://localhost:8000/api/counts';
const UPDATE_INTERVAL = 300; 

async function fetchCountsFromBackend(){
    try {
       
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
        
        updateCounts({ 
            in: data.in, 
            out: data.out, 
            present: data.present 
        });
        
        console.log('Updated UI - IN:', data.in, 'OUT:', data.out, 'PRESENT:', (data.in - data.out));
        
    
        document.body.style.opacity = '1';
    } catch (error){
        if (error.name !== 'AbortError') {
            console.error('Failed to fetch from backend:', error);
        }
       
        document.body.style.opacity = '0.6';
    }
}


function initializeDashboard() {

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeDashboard);
        return;
    }
    

    fetchCountsFromBackend();
    

    const _backendInterval = setInterval(fetchCountsFromBackend, UPDATE_INTERVAL);
    
    
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            fetchCountsFromBackend();
        }
    });
    

    window.updateCounts = updateCounts;
    window.fetchCountsFromBackend = fetchCountsFromBackend;
    window._backendInterval = _backendInterval;
    
    console.log('Dashboard initialized. Fetching from:', BACKEND_URL);
}



initializeDashboard();
