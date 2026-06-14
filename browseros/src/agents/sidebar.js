// BrowserOS Research Agent Worker
// Posts to the Cloud Function when user clicks \"Run Research Agent\"

const RESEARCH_API_URL = 'https://agent-research-api.vercel.app/research';

/**
 * Runs a research query via the API * @param {string} query - The research query * @param {string} user - User identifier (optional) * @returns {Promise<object>} */
export async function runResearchAgent(query, user = 'browseros-user') {
  if (!query) {
    throw new Error('Query is required');
  }
  
  try {
    console.log('[Research Agent] Starting research query:', query);
    
    const response = await fetch(RESEARCH_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user,
        query,
        timestamp: new Date().toISOString(),
      }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('[Research Agent] Response:', data);
    
    return {
      success: true,
      done: true,
      results: data,
      requestId: data.request_id,
      processedAt: data.results.processed_at,
    };
  } catch (error) {
    console.error('[Research Agent] Error:', error);
    return {
      success: false,
      error: error.message,
      done: false,
    };
  }
}

/**
 * Tests the connection to the research API * @returns {Promise<boolean>} */
export async function testConnection() {
  try {
    const response = await fetch('https://agent-research-api.vercel.app/health');
    return response.ok;
  } catch (error) {
    console.error('[Research Agent] Connection test failed:', error);
    return false;
  }
}

/**
 * Initializes the Sidebar Agent
 * This is called when BrowserOS loads */
export function initSidebarAgent() {
  console.log('[Research Agent] Sidebar agent initialized');
  
  // Test connection on startup
  testConnection().then((connected) => {
    if (connected) {
      console.log('[Research Agent] ❌ Connected to API');
    } else {
      console.warn('[Research Agent] ✆ Unable to connect to API');
    }
  });
  
  return {
    runResearchAgent,
    testConnection,
  };
}

// Default export for BrowserOS integration
export default {
  runResearchAgent,
  testConnection,
  initSidebarAgent,
};
