// ============================================
// Global Admin - All Requests
// ============================================
let allRequests = [];
let hospitals = [];

document.addEventListener('DOMContentLoaded', function() {
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    loadRequests();
    loadHospitals();

    document.getElementById('applyFiltersBtn').addEventListener('click', applyFilters);
    document.getElementById('resetFiltersBtn').addEventListener('click', resetFilters);
});

async function loadRequests() {
    const tbody = document.getElementById('requestsBody');
    tbody.innerHTML = '<tr><td colspan="7">Loading...</td></tr>';

    try {
        const result = await apiRequest('/admin/requests', { method: 'GET' });
        
        if (result && result.status === 200 && result.data) {
            allRequests = result.data;
            renderTable(allRequests);
        } else {
            tbody.innerHTML = '<tr><td colspan="7">Error loading requests.</td></tr>';
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="7">Error loading requests.</td></tr>';
        console.error('Error loading requests:', error);
    }
}

async function loadHospitals() {
    try {
        const result = await apiRequest('/admin/stats', { method: 'GET' });
        if (result && result.status === 200 && result.data) {
            hospitals = result.data.hospitals || [];
            const select = document.getElementById('filterHospital');
            hospitals.forEach(h => {
                const option = document.createElement('option');
                option.value = h.hospital_id;
                option.textContent = h.name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading hospitals:', error);
    }
}

function renderTable(requests) {
    const tbody = document.getElementById('requestsBody');
    
    if (requests.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7">No requests found.</td></tr>';
        return;
    }

    tbody.innerHTML = requests.map(req => `
        <tr>
            <td>${req.hospital_id ? getHospitalName(req.hospital_id) : 'Unknown'}</td>
            <td><strong>${req.patient_name}</strong></td>
            <td><span class="badge">${req.blood_group}</span></td>
            <td>${req.quantity_ml}</td>
            <td><span class="urgency-badge urgency-${req.urgency.toLowerCase()}">${req.urgency}</span></td>
            <td><span class="status-badge status-${req.status.toLowerCase()}">${req.status}</span></td>
            <td>${req.requested_at ? formatDateTime(req.requested_at) : '-'}</td>
        </tr>
    `).join('');
}

function getHospitalName(hospitalId) {
    const hospital = hospitals.find(h => h.hospital_id === hospitalId);
    return hospital ? hospital.name : hospitalId.substring(0, 8) + '...';
}

function formatDateTime(dateString) {
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

function applyFilters() {
    const hospitalFilter = document.getElementById('filterHospital').value;
    const statusFilter = document.getElementById('filterStatus').value;

    let filtered = allRequests;

    if (hospitalFilter !== 'all') {
        filtered = filtered.filter(d => d.hospital_id === hospitalFilter);
    }

    if (statusFilter !== 'all') {
        filtered = filtered.filter(d => d.status === statusFilter);
    }

    renderTable(filtered);
}

function resetFilters() {
    document.getElementById('filterHospital').value = 'all';
    document.getElementById('filterStatus').value = 'all';
    renderTable(allRequests);
}