/**
 * API Client for Elite Crew Dashboard
 * Handles all REST API communications with the backend
 */

class ApiClient {
    constructor() {
        this.baseUrl = '';
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return await response.text();
        } catch (error) {
            console.error(`API request failed for ${endpoint}:`, error);
            throw error;
        }
    }

    // System Status
    async getSystemStatus() {
        return this.request('/api/system/status');
    }

    // Projects
    async getProjects(limit = 10, offset = 0) {
        return this.request(`/api/projects?limit=${limit}&offset=${offset}`);
    }

    async createProject(projectData) {
        return this.request('/api/projects/create', {
            method: 'POST',
            body: JSON.stringify(projectData)
        });
    }

    async executeProject(projectId) {
        return this.request(`/api/projects/${projectId}/execute`, {
            method: 'POST'
        });
    }

    // Tasks
    async getProjectTasks(projectId) {
        return this.request(`/api/projects/${projectId}/tasks`);
    }

    async createTask(projectId, taskData) {
        return this.request(`/api/projects/${projectId}/tasks/create`, {
            method: 'POST',
            body: JSON.stringify(taskData)
        });
    }

    async updateTaskStatus(taskId, statusData) {
        return this.request(`/api/tasks/${taskId}/status`, {
            method: 'POST',
            body: JSON.stringify(statusData)
        });
    }

    // Agents
    async getAgents() {
        return this.request('/api/agents');
    }

    // Metrics
    async getMetrics() {
        return this.request('/api/metrics');
    }

    // Utility methods
    async ping() {
        try {
            await this.request('/api/system/status');
            return true;
        } catch (error) {
            return false;
        }
    }

    // Batch requests
    async batchRequest(requests) {
        const promises = requests.map(req => 
            this.request(req.endpoint, req.options).catch(error => ({
                error: error.message,
                endpoint: req.endpoint
            }))
        );

        return Promise.all(promises);
    }
}

// Create global instance
window.apiClient = new ApiClient();