// ============================================
// Dashboard (UPDATED with Sync Status & Low Stock Warnings)
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    loadDashboardStats();
    loadRecentDonors();
    loadSyncStatus();
    loadPendingUsers();
    loadLocalLowStockWarnings(); // 🔴 ဤနေရာတွင် Low Stock Warning ကို ထည့်ခေါ်ရန်

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
                    statusMsg.textContent = '✅ ဒေတာများအားလုံး ချိတ်ဆက်ပြီးပါပြီ';
                    statusMsg.style.color = '#10b981';
                } else {
                    statusMsg.textContent = `⏳ ဒေတာ ${data.pending_count} ခု ချိတ်ဆက်ရန် ကျန်ရှိသည်`;
                    statusMsg.style.color = '#f59e0b';
                }
            }
            
            // Update last sync time
            const lastSyncEl = document.getElementById('lastSyncTime');
            if (lastSyncEl && data.last_sync_at) {
                lastSyncEl.textContent = `နောက်ဆုံးချိတ်ဆက်ချိန်: ${formatDateTime(data.last_sync_at)}`;
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
    
    syncBtn.textContent = '⏳ ချိတ်ဆက်နေသည်...';
    syncBtn.disabled = true;

    try {
        const result = await apiRequest('/sync/push', { method: 'POST' });
        
        if (result && result.status === 200) {
            const data = result.data;
            
            const pushData = data.push_result || { synced: 0, failed: 0, conflicts: 0 };
            const pullData = data.pull_result || { pulled: 0 };
            
            if (pushData.synced > 0 || pullData.pulled > 0) {
                let msg = `✅ ဒေတာချိတ်ဆက်မှု အောင်မြင်ပါသည်!\n\n`;
                msg += `📤 ပို့လိုက်သည်: ${pushData.synced} ခု (မအောင်မြင်: ${pushData.failed})\n`;
                msg += `📥 ရယူခဲ့သည်: ${pullData.pulled} ခု`;
                alert(msg);
            } else {
                alert('ℹ️ ဒေတာများ အသစ်ဆုံး အနေအထားတွင် ရှိပါသည်။');
            }
            
            loadSyncStatus();
            loadDashboardStats();
            loadLocalLowStockWarnings();
            
            if (typeof loadMyRequests === 'function') loadMyRequests();
        } else {
            alert('❌ ဒေတာချိတ်ဆက်ရာတွင် အမှားအယွင်း ရှိနေပါသည်။');
        }
    } catch (error) {
        alert('❌ Network ချိတ်ဆက်မှု မမှန်ကန်ပါ။');
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
                tbody.innerHTML = '<tr><td colspan="3">အလှူရှင် မရှိသေးပါ။</td></tr>';
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
        tbody.innerHTML = '<tr><td colspan="3">အလှူရှင် ဒေတာ ရယူ၍ မရပါ။</td></tr>';
    }
}

// ============================================
// 🆕 Load Local Low Stock Warnings (UPDATED with Component)
// ============================================
async function loadLocalLowStockWarnings() {
    const container = document.getElementById('lowStockAlertsContainer');
    if (!container) return;

    try {
        const result = await apiRequest('/inventory/low-stock-warnings?threshold=500', { method: 'GET' });
        
        if (result && result.status === 200 && result.data && result.data.alerts) {
            const alerts = result.data.alerts;
            
            if (alerts.length > 0) {
                let alertsHTML = '';
                alerts.forEach(alert => {
                    // 🟢 Component Name ကို လှပအောင် ပြောင်းခြင်း (ဥပမာ - Red_Cells -> Red Cells)
                    let compName = alert.blood_component ? alert.blood_component.replace('_', ' ') : 'Whole Blood';

                    alertsHTML += `
                        <div class="alert-warning">
                            <span class="icon">⚠️</span>
                            <!-- 🟢 ဤနေရာတွင် Component အမည် (${compName}) ကို ထည့်သွင်းထားပါသည် -->
                            <span>သတိပေးချက်: ${alert.blood_group} ${alert.rh_factor} (${compName}) သွေးပမာဏမှာ ${alert.total_quantity} ml သာ ကျန်ရှိတော့ပါ (500 ml အောက် နည်းနေပါသည်)။</span>
                        </div>
                    `;
                });
                container.innerHTML = alertsHTML;
            } else {
                container.innerHTML = '';
            }
        }
    } catch (error) {
        console.error('Error loading local low stock warnings:', error);
    }
}

// ============================================
// Load Pending Users
// ============================================
async function loadPendingUsers() {
    const tbody = document.getElementById('pendingUsersBody');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="5">ဝန်ထမ်းစာရင်း ရယူနေသည်...</td></tr>';

    try {
        const result = await apiRequest('/auth/pending-users', { method: 'GET' });
        
        if (result && result.status === 200 && result.data) {
            const pendingCount = document.getElementById('pendingCount');
            if (pendingCount) {
                pendingCount.textContent = result.data.length;
            }

            if (result.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5">✅ အတည်ပြုရန် စောင့်ဆိုင်းနေသော ဝန်ထမ်း မရှိပါ။</td></tr>';
                return;
            }

            tbody.innerHTML = result.data.map(user => `
                <tr>
                    <td><strong>${user.username}</strong></td>
                    <td>${user.full_name || '-'}</td>
                    <td><span class="badge">${user.role}</span></td>
                    <td>${formatDate(user.created_at)}</td>
                    <td>
                        <button class="btn btn-success btn-sm" onclick="approveUser('${user.id}')">✅ အတည်ပြုမည်</button>
                        <button class="btn btn-danger btn-sm" onclick="rejectUser('${user.id}')">❌ ငြင်းပယ်မည်</button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="5">ဒေတာ ရယူရာတွင် အမှားရှိသည်။</td></tr>';
        console.error('Error loading pending users:', error);
    }
}

// ============================================
// Approve User (Admin Only)
// ============================================
async function approveUser(userId) {
    if (!confirm('ဤဝန်ထမ်း အကောင့်ကို အတည်ပြုရန် သေချာပါသလား?')) return;

    try {
        const result = await apiRequest(`/auth/approve-user/${userId}`, { 
            method: 'PUT',
            body: JSON.stringify({ is_active: true })
        });

        if (result && result.status === 200) {
            alert('✅ ဝန်ထမ်းအကောင့် အတည်ပြုပြီးပါပြီ!');
            loadPendingUsers();
            loadDashboardStats();
        } else {
            alert('❌ အမှားအယွင်း ရှိနေပါသည်။');
        }
    } catch (error) {
        alert('❌ Network ချိတ်ဆက်မှု မမှန်ကန်ပါ။');
    }
}

// ============================================
// Reject User (Admin Only)
// ============================================
async function rejectUser(userId) {
    if (!confirm('ဤဝန်ထမ်း တောင်းဆိုမှုကို ပယ်ချရန် သေချာပါသလား?')) return;

    try {
        const result = await apiRequest(`/auth/approve-user/${userId}`, { 
            method: 'PUT',
            body: JSON.stringify({ is_active: false })
        });

        if (result && result.status === 200) {
            alert('❌ ဝန်ထမ်း တောင်းဆိုမှု ပယ်ချပြီးပါပြီ။');
            loadPendingUsers();
        } else {
            alert('❌ အမှားအယွင်း ရှိနေပါသည်။');
        }
    } catch (error) {
        alert('❌ Network ချိတ်ဆက်မှု မမှန်ကန်ပါ။');
    }
}

// ============================================
// Utility Functions
// ============================================
function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('my-MM', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('my-MM', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}