// ============================================
// Blood Request Management
// ============================================
let editingRequestId = null;

document.addEventListener('DOMContentLoaded', function() {
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    loadRequests();

    // Modal events
    const modal = document.getElementById('requestModal');
    const addBtn = document.getElementById('addRequestBtn');
    const closeBtn = document.querySelector('.close');

    if (addBtn) addBtn.addEventListener('click', () => openRequestModal());
    if (closeBtn) closeBtn.addEventListener('click', closeRequestModal);

    window.addEventListener('click', (e) => {
        if (e.target === modal) closeRequestModal();
    });

    // Form submit
    const form = document.getElementById('requestForm');
    if (form) form.addEventListener('submit', handleRequestSubmit);
});

// ============================================
// Load Requests
// ============================================
async function loadRequests() {
    const tbody = document.getElementById('requestsBody');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="8">Loading...</td></tr>';

    try {
        const result = await apiRequest('/requests/', { method: 'GET' });
        
        if (result && result.status === 200 && result.data) {
            if (result.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8">No blood requests found.</td></tr>';
                return;
            }
            
            tbody.innerHTML = result.data.map(req => `
                <tr>
                    <td><strong>${req.patient_name}</strong></td>
                    <td><span class="badge">${req.blood_group}</span></td>
                    <td>${req.rh_factor}</td>
                    <td>${req.quantity_ml}</td>
                    <td><span class="urgency-badge urgency-${req.urgency.toLowerCase()}">${req.urgency}</span></td>
                    <td><span class="status-badge status-${req.status.toLowerCase()}">${req.status}</span></td>
                    <td>${formatDateTime(req.requested_at)}</td>
                    <td>
                        <button class="btn btn-warning btn-sm" onclick="editRequest('${req.id}')">✏️</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteRequest('${req.id}')">🗑️</button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="8">Error loading requests.</td></tr>';
        console.error('Error loading requests:', error);
    }
}

// ============================================
// Open/Close Modal
// ============================================
function openRequestModal(requestData = null) {
    const modal = document.getElementById('requestModal');
    const title = document.getElementById('modalTitle');
    const form = document.getElementById('requestForm');
    const errorEl = document.getElementById('requestFormError');
    
    errorEl.style.display = 'none';
    form.reset();
    editingRequestId = null;

    if (requestData) {
        title.textContent = 'Edit Blood Request';
        document.getElementById('requestId').value = requestData.id;
        document.getElementById('reqPatientName').value = requestData.patient_name;
        document.getElementById('reqBloodGroup').value = requestData.blood_group;
        document.getElementById('reqRhFactor').value = requestData.rh_factor;
        document.getElementById('reqQuantity').value = requestData.quantity_ml;
        document.getElementById('reqUrgency').value = requestData.urgency;
        document.getElementById('reqStatus').value = requestData.status;
        editingRequestId = requestData.id;
    } else {
        title.textContent = 'New Blood Request';
        document.getElementById('reqStatus').value = 'Pending';
        document.getElementById('reqUrgency').value = 'Normal';
    }

    modal.classList.add('show');
}

function closeRequestModal() {
    document.getElementById('requestModal').classList.remove('show');
    document.getElementById('requestForm').reset();
    document.getElementById('requestFormError').style.display = 'none';
    editingRequestId = null;
}

// ============================================
// Edit Request
// ============================================
async function editRequest(id) {
    try {
        const result = await apiRequest(`/requests/${id}`, { method: 'GET' });
        if (result && result.status === 200 && result.data) {
            openRequestModal(result.data);
        }
    } catch (error) {
        alert('Error loading request data.');
    }
}

// ============================================
// Delete Request
// ============================================
async function deleteRequest(id) {
    if (!confirm('Are you sure you want to delete this request?')) return;

    try {
        const result = await apiRequest(`/requests/${id}`, { method: 'DELETE' });
        if (result && (result.status === 204 || result.status === 200)) {
            loadRequests();
        } else {
            alert('Error deleting request.');
        }
    } catch (error) {
        alert('Network error. Please check your connection.');
    }
}

// ============================================
// Handle Form Submit
// ============================================
async function handleRequestSubmit(e) {
    e.preventDefault();
    
    const errorEl = document.getElementById('requestFormError');
    errorEl.style.display = 'none';

    const requestData = {
        patient_name: document.getElementById('reqPatientName').value,
        blood_group: document.getElementById('reqBloodGroup').value,
        rh_factor: document.getElementById('reqRhFactor').value,
        quantity_ml: parseInt(document.getElementById('reqQuantity').value),
        urgency: document.getElementById('reqUrgency').value,
        status: document.getElementById('reqStatus').value
    };

    // Validation
    if (!requestData.patient_name || !requestData.blood_group || !requestData.rh_factor) {
        errorEl.textContent = 'Patient name, blood group, and Rh factor are required.';
        errorEl.style.display = 'block';
        return;
    }

    try {
        let result;
        if (editingRequestId) {
            result = await apiRequest(`/requests/${editingRequestId}`, {
                method: 'PUT',
                body: JSON.stringify(requestData)
            });
        } else {
            result = await apiRequest('/requests/', {
                method: 'POST',
                body: JSON.stringify(requestData)
            });
        }

        if (result && (result.status === 201 || result.status === 200)) {
            closeRequestModal();
            loadRequests();
        } else {
            errorEl.textContent = result?.data?.detail || 'Error saving request.';
            errorEl.style.display = 'block';
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.style.display = 'block';
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
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}