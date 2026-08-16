// ============================================
// Global Blood Request (Local Hospital)
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    loadMyRequests();

    document.getElementById('globalRequestForm').addEventListener('submit', handleSubmit);
});

async function handleSubmit(e) {
    e.preventDefault();
    
    const errorEl = document.getElementById('formError');
    errorEl.style.display = 'none';

    const requestData = {
        blood_group: document.getElementById('reqBloodGroup').value,
        rh_factor: document.getElementById('reqRhFactor').value,
        blood_component: document.getElementById('reqBloodComponent').value, // 🟢 Component တန်ဖိုးကို ယူလိုက်ပါပြီ
        quantity_ml: parseInt(document.getElementById('reqQuantity').value),
        urgency: document.getElementById('reqUrgency').value,
        request_note: document.getElementById('reqNote').value || null
    };

    try {
        const result = await apiRequest('/global-requests/', {
            method: 'POST',
            body: JSON.stringify(requestData)
        });

        if (result && result.status === 201) {
            alert('✅ Global request sent successfully!');
            document.getElementById('globalRequestForm').reset();
            loadMyRequests();
        } else {
            errorEl.textContent = result?.data?.detail || 'Error sending request.';
            errorEl.style.display = 'block';
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.style.display = 'block';
    }
}

async function loadMyRequests() {
    const tbody = document.getElementById('requestsBody');
    // 🟢 ကော်လံ (၉) ခုဖြစ်သွားသဖြင့် colspan ကို 9 သို့ ပြောင်းထားပါသည်
    tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">Loading...</td></tr>';

    try {
        console.log('Fetching global requests...');
        const result = await apiRequest('/global-requests/', { method: 'GET' });
        console.log('API Response:', result);

        if (result && result.status === 200 && result.data) {
            if (result.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No global requests found.</td></tr>';
                return;
            }
            
            tbody.innerHTML = result.data.map(req => {
                // Action Button ကို Status ပေါ်မူတည်ပြီး ရွေးချယ်မည်
                let actionBtn = '-';
                const statusUpper = req.status.toUpperCase();
                
                // ၁။ ကိုယ်က သွေးတောင်းထားပြီး ရောက်လာတဲ့အခါ (Receive လုပ်ရန်)
                if (statusUpper === 'SUPPLIER_FULFILLED' || statusUpper === 'IN-TRANSIT') {
                    actionBtn = `<button onclick="receiveBlood('${req.id}')" class="btn btn-sm btn-success" style="background-color: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">Receive Blood</button>`;
                } 
                // ၂။ ကိုယ့်ဆီကို သွေးလှမ်းတောင်း (Assign ချ) ခံရတဲ့အခါ (Fulfill လုပ်ရန်)
                else if (statusUpper === 'ASSIGNED') {
                    actionBtn = `<button onclick="fulfillBlood('${req.id}')" class="btn btn-sm btn-primary" style="background-color: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">📦 Send Blood</button>`;
                }

                // 🟢 Component အသစ်ကို ဇယားထဲတွင် ပြသရန် ထည့်သွင်းထားပါသည်
                const componentDisplay = req.blood_component ? req.blood_component.replace('_', ' ') : 'Whole Blood';

                return `
                <tr>
                    <td><span class="badge">${req.blood_group}</span></td>
                    <td>${req.rh_factor}</td>
                    <td><span class="badge" style="background-color: #e2e8f0; color: #475569;">${componentDisplay}</span></td> <!-- 🆕 -->
                    <td>${req.quantity_ml} ml</td>
                    <td><span class="urgency-badge urgency-${req.urgency.toLowerCase()}">${req.urgency}</span></td>
                    <td><span class="status-badge status-${req.status.toLowerCase()}">${req.status}</span></td>
                    <td>${req.assigned_hospital_id ? 'Assigned' : 'Not assigned'}</td>
                    <td>${formatDateTime(req.created_at)}</td>
                    <td>${actionBtn}</td>
                </tr>
                `;
            }).join('');
        } else {
            console.error('Failed to load requests:', result);
            tbody.innerHTML = '<tr><td colspan="9" class="text-center" style="color: red;">Error loading requests. Please check console.</td></tr>';
        }
    } catch (error) {
        console.error('Error loading requests:', error);
        tbody.innerHTML = '<tr><td colspan="9" class="text-center" style="color: red;">Error loading requests.</td></tr>';
    }
}

// ==========================================
// Global သို့ သွေးပေးပို့ရန် (Fulfill)
// ==========================================
async function fulfillBlood(reqId) {
    if (!confirm('Are you sure you want to send this blood? \n(It will be deducted from your Local Inventory)')) {
        return;
    }

    try {
        const result = await apiRequest(`/global-requests/${reqId}/fulfill`, {
            method: 'POST'
        });

        if (result && result.status === 200) {
            alert('🎉 Blood fulfilled successfully! Deducted from local inventory.');
            loadMyRequests(); // Auto Refresh
        } else {
            alert(result?.data?.detail || 'Error fulfilling blood. Do you have enough inventory?');
        }
    } catch (error) {
        console.error('Error fulfilling blood:', error);
        alert('Network error while fulfilling blood.');
    }
}

// ==========================================
// Global မှ ပို့လိုက်သော သွေးကို လက်ခံရန် (Receive)
// ==========================================
async function receiveBlood(reqId) {
    if (!confirm('Are you sure you have received the blood delivery? Local inventory will be updated.')) {
        return;
    }

    try {
        const result = await apiRequest(`/global-requests/${reqId}/receive`, {
            method: 'POST'
        });

        if (result && result.status === 200) {
            alert('🎉 Blood received successfully! Local inventory has been updated.');
            loadMyRequests(); 
        } else {
            alert(result?.data?.detail || 'Error receiving blood.');
        }
    } catch (error) {
        console.error('Error receiving blood:', error);
        alert('Network error while receiving blood.');
    }
}

// ==========================================
// Global ဆီမှ Data များကို လှမ်းဆွဲယူရန် (Pull Sync)
// ==========================================
async function syncFromGlobal() {
    try {
        const response = await apiRequest('/sync/pull', {
            method: 'POST'
        });

        if (response) {
            alert('🔄 Successfully synced/pulled updates from Global Server!');
            loadMyRequests(); 
        } else {
            alert('Failed to sync from global.');
        }
    } catch (error) {
        console.error('Sync error:', error);
        alert('Network error while syncing from global server.');
    }
}

function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}