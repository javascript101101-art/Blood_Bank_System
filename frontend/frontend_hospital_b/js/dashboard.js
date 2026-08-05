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
// Manual Sync (UPDATED for Two-way Sync)
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
            
            // Backend မှ အသစ်ပြင်ထားသော (Push + Pull) Response ကို ခွဲထုတ်ခြင်း
            const pushData = data.push_result || { synced: 0, failed: 0, conflicts: 0 };
            const pullData = data.pull_result || { pulled: 0 };
            
            if (pushData.synced > 0 || pullData.pulled > 0) {
                let msg = `✅ Sync completed successfully!\n\n`;
                msg += `📤 Sent to Global: ${pushData.synced} items (Failed: ${pushData.failed})\n`;
                msg += `📥 Received from Global: ${pullData.pulled} updates`;
                alert(msg);
            } else {
                alert('ℹ️ System is up to date. No pending items to sync.');
            }
            
            // Reload stats
            loadSyncStatus();
            
            // ဇယားတွေရှိရင် Auto-refresh လုပ်ရန် (Optional)
            if (typeof loadMyRequests === 'function') loadMyRequests();
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
// ============================================
// 🆕 User Management - Pending Staff Approvals
// ============================================

// Load pending users when dashboard loads
document.addEventListener('DOMContentLoaded', function() {
    // ... existing code ...
    
    // Load pending users
    loadPendingUsers();
});

// ============================================
// Load Pending Users
// ============================================
async function loadPendingUsers() {
    const tbody = document.getElementById('pendingUsersBody');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="5">Loading pending users...</td></tr>';

    try {
        const result = await apiRequest('/auth/pending-users', { method: 'GET' });
        
        if (result && result.status === 200 && result.data) {
            const pendingCount = document.getElementById('pendingCount');
            if (pendingCount) {
                pendingCount.textContent = result.data.length;
            }

            if (result.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5">✅ No pending staff registrations.</td></tr>';
                return;
            }

            tbody.innerHTML = result.data.map(user => `
                <tr>
                    <td><strong>${user.username}</strong></td>
                    <td>${user.full_name || '-'}</td>
                    <td><span class="badge">${user.role}</span></td>
                    <td>${formatDate(user.created_at)}</td>
                    <td>
                        <button class="btn btn-success btn-sm" onclick="approveUser('${user.id}')">✅ Approve</button>
                        <button class="btn btn-danger btn-sm" onclick="rejectUser('${user.id}')">❌ Reject</button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="5">Error loading pending users.</td></tr>';
        console.error('Error loading pending users:', error);
    }
}

// ============================================
// Approve User (Admin Only)
// ============================================
async function approveUser(userId) {
    if (!confirm('Are you sure you want to APPROVE this staff registration?')) return;

    try {
        const result = await apiRequest(`/auth/approve-user/${userId}`, { 
            method: 'PUT',
            body: JSON.stringify({ is_active: true })
        });

        if (result && result.status === 200) {
            alert('✅ Staff account approved successfully!');
            loadPendingUsers(); // Refresh the list
            loadDashboardStats(); // Refresh stats
        } else {
            alert('❌ Error: ' + (result?.data?.detail || 'Could not approve user.'));
        }
    } catch (error) {
        alert('❌ Network error. Please try again.');
    }
}

// ============================================
// Reject User (Admin Only)
// ============================================
async function rejectUser(userId) {
    if (!confirm('Are you sure you want to REJECT this staff registration?')) return;

    try {
        const result = await apiRequest(`/auth/approve-user/${userId}`, { 
            method: 'PUT',
            body: JSON.stringify({ is_active: false })
        });

        if (result && result.status === 200) {
            alert('❌ Staff registration rejected.');
            loadPendingUsers(); // Refresh the list
        } else {
            alert('❌ Error: ' + (result?.data?.detail || 'Could not reject user.'));
        }
    } catch (error) {
        alert('❌ Network error. Please try again.');
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