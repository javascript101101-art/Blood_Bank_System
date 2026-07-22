// ============================================
// Global Blood Request (Hospital A)
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
    tbody.innerHTML = '<tr><td colspan="7">Loading...</td></tr>';

    try {
        console.log('Fetching global requests...');
        const result = await apiRequest('/global-requests/', { method: 'GET' });
        console.log('API Response:', result);

        if (result && result.status === 200 && result.data) {
            if (result.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7">No global requests found.</td></tr>';
                return;
            }
            
            // ✅ Rh Factor ထည့်ပြီးသား
            tbody.innerHTML = result.data.map(req => `
                <tr>
                    <td><span class="badge">${req.blood_group}</span></td>
                    <td>${req.rh_factor}</td>   <!-- 🆕 Rh Factor -->
                    <td>${req.quantity_ml} ml</td>
                    <td><span class="urgency-badge urgency-${req.urgency.toLowerCase()}">${req.urgency}</span></td>
                    <td><span class="status-badge status-${req.status.toLowerCase()}">${req.status}</span></td>
                    <td>${req.assigned_hospital_id ? 'Assigned' : 'Not assigned'}</td>
                    <td>${formatDateTime(req.created_at)}</td>
                </tr>
            `).join('');
        } else {
            console.error('Failed to load requests:', result);
            tbody.innerHTML = '<tr><td colspan="7">Error loading requests. Please check console.</td></tr>';
        }
    } catch (error) {
        console.error('Error loading requests:', error);
        tbody.innerHTML = '<tr><td colspan="7">Error loading requests.</td></tr>';
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