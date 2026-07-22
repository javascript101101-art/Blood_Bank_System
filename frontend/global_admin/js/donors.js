// ============================================
// Global Admin - All Donors
// ============================================
let allDonors = [];
let hospitals = [];

document.addEventListener('DOMContentLoaded', function() {
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    loadDonors();
    loadHospitals();

    // Filter buttons
    document.getElementById('applyFiltersBtn').addEventListener('click', applyFilters);
    document.getElementById('resetFiltersBtn').addEventListener('click', resetFilters);
});

// ============================================
// Load Donors
// ============================================
async function loadDonors() {
    const tbody = document.getElementById('donorsBody');
    tbody.innerHTML = '<tr><td colspan="7">Loading...</td></tr>';

    try {
        const result = await apiRequest('/admin/donors', { method: 'GET' });
        
        if (result && result.status === 200 && result.data) {
            allDonors = result.data;
            renderTable(allDonors);
        } else {
            tbody.innerHTML = '<tr><td colspan="7">Error loading donors.</td></tr>';
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="7">Error loading donors.</td></tr>';
        console.error('Error loading donors:', error);
    }
}

// ============================================
// Load Hospitals for Filter
// ============================================
async function loadHospitals() {
    try {
        const result = await apiRequest('/admin/stats', { method: 'GET' });
        if (result && result.status === 200 && result.data) {
            hospitals = result.data.hospitals || [];
            const select = document.getElementById('filterHospital');
            
            // Add hospital options
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

// ============================================
// Render Table
// ============================================
function renderTable(donors) {
    const tbody = document.getElementById('donorsBody');
    
    if (donors.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7">No donors found.</td></tr>';
        return;
    }

    tbody.innerHTML = donors.map(donor => `
        <tr>
            <td>${donor.hospital_id ? getHospitalName(donor.hospital_id) : 'Unknown'}</td>
            <td><strong>${donor.name}</strong></td>
            <td><span class="badge">${donor.blood_group}</span></td>
            <td>${donor.rh_factor}</td>
            <td>${donor.contact_phone || '-'}</td>
            <td>${donor.email || '-'}</td>
            <td>${donor.donation_quantity ? donor.donation_quantity + 'ml' : '-'}</td>
        </tr>
    `).join('');
}

// ============================================
// Get Hospital Name by ID
// ============================================
function getHospitalName(hospitalId) {
    const hospital = hospitals.find(h => h.hospital_id === hospitalId);
    return hospital ? hospital.name : hospitalId.substring(0, 8) + '...';
}

// ============================================
// Apply Filters
// ============================================
function applyFilters() {
    const hospitalFilter = document.getElementById('filterHospital').value;
    const bloodGroupFilter = document.getElementById('filterBloodGroup').value;

    let filtered = allDonors;

    if (hospitalFilter !== 'all') {
        filtered = filtered.filter(d => d.hospital_id === hospitalFilter);
    }

    if (bloodGroupFilter !== 'all') {
        filtered = filtered.filter(d => d.blood_group === bloodGroupFilter);
    }

    renderTable(filtered);
}

// ============================================
// Reset Filters
// ============================================
function resetFilters() {
    document.getElementById('filterHospital').value = 'all';
    document.getElementById('filterBloodGroup').value = 'all';
    renderTable(allDonors);
}