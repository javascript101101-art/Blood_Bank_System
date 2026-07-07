// ============================================
// Dashboard (UPDATED with Sync Status)
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    loadDashboardStats();
    loadRecentDonors();
    loadSyncStatus();

    // Sync Button
    const syncBtn = document.getElementById('syncBtn');
    if (syncBtn) {
        syncBtn.addEventListener('click', manualSync);
    }
});

// ============================================
// Load Dashboard Stats (UPDATED with Inventory & Requests)
// ============================================
async function loadDashboardStats() {
    try {
        // Get Donors
        const donorsResult = await apiRequest('/donors/', { method: 'GET' });
        if (donorsResult && donorsResult.status === 200) {
            document.getElementById('totalDonors').textContent = donorsResult.data.length || 0;
        }

        // Get Inventory
        const inventoryResult = await apiRequest('/inventory/', { method: 'GET' });
        if (inventoryResult && inventoryResult.status === 200) {
            document.getElementById('totalInventory').textContent = inventoryResult.data.length || 0;
        }

        // Get Requests
        const requestsResult = await apiRequest('/requests/', { method: 'GET' });
        if (requestsResult && requestsResult.status === 200) {
            document.getElementById('totalRequests').textContent = requestsResult.data.length || 0;
        }

        // Get Sync Status
        await loadSyncStatus();
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

// ============================================
// Load Sync Status (NEW)
// ============================================
async function loadSyncStatus() {
    try {
        const syncResult = await apiRequest('/sync/status', { method: 'GET' });
        if (syncResult && syncResult.status === 200) {
            const data = syncResult.data;
            document.getElementById('pendingSync').textContent = data.pending_count || 0;
            
            // Update sync status message
            const statusMsg = document.getElementById('syncStatusMsg');
            if (statusMsg) {
                if (data.pending_count === 0) {
                    statusMsg.textContent = '✅ All data synced';
                    statusMsg.style.color = '#27ae60';
                } else {
                    statusMsg.textContent = `⏳ ${data.pending_count} items pending sync`;
                    statusMsg.style.color = '#f39c12';
                }
            }
            
            // Update last sync time
            const lastSyncEl = document.getElementById('lastSyncTime');
            if (lastSyncEl && data.last_sync_at) {
                lastSyncEl.textContent = `Last sync: ${formatDateTime(data.last_sync_at)}`;
            }
        }
    } catch (error) {
        console.error('Error loading sync status:', error);
    }
}

// ============================================
// Manual Sync (NEW)
// ============================================
async function manualSync() {
    const syncBtn = document.getElementById('syncBtn');
    const originalText = syncBtn.textContent;
    
    syncBtn.textContent = '⏳ Syncing...';
    syncBtn.disabled = true;

    try {
        const result = await apiRequest('/sync/push', { method: 'POST' });
        
        if (result && result.status === 200) {
            const data = result.data;
            if (data.synced > 0) {
                alert(`✅ Sync completed!\nSynced: ${data.synced}\nFailed: ${data.failed}\nConflicts: ${data.conflicts}`);
            } else {
                alert('ℹ️ No pending items to sync.');
            }
            // Reload stats
            loadSyncStatus();
        } else {
            alert('❌ Error syncing data. Please try again.');
        }
    } catch (error) {
        alert('❌ Network error. Please check your connection.');
    } finally {
        syncBtn.textContent = originalText;
        syncBtn.disabled = false;
    }
}

// ============================================
// Load Recent Donors
// ============================================
async function loadRecentDonors() {
    const tbody = document.getElementById('recentDonorsBody');
    if (!tbody) return;

    try {
        const result = await apiRequest('/donors/', { method: 'GET' });
        if (result && result.status === 200 && result.data) {
            const recent = result.data.slice(-5).reverse();
            if (recent.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3">No donors yet.</td></tr>';
                return;
            }
            tbody.innerHTML = recent.map(donor => `
                <tr>
                    <td>${donor.name}</td>
                    <td><span class="badge">${donor.blood_group} ${donor.rh_factor}</span></td>
                    <td>${donor.contact_phone || '-'}</td>
                </tr>
            `).join('');
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="3">Error loading donors.</td></tr>';
    }
}

// ============================================
// Utility Functions
// ============================================
function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}