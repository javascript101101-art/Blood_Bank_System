// ============================================
// Blood Request Management (FIXED FOR EXTERNAL CLINIC)
// ============================================
let editingRequestId = null;
let currentUserRole = null;

document.addEventListener('DOMContentLoaded', function() {
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    const user = getUser();
    currentUserRole = user?.role || 'Hospital_Admin';

    // ★★★ Clinic အတွက် Status Dropdown ကို ဖျောက်ပါ ★★★
    // 🟢 ဒီနေရာမှာ Clinic ဟု ပြောင်းထားပါသည်
    const isClinic = currentUserRole === 'Clinic';
    const statusGroup = document.getElementById('statusGroup');
    if (statusGroup && isClinic) {
        statusGroup.style.display = 'none';
    }

    loadRequests();

    const modal = document.getElementById('requestModal');
    const addBtn = document.getElementById('addRequestBtn');
    const closeBtn = document.querySelector('.close');

    if (addBtn) {
        addBtn.addEventListener('click', () => openRequestModal());
    }

    if (closeBtn) closeBtn.addEventListener('click', closeRequestModal);

    window.addEventListener('click', (e) => {
        if (e.target === modal) closeRequestModal();
    });

    const form = document.getElementById('requestForm');
    if (form) form.addEventListener('submit', handleRequestSubmit);
});

// ============================================
// 🆕 Load Clinic Profile (Auto-Fill for Clinic)
// ============================================
async function loadClinicProfile() {
    try {
        const result = await apiRequest('/auth/profile', { method: 'GET' });
        
        if (result && result.status === 200 && result.data) {
            const data = result.data;
            
            // HTML ထဲက Input ID များကို တိုက်ဆိုင်စစ်ဆေးပြီး Data ဖြည့်ပါမည်
            const fields = [
                { id: 'reqClinicName', value: data.clinic_name },
                { id: 'reqLicense', value: data.license },
                { id: 'reqContactPhone', value: data.contact_phone },
                { id: 'reqContactEmail', value: data.contact_email },
                { id: 'reqClinicAddress', value: data.clinic_address }
            ];

            fields.forEach(field => {
                const inputEl = document.getElementById(field.id);
                if (inputEl) {
                    inputEl.value = field.value;
                    inputEl.readOnly = true; // 🟢 ပြင်၍မရအောင် ပိတ်ထားမည်
                    inputEl.style.backgroundColor = "#e9ecef"; // 🟢 မီးခိုးရောင် နောက်ခံလေးပြမည်
                }
            });
        }
    } catch (error) {
        console.error("Could not load clinic profile:", error);
    }
}

// ============================================
// Load Requests (Role-based Actions)
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
            
            tbody.innerHTML = result.data.map(req => {
                let actionButtons = '';
                let editDeleteButtons = '';

                const isAdmin = currentUserRole === 'Hospital_Admin';
                // 🟢 ဒီနေရာမှာ Clinic ဟု ပြောင်းထားပါသည်
                const isClinic = currentUserRole === 'Clinic';

                if (isAdmin) {
                    if (req.status === 'Pending') {
                        actionButtons = `
                            <button class="btn btn-success btn-sm" onclick="approveRequest('${req.id}')">✅ Approve</button>
                            <button class="btn btn-danger btn-sm" onclick="rejectRequest('${req.id}')">❌ Reject</button>
                        `;
                    } else if (req.status === 'Approved') {
                        actionButtons = `
                            <button class="btn btn-primary btn-sm" onclick="fulfillRequest('${req.id}')">📦 Fulfill</button>
                            <button class="btn btn-danger btn-sm" onclick="rejectRequest('${req.id}')">❌ Reject</button>
                        `;
                    } else if (req.status === 'Fulfilled') {
                        actionButtons = `<span class="status-badge status-fulfilled">✅ Done</span>`;
                    } else if (req.status === 'Rejected') {
                        actionButtons = `<span class="status-badge status-rejected">❌ Rejected</span>`;
                    }

                    if (req.status !== 'Fulfilled' && req.status !== 'Rejected') {
                        editDeleteButtons = `
                            <button class="btn btn-warning btn-sm" onclick="editRequest('${req.id}')">✏️</button>
                            <button class="btn btn-danger btn-sm" onclick="deleteRequest('${req.id}')">🗑️</button>
                        `;
                    }
                }

                if (isClinic) {
                    actionButtons = `<span class="status-badge status-${req.status.toLowerCase()}">${req.status}</span>`;
                    editDeleteButtons = '';
                }

                return `
                    <tr>
                        <td><strong>${req.clinic_name}</strong><br><small>${req.contact_phone}</small></td>
                        <td><span class="badge">${req.blood_group}</span></td>
                        <td>${req.required_date || '-'}</td>
                        <td>${req.quantity_units}</td>
                        <td><span class="urgency-badge urgency-${req.urgency ? req.urgency.split(' ')[0].toLowerCase() : 'normal'}">${req.urgency}</span></td>
                        <td><span class="status-badge status-${req.status.toLowerCase()}">${req.status}</span></td>
                        <td>${formatDateTime(req.requested_at || req.created_at)}</td>
                        <td>
                            ${actionButtons}
                            ${editDeleteButtons}
                        </td>
                    </tr>
                `;
            }).join('');
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="8">Error loading requests.</td></tr>';
        console.error('Error loading requests:', error);
    }
}

// ============================================
// Approve / Reject / Fulfill Functions
// ============================================
async function approveRequest(id) {
    if (!confirm('Are you sure you want to APPROVE this request?')) return;
    updateRequestStatus(id, 'Approved', '✅ Request approved successfully!');
}

async function rejectRequest(id) {
    if (!confirm('Are you sure you want to REJECT this request?')) return;
    updateRequestStatus(id, 'Rejected', '❌ Request rejected.');
}

async function fulfillRequest(id) {
    if (!confirm('Are you sure you want to FULFILL this request? This will decrease inventory.')) return;
    updateRequestStatus(id, 'Fulfilled', '✅ Request fulfilled! Inventory has been updated.');
}

async function updateRequestStatus(id, status, successMessage) {
    try {
        const result = await apiRequest(`/requests/${id}`, {
            method: 'PUT',
            body: JSON.stringify({ status: status })
        });
        if (result && (result.status === 200)) {
            alert(successMessage);
            loadRequests();
        } else {
            alert('❌ Error: ' + (result?.data?.detail || 'Could not update request.'));
        }
    } catch (error) {
        alert('❌ Network error. Please try again.');
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
        
        document.getElementById('reqClinicName').value = requestData.clinic_name;
        document.getElementById('reqLicense').value = requestData.license;
        document.getElementById('reqContactPhone').value = requestData.contact_phone;
        document.getElementById('reqContactEmail').value = requestData.contact_email;
        document.getElementById('reqClinicAddress').value = requestData.clinic_address;
        
        document.getElementById('reqBloodGroup').value = requestData.blood_group;
        document.getElementById('reqQuantity').value = requestData.quantity_units;
        document.getElementById('reqUrgency').value = requestData.urgency;
        document.getElementById('reqRequiredDate').value = requestData.required_date || '';
        document.getElementById('reqPatientCondition').value = requestData.patient_condition || '';
        document.getElementById('reqStatus').value = requestData.status;
        
        editingRequestId = requestData.id;
    } else {
        title.textContent = 'New Blood Request';
        document.getElementById('reqStatus').value = 'Pending';
        document.getElementById('reqUrgency').value = 'Normal Request';
        
        // 🟢 ဒီနေရာမှာ Clinic ဟု ပြောင်းထားပါသည်
        const isClinic = currentUserRole === 'Clinic';
        if (isClinic) {
            loadClinicProfile();
        }
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
// Edit / Delete Request (Admin Only)
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

    // 🟢 Payload ဖွဲ့စည်းခြင်း (Backend Schema နှင့် ကိုက်ညီအောင် ပြင်ဆင်ထားသည်)
    // အသစ်ဖန်တီးရာတွင် Clinic Data များ မလိုအပ်ပါ။ Backend က Auto ယူပါလိမ့်မည်။
    let requestData = {
        blood_group: document.getElementById('reqBloodGroup').value,
        quantity_units: parseInt(document.getElementById('reqQuantity').value),
        urgency: document.getElementById('reqUrgency').value,
        required_date: document.getElementById('reqRequiredDate').value,
        patient_condition: document.getElementById('reqPatientCondition').value
    };

    // 🟢 Update လုပ်ခြင်း (Admin) ဖြစ်ပါက အချက်အလက်အပြည့်အစုံကို ထည့်ပေးရပါမည်
    if (editingRequestId) {
        requestData = {
            ...requestData,
            clinic_name: document.getElementById('reqClinicName').value,
            license: document.getElementById('reqLicense').value,
            contact_phone: document.getElementById('reqContactPhone').value,
            contact_email: document.getElementById('reqContactEmail').value,
            clinic_address: document.getElementById('reqClinicAddress').value,
            status: document.getElementById('reqStatus').value
        };
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
                body: JSON.stringify(requestData) // 🟢 သွေးအမျိုးအစား၊ ပမာဏ စသည်တို့ကိုသာ ပို့ပါမည်
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