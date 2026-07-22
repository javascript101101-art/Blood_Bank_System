// ============================================
// Global Admin - Global Blood Requests
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('🟢 DOM loaded');
    if (!isAuthenticated()) {
        console.log('🔴 Not authenticated, redirecting...');
        window.location.href = 'index.html';
        return;
    }
    console.log('🟢 Authenticated, loading requests...');
    loadRequests();
});

async function loadRequests() {
    console.log('🟢 loadRequests() started');
    const tbody = document.getElementById('requestsBody');
    
    if (!tbody) {
        console.error('❌ tbody with id "requestsBody" not found!');
        return;
    }
    
    tbody.innerHTML = '<tr><td colspan="8">Loading...</td></tr>';

    try {
        console.log('📡 Fetching /global-requests/');
        const result = await apiRequest('/global-requests/', { method: 'GET' });
        console.log('📦 API Response:', result);

        if (!result) {
            console.error('❌ Result is null or undefined');
            tbody.innerHTML = '<tr><td colspan="8">Error: No response from server</td></tr>';
            return;
        }

        if (result.status === 200 && result.data) {
            console.log('✅ Data received:', result.data.length, 'items');
            
            if (result.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8">No global requests found.</td></tr>';
                return;
            }

            // ✅ Render Table Rows
            let html = '';
            result.data.forEach(req => {
                let actions = '';
                if (req.status === 'Pending') {
                    actions = `
                        <button class="btn btn-primary btn-sm" onclick="assignRequest('${req.id}')">📌 Assign</button>
                        <button class="btn btn-danger btn-sm" onclick="rejectRequest('${req.id}')">❌ Reject</button>
                    `;
                } else if (req.status === 'Assigned') {
                    actions = `
                        <button class="btn btn-success btn-sm" onclick="approveRequest('${req.id}')">✅ Approve</button>
                        <button class="btn btn-danger btn-sm" onclick="rejectRequest('${req.id}')">❌ Reject</button>
                    `;
                } else if (req.status === 'Approved') {
                    actions = `<span class="status-badge status-approved">✅ Approved</span>`;
                } else if (req.status === 'Fulfilled') {
                    actions = `<span class="status-badge status-fulfilled">✅ Fulfilled</span>`;
                } else if (req.status === 'Rejected') {
                    actions = `<span class="status-badge status-rejected">❌ Rejected</span>`;
                }

                html += `
                    <tr>
                        <td>${req.requesting_hospital_id || 'Unknown'}</td>
                        <td><span class="badge">${req.blood_group}</span></td>
                        <td>${req.rh_factor}</td>  <!-- 🆕 -->
                        <td>${req.quantity_ml} ml</td>
                        <td><span class="urgency-badge urgency-${req.urgency.toLowerCase()}">${req.urgency}</span></td>
                        <td><span class="status-badge status-${req.status.toLowerCase()}">${req.status}</span></td>
                        <td>${req.assigned_hospital_id || 'Not assigned'}</td>
                        <td>${actions}</td>
                    </tr>
                `;
            });
            
            tbody.innerHTML = html;
            console.log('✅ Table rendered with', result.data.length, 'rows');
            
        } else {
            console.error('❌ Failed to load requests:', result);
            tbody.innerHTML = '<tr><td colspan="8">Error loading requests.</td></tr>';
        }
    } catch (error) {
        console.error('❌ Error loading requests:', error);
        tbody.innerHTML = '<tr><td colspan="8">Error loading requests: ' + error.message + '</td></tr>';
    }
}

// ============================================
// Assign Request
// ============================================
async function assignRequest(id) {
    const hospitalId = prompt('Enter hospital ID to assign:');
    if (!hospitalId) return;

    try {
        const result = await apiRequest(`/global-requests/${id}`, {
            method: 'PUT',
            body: JSON.stringify({
                status: 'Assigned',
                assigned_hospital_id: hospitalId
            })
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
// Approve Request
// ============================================
async function approveRequest(id) {
    if (!confirm('Are you sure you want to APPROVE this request?')) return;

    try {
        const result = await apiRequest(`/global-requests/${id}`, {
            method: 'PUT',
            body: JSON.stringify({ status: 'Approved' })
        });

        if (result && result.status === 200) {
            alert('✅ Request approved successfully!');
            loadRequests();
        } else {
            alert('❌ Error: ' + (result?.data?.detail || 'Could not approve request.'));
        }
    } catch (error) {
        alert('❌ Network error. Please try again.');
    }
}

// ============================================
// Reject Request
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