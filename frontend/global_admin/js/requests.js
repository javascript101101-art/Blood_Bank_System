// ============================================
// Global Admin - All Requests (FIXED FOR CLINIC & COMPONENTS)
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
    // 🟢 HTML အသစ်အတိုင်း colspan ကို 9 သို့ ပြောင်းထားပါသည်
    tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: var(--text-muted);">Loading...</td></tr>';

    try {
        const result = await apiRequest('/admin/requests', { method: 'GET' });
        
        // 🟢 API Response ဖွဲ့စည်းပုံကို သေချာဖမ်းရန် (result.data က Array သက်သက်ဖြစ်နိုင်သည်)
        const requestsData = result.data || result;
        
        if (requestsData && Array.isArray(requestsData)) {
            allRequests = requestsData;
            renderTable(allRequests);
        } else {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: red;">Error loading requests.</td></tr>';
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: red;">Error loading requests.</td></tr>';
        console.error('Error loading requests:', error);
    }
}

async function loadHospitals() {
    try {
        const result = await apiRequest('/admin/stats', { method: 'GET' });
        const statsData = result.data || result;
        if (statsData && statsData.hospitals) {
            hospitals = statsData.hospitals || [];
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
        tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: var(--text-muted);">No requests found.</td></tr>';
        return;
    }

    tbody.innerHTML = requests.map(req => {
        // 🟢 သွေးအစိတ်အပိုင်း (Blood Component) ကို ရှင်းလင်းစွာ ပြသရန်
        const componentDisplay = (req.blood_component || 'Whole_Blood').replace('_', ' ').toUpperCase();
        
        // 🟢 Urgency CSS class အတွက် (ဥပမာ "Normal Request" ဆိုလျှင် "normal" ကိုသာ ယူရန်)
        const urgencyClass = req.urgency ? req.urgency.split(' ')[0].toLowerCase() : 'normal';
        const statusClass = req.status ? req.status.toLowerCase() : 'pending';

        return `
            <tr>
                <td>${req.hospital_id ? getHospitalName(req.hospital_id) : 'Unknown'}</td>
                <td><strong>${req.clinic_name || '-'}</strong></td>                 <!-- 🟢 အသစ် -->
                <td><span class="badge" style="background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; padding: 3px 8px; border-radius: 4px;">${componentDisplay}</span></td> <!-- 🟢 အသစ် -->
                <td><span class="badge">${req.blood_group || '-'}</span></td>
                <td>${req.required_date || '-'}</td>                                <!-- 🟢 အသစ် -->
                <td>${req.quantity_units || '-'}</td>                               <!-- 🟢 အသစ် -->
                <td><span class="urgency-badge urgency-${urgencyClass}">${req.urgency || '-'}</span></td>
                <td><span class="status-badge status-${statusClass}">${req.status || '-'}</span></td>
                <td>${req.requested_at ? formatDateTime(req.requested_at) : '-'}</td>
            </tr>
        `;
    }).join('');
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