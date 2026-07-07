// ============================================
// Sync Logs Viewer
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    loadSyncLogs();

    // Refresh button
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadSyncLogs);
    }
});

// ============================================
// Load Sync Logs
// ============================================
async function loadSyncLogs() {
    const tbody = document.getElementById('syncLogsBody');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="4">Loading...</td></tr>';

    try {
        // Global Server မှာ sync_logs endpoint ရှိဖို့ လိုပါတယ်
        // အခုချိန်မှာ မရှိသေးရင် နမူနာ data ပြပါ
        tbody.innerHTML = `
            <tr>
                <td>${new Date().toLocaleString()}</td>
                <td>sync_001</td>
                <td><span class="status-badge status-success">SUCCESS</span></td>
                <td>-</td>
            </tr>
            <tr>
                <td>${new Date(Date.now() - 3600000).toLocaleString()}</td>
                <td>sync_002</td>
                <td><span class="status-badge status-success">SUCCESS</span></td>
                <td>-</td>
            </tr>
            <tr>
                <td>${new Date(Date.now() - 7200000).toLocaleString()}</td>
                <td>sync_003</td>
                <td><span class="status-badge status-failed">FAILED</span></td>
                <td>Foreign key violation</td>
            </tr>
        `;
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="4">Error loading sync logs.</td></tr>';
        console.error('Error loading sync logs:', error);
    }
}