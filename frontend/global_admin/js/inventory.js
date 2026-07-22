// ============================================
// Global Admin - All Inventory
// ============================================
let allInventory = [];
let hospitals = [];

document.addEventListener('DOMContentLoaded', function() {
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    loadInventory();
    loadHospitals();

    document.getElementById('applyFiltersBtn').addEventListener('click', applyFilters);
    document.getElementById('resetFiltersBtn').addEventListener('click', resetFilters);
});

async function loadInventory() {
    const tbody = document.getElementById('inventoryBody');
    tbody.innerHTML = '<tr><td colspan="6">Loading...</td></tr>';

    try {
        const result = await apiRequest('/admin/inventory', { method: 'GET' });
        
        if (result && result.status === 200 && result.data) {
            allInventory = result.data;
            renderTable(allInventory);
        } else {
            tbody.innerHTML = '<tr><td colspan="6">Error loading inventory.</td></tr>';
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="6">Error loading inventory.</td></tr>';
        console.error('Error loading inventory:', error);
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

function renderTable(inventory) {
    const tbody = document.getElementById('inventoryBody');
    
    if (inventory.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6">No inventory found.</td></tr>';
        return;
    }

    tbody.innerHTML = inventory.map(item => `
        <tr>
            <td>${item.hospital_id ? getHospitalName(item.hospital_id) : 'Unknown'}</td>
            <td><span class="badge">${item.blood_group}</span></td>
            <td>${item.rh_factor}</td>
            <td>${item.quantity_ml}</td>
            <td>${item.expiry_date ? formatDate(item.expiry_date) : '-'}</td>
            <td><span class="status-badge status-${item.status.toLowerCase()}">${item.status}</span></td>
        </tr>
    `).join('');
}

function getHospitalName(hospitalId) {
    const hospital = hospitals.find(h => h.hospital_id === hospitalId);
    return hospital ? hospital.name : hospitalId.substring(0, 8) + '...';
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function applyFilters() {
    const hospitalFilter = document.getElementById('filterHospital').value;
    const bloodGroupFilter = document.getElementById('filterBloodGroup').value;

    let filtered = allInventory;

    if (hospitalFilter !== 'all') {
        filtered = filtered.filter(d => d.hospital_id === hospitalFilter);
    }

    if (bloodGroupFilter !== 'all') {
        filtered = filtered.filter(d => d.blood_group === bloodGroupFilter);
    }

    renderTable(filtered);
}

function resetFilters() {
    document.getElementById('filterHospital').value = 'all';
    document.getElementById('filterBloodGroup').value = 'all';
    renderTable(allInventory);
}