// ============================================
// Global Admin - Global Blood Requests (UPDATED: Hospital Names)
// ============================================
let hospitals = []; // 🟢 ဆေးရုံစာရင်းများကို သိမ်းထားမည့် Array အသစ်

document.addEventListener('DOMContentLoaded', async function() {
    console.log('🟢 DOM loaded');
    if (!isAuthenticated()) {
        console.log('🔴 Not authenticated, redirecting...');
        window.location.href = 'index.html';
        return;
    }
    console.log('🟢 Authenticated, loading hospitals and requests...');
    
    // 🟢 Requests များကို မဆွဲယူမီ ဆေးရုံစာရင်းကို အရင်ဆွဲယူပါမည်
    await loadHospitals(); 
    loadRequests();
});

// ============================================
// 🏥 Helper: ဆေးရုံစာရင်း ဆွဲယူခြင်းနှင့် နာမည်ပြောင်းခြင်း
// ============================================
async function loadHospitals() {
    try {
        const result = await apiRequest('/admin/stats', { method: 'GET' });
        if (result && result.status === 200 && result.data) {
            hospitals = result.data.hospitals || [];
            console.log('✅ Hospitals loaded:', hospitals.length);
        }
    } catch (error) {
        console.error('❌ Error loading hospitals:', error);
    }
}

function getHospitalName(hospitalId) {
    if (!hospitalId) return 'Not assigned';
    const hospital = hospitals.find(h => h.hospital_id === hospitalId);
    // နာမည်တွေ့လျှင် နာမည်ပြမည်၊ မတွေ့လျှင် ID အစပိုင်းကိုသာ ပြမည်
    return hospital ? hospital.name : hospitalId.substring(0, 8) + '...';
}

async function loadRequests() {
    console.log('🟢 loadRequests() started');
    const tbody = document.getElementById('requestsBody');
    
    if (!tbody) {
        console.error('❌ tbody with id "requestsBody" not found!');
        return;
    }
    
    tbody.innerHTML = '<tr><td colspan="9" class="text-center">Loading...</td></tr>';

    try {
        console.log('📡 Fetching /global-requests/');
        const result = await apiRequest('/global-requests/', { method: 'GET' });
        console.log('📦 API Response:', result);

        if (!result) {
            console.error('❌ Result is null or undefined');
            tbody.innerHTML = '<tr><td colspan="9" class="text-center text-danger">Error: No response from server</td></tr>';
            return;
        }

        if (result.status === 200 && result.data) {
            console.log('✅ Data received:', result.data.length, 'items');
            
            if (result.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="9" class="text-center">No global requests found.</td></tr>';
                return;
            }

            // ✅ Render Table Rows with New Workflow Actions
            let html = '';
            result.data.forEach(req => {
                let actions = '';
                
                // Status စစ်ဆေးခြင်း
                if (req.status === 'PENDING' || req.status === 'Pending') {
                    actions = `
                        <!-- လမ်းကြောင်း ၁: Global မှ တိုက်ရိုက်ထုတ်ပေးရန် -->
                        <button class="btn btn-success btn-sm" onclick="approveFromGlobal('${req.id}')">🩸 Approve (Global Stock)</button>
                        
                        <!-- လမ်းကြောင်း ၂: တခြားဆေးရုံကို လှမ်းတောင်းရန် -->
                        <button class="btn btn-primary btn-sm" onclick="assignRequest('${req.id}')">🏥 Ask Hospital</button>
                        
                        <button class="btn btn-danger btn-sm" onclick="rejectRequest('${req.id}')">❌ Reject</button>
                    `;
                } else if (req.status === 'ASSIGNED' || req.status === 'Assigned') {
                    actions = `
                        <button class="btn btn-info btn-sm" onclick="fulfillRequest('${req.id}')">📦 Mark Fulfilled</button>
                        <button class="btn btn-danger btn-sm" onclick="rejectRequest('${req.id}')">❌ Reject</button>
                    `;
                } else if (req.status === 'FULFILLED' || req.status === 'Fulfilled' || req.status === 'SUPPLIER_FULFILLED' || req.status === 'Supplier_Fulfilled') {
                    actions = `
                        <button class="btn btn-warning btn-sm" onclick="deliverRequest('${req.id}')">🚚 Deliver Blood</button>
                    `;
                } else if (req.status === 'IN-TRANSIT' || req.status === 'In-Transit') {
                    actions = `<span class="status-badge status-in-transit">🚚 In Transit</span>`;
                } else if (req.status === 'DELIVERED' || req.status === 'Delivered') {
                    actions = `<span class="status-badge status-delivered" style="color: green;">✅ Delivered</span>`;
                } else if (req.status === 'REJECTED' || req.status === 'Rejected') {
                    actions = `<span class="status-badge status-rejected" style="color: red;">❌ Rejected</span>`;
                }

                // 🆕 Component အမည်ကို ယူပြီး လှပအောင် ပြင်ဆင်ခြင်း
                const componentDisplay = req.blood_component ? req.blood_component.replace('_', ' ') : 'Whole Blood';

                // 🟢 ID များအစား getHospitalName ကို အသုံးပြု၍ နာမည်များ ဖော်ပြခြင်း
                html += `
                    <tr>
                        <td><strong>${getHospitalName(req.requesting_hospital_id)}</strong></td>
                        <td><span class="badge">${req.blood_group}</span></td>
                        <td>${req.rh_factor}</td>
                        <td><span class="badge" style="background-color: #e2e8f0; color: #475569;">${componentDisplay}</span></td>
                        <td>${req.quantity_ml} ml</td>
                        <td><span class="urgency-badge urgency-${req.urgency.toLowerCase()}">${req.urgency}</span></td>
                        <td><span class="status-badge status-${req.status.toLowerCase()}">${req.status}</span></td>
                        <td>${getHospitalName(req.assigned_hospital_id)}</td>
                        <td>${actions}</td>
                    </tr>
                `;
            });
            
            tbody.innerHTML = html;
            
        } else {
            console.error('❌ Failed to load requests:', result);
            tbody.innerHTML = '<tr><td colspan="9" class="text-center text-danger">Error loading requests.</td></tr>';
        }
    } catch (error) {
        console.error('❌ Error loading requests:', error);
        tbody.innerHTML = '<tr><td colspan="9" class="text-center text-danger">Error loading requests: ' + error.message + '</td></tr>';
    }
}

// ============================================
// 🩸 Approve From Global (Pending -> Fulfilled)
// ============================================
async function approveFromGlobal(id) {
    if (!confirm('Global Inventory မှ သွေးထုတ်ပေးမည်မှာ သေချာပါသလား? (သွေးပို့ရန် အသင့်ဖြစ်ပါမည်)')) return;

    try {
        const result = await apiRequest(`/global-requests/${id}`, {
            method: 'PUT',
            body: JSON.stringify({ 
                status: 'SUPPLIER_FULFILLED', 
                assigned_hospital_id: null
            })
        });

        if (result && result.status === 200) {
            alert('✅ Global Stock မှ သွေးထုတ်ပေးရန် အသင့်ဖြစ်ပါပြီ။ (🚚 Deliver ဆက်လုပ်ပါ)');
            loadRequests();
        } else {
            alert('❌ Error: ' + (result?.data?.detail || 'Could not approve request.'));
        }
    } catch (error) {
        alert('❌ Network error. Please try again.');
    }
}

// ============================================
// 🏥 Assign Request (Pending -> Assigned)
// ============================================
async function assignRequest(id) {
    const hospitalId = prompt('Enter hospital ID to assign:');
    if (!hospitalId) return;

    try {
        const result = await apiRequest(`/global-requests/${id}/assign`, {
            method: 'POST',
            body: JSON.stringify({ hospital_id: hospitalId })
        });

        if (result && result.status === 200) {
            alert('✅ Request assigned successfully!');
            loadRequests();
        } else {
            alert('❌ Error: ' + (result?.data?.detail || 'Could not assign request.'));
        }
    } catch (error) {
        alert('❌ Network error. Please try again.');
    }
}

// ============================================
// 📦 Fulfill Request (Assigned -> Fulfilled)
// ============================================
async function fulfillRequest(id) {
    if (!confirm('Are you sure this request is FULFILLED? (Blood has arrived at Global Inventory)')) return;

    try {
        const result = await apiRequest(`/global-requests/${id}/fulfill`, {
            method: 'POST'
        });

        if (result && result.status === 200) {
            alert('✅ Request fulfilled! Blood added to Global Inventory.');
            loadRequests();
        } else {
            alert('❌ Error: ' + (result?.data?.detail || 'Could not fulfill request.'));
        }
    } catch (error) {
        alert('❌ Network error. Please try again.');
    }
}

// ============================================
// 🚚 Deliver Request (Fulfilled -> In-Transit)
// ============================================
async function deliverRequest(id) {
    if (!confirm('Are you sure you want to DELIVER this blood? (Blood will leave Global Inventory)')) return;

    try {
        const result = await apiRequest(`/global-requests/${id}/deliver`, {
            method: 'POST'
        });

        if (result && result.status === 200) {
            alert('🚚 Blood is now In-Transit to the requesting hospital!');
            loadRequests();
        } else {
            alert('❌ Error: ' + (result?.data?.detail || 'Could not deliver blood.'));
        }
    } catch (error) {
        alert('❌ Network error. Please try again.');
    }
}

// ============================================
// ❌ Reject Request
// ============================================
async function rejectRequest(id) {
    if (!confirm('Are you sure you want to REJECT this request?')) return;

    try {
        const result = await apiRequest(`/global-requests/${id}`, {
            method: 'PUT',
            body: JSON.stringify({ status: 'Rejected' })
        });

        if (result && result.status === 200) {
            alert('❌ Request rejected.');
            loadRequests();
        } else {
            alert('❌ Error: ' + (result?.data?.detail || 'Could not reject request.'));
        }
    } catch (error) {
        alert('❌ Network error. Please try again.');
    }
}