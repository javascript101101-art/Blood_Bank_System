// ============================================
// Global Admin - All Donors (UPDATED & Fixed)
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
    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">Loading...</td></tr>';

    try {
        const result = await apiRequest('/admin/donors', { method: 'GET' });
        const donorsData = result.data || result; // 🟢 Array ကို သေချာဖမ်းရန်
        
        if (donorsData && Array.isArray(donorsData)) {
            allDonors = donorsData;
            renderTable(allDonors);
        } else {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">Error loading donors.</td></tr>';
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">Error loading donors.</td></tr>';
        console.error('Error loading donors:', error);
    }
}

// ============================================
// Load Hospitals for Filter
// ============================================
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

// ============================================
// Render Table
// ============================================
function renderTable(donors) {
    const tbody = document.getElementById('donorsBody');
    
    if (donors.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">No donors found.</td></tr>';
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
            <td style="text-align: center;">
                <button class="btn btn-info btn-sm" onclick="openDonorHistory('${donor.id}', '${donor.name}')" title="သွေးလှူဒါန်းမှု မှတ်တမ်းကြည့်ရန်">📜</button>
            </td>
        </tr>
    `).join('');
}

// ============================================
// 🟢 Open Donor History Modal (Fixed Display & Data Mapping)
// ============================================
async function openDonorHistory(donorId, donorName) {
    const historyModal = document.getElementById('donorHistoryModal');
    const nameEl = document.getElementById('historyDonorName');
    const tbody = document.getElementById('donorHistoryBody');

    nameEl.textContent = donorName;
    tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 15px; color: #64748b;">မှတ်တမ်းများ ရယူနေသည်...</td></tr>';
    
    // 🟢 Modal ပွင့်လာစေရန် style.display ကို flex သို့ ပြောင်းပါ
    if (historyModal) {
        historyModal.style.display = 'flex';
    }

    try {
        const result = await apiRequest(`/admin/donors/${donorId}/history`, { method: 'GET' });
        
        // 🟢 API Response မှ Data ကို Array အဖြစ် သေချာဖမ်းယူခြင်း
        const historyData = result.data || result;
        
        console.log("History API Response:", historyData); // Debug အတွက်

        if (historyData && Array.isArray(historyData)) {
            if (historyData.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 15px; color: #64748b;">ဤအလှူရှင်တွင် လှူဒါန်းမှု မှတ်တမ်းမရှိသေးပါ။</td></tr>';
                return;
            }

            tbody.innerHTML = historyData.map(item => {
                const componentDisplay = (item.blood_component || 'Whole_Blood').replace('_', ' ').toUpperCase();
                return `
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 10px;"><span class="badge" style="background-color: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; padding: 3px 8px; border-radius: 4px;">${componentDisplay}</span></td>
                        <td style="padding: 10px; font-weight: bold; color: #0f172a;">${item.quantity_ml} ml</td>
                        <td style="padding: 10px; color: #334155;">${formatDate(item.expiry_date)}</td>
                        <td style="padding: 10px; color: #334155;">${item.status}</td>
                    </tr>
                `;
            }).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 15px; color: red;">မှတ်တမ်းရယူရာတွင် အမှားအယွင်းရှိသည်။</td></tr>';
        }
    } catch (error) {
        console.error('Error loading donor history:', error);
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 15px; color: red;">Network error. Please try again.</td></tr>';
    }
}

// ============================================
// Get Hospital Name by ID
// ============================================
function getHospitalName(hospitalId) {
    const hospital = hospitals.find(h => h.hospital_id === hospitalId);
    return hospital ? hospital.name : hospitalId.substring(0, 8) + '...';
}

// ============================================
// Utility Functions
// ============================================
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
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