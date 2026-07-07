// ============================================
// Global Dashboard - Live Data from Global APIs
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    loadDashboardStats();
    loadSyncLogs();
});

// ============================================
// Load Dashboard Stats from Global API
// ============================================
async function loadDashboardStats() {
    try {
        const result = await apiRequest('/admin/stats', { method: 'GET' });
        
        if (result && result.status === 200 && result.data) {
            const data = result.data;
            
            // Update Stats Cards
            document.getElementById('totalDonors').textContent = data.total_donors || 0;
            document.getElementById('totalInventory').textContent = data.total_inventory || 0;
            document.getElementById('totalRequests').textContent = data.total_requests || 0;
            document.getElementById('totalHospitals').textContent = data.total_hospitals || 0;
            
            // Update Hospitals Table
            const tbody = document.getElementById('hospitalsBody');
            if (tbody && data.hospitals) {
                if (data.hospitals.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5">No hospitals found.</td></tr>';
                } else {
                    tbody.innerHTML = data.hospitals.map(h => `
                        <tr>
                            <td><strong>${h.name}</strong></td>
                            <td>${h.location || '-'}</td>
                            <td>${h.donor_count}</td>
                            <td>${h.inventory_count}</td>
                            <td>${h.request_count}</td>
                        </tr>
                    `).join('');
                }
            }
        } else {
            console.warn('Failed to load stats from Global API');
            // Show fallback message
            document.querySelectorAll('.stat-info h3').forEach(el => {
                if (el.id !== 'totalHospitals') el.textContent = '--';
            });
        }
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
        // Show fallback message
        document.querySelectorAll('.stat-info h3').forEach(el => {
            if (el.id !== 'totalHospitals') el.textContent = '--';
        });
    }
}

// ============================================
// Load Sync Logs from Global API
// ============================================
async function loadSyncLogs() {
    const tbody = document.getElementById('recentSyncBody');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="3">Loading...</td></tr>';

    try {
        const result = await apiRequest('/admin/sync-logs?limit=5', { method: 'GET' });
        
        if (result && result.status === 200 && result.data) {
            if (result.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3">No sync logs found.</td></tr>';
                return;
            }
            
            tbody.innerHTML = result.data.map(log => {
                const statusClass = log.status === 'SUCCESS' ? 'status-success' : 
                                   log.status === 'FAILED' ? 'status-failed' : 'status-pending';
                return `
                    <tr>
                        <td>${new Date(log.sync_timestamp).toLocaleString()}</td>
                        <td>Hospital A</td>
                        <td><span class="status-badge ${statusClass}">${log.status}</span></td>
                    </tr>
                `;
            }).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="3">No sync logs available.</td></tr>';
        }
    } catch (error) {
        console.error('Error loading sync logs:', error);
        tbody.innerHTML = '<tr><td colspan="3">Error loading sync logs.</td></tr>';
    }
}

// ============================================
// Utility: Format Date
// ============================================
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}