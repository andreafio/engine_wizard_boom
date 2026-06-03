/**
 * Frontend integration for Wizard Engine Boom
 * JavaScript functions to interact with the FastAPI backend
 */

// Configuration
const WIZARD_API_BASE = window.location.origin; // Use same-origin API base for Vercel
const TENANT_ID = 'boom'; // From config.py tenant_keys_json
const API_KEY = 'API_KEY_123'; // From config.py tenant_keys_json

/**
 * Test server connectivity
 * @returns {Promise<boolean>} - True if server is reachable
 */
async function testServerConnection() {
    try {
        const response = await fetch(`${WIZARD_API_BASE}/health`);
        return response.ok;
    } catch (error) {
        console.error('Server connection test failed:', error);
        return false;
    }
}

/**
 * Start a new wizard session
 * @param {Object} context - Initial context data
 * @param {Object} consent - User consent preferences
 * @returns {Promise<Object>} - Session data with wizard state
 */
async function startWizard(context = {}, consent = {}) {
    try {
        const response = await fetch(`${WIZARD_API_BASE}/v1/sessions/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Tenant-Id': TENANT_ID,
                'X-Api-Key': API_KEY
            },
            body: JSON.stringify({
                context: context,
                consent: consent
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(`Start session failed (${response.status}): ${error.detail || response.statusText}`);
        }

        const data = await response.json();
        console.log('Wizard session started:', data.session_id);
        return data;

    } catch (error) {
        console.error('Error starting wizard:', error);
        throw error;
    }
}

/**
 * Send a wizard turn (user input)
 * @param {string} sessionId - Session ID from startWizard
 * @param {string} eventId - Unique event ID for idempotency
 * @param {Object} uiEvent - Structured UI event (preferred)
 * @param {string} userMessage - Free text message (fallback)
 * @param {Object} context - Additional context
 * @returns {Promise<Object>} - Next wizard state and assistant message
 */
async function sendWizardTurn(sessionId, eventId, uiEvent = null, userMessage = null, context = {}) {
    try {
        const requestBody = {
            session_id: sessionId,
            event_id: eventId,
            context: context
        };

        if (uiEvent) {
            requestBody.ui_event = uiEvent;
        } else if (userMessage) {
            requestBody.user_message = userMessage;
        } else {
            throw new Error('Either uiEvent or userMessage must be provided');
        }

        const response = await fetch(`${WIZARD_API_BASE}/v1/wizard/turn`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Tenant-Id': TENANT_ID,
                'X-Api-Key': API_KEY
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(`Wizard turn failed: ${error.detail || response.statusText}`);
        }

        const data = await response.json();
        console.log('Wizard turn processed:', eventId);
        return data;

    } catch (error) {
        console.error('Error processing wizard turn:', error);
        throw error;
    }
}

/**
 * Generate final output (presentation and report)
 * @param {string} sessionId - Session ID from startWizard
 * @param {string} eventId - Unique event ID for idempotency
 * @param {string} format - Output format: 'json', 'html', 'pdf'
 * @returns {Promise<Object>} - Generated presentation and report
 */
async function generateWizardOutput(sessionId, eventId, format = 'json') {
    try {
        const response = await fetch(`${WIZARD_API_BASE}/v1/wizard/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Tenant-Id': TENANT_ID,
                'X-Api-Key': API_KEY
            },
            body: JSON.stringify({
                session_id: sessionId,
                event_id: eventId,
                format: format
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(`Generation failed: ${error.detail || response.statusText}`);
        }

        const data = await response.json();
        console.log('Wizard output generated:', sessionId);
        return data;

    } catch (error) {
        console.error('Error generating wizard output:', error);
        throw error;
    }
}

// Export functions for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        startWizard,
        sendWizardTurn,
        generateWizardOutput,
        testServerConnection
    };
}

// Export for browser global scope
if (typeof window !== 'undefined') {
    window.WizardAPI = {
        startWizard,
        sendWizardTurn,
        generateWizardOutput,
        testServerConnection
    };
}