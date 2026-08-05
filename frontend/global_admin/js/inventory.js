// ============================================
// Global Admin - All Inventory Management
// ============================================
let allInventory = []; // Local hospitals stock
let hospitals = [];
let globalInventory = []; // Global Central stock

document.addEventListener('DOMContentLoaded', function() {
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    // ဇယား ၂ မျိုးလုံးကို Load လုပ်ရန်
    loadGlobalInventory();
    loadLocalInventory();
    loadHospitals();

    // Filters
    document.getElementById('applyFiltersBtn').addEventListener('click', applyFilters);
    document.getElementById('resetFiltersBtn').addEventListener('click', resetFilters);
    
    // Add Blood Form Submit
    document.getElementById('addBloodForm').addEventListener('submit', handleAddBlood);
});

// ============================================
// 🏦 ၁။ Global Central Stock ကို Load လုပ်ခြင်း
// ============================================
async function loadGlobalInventory() {
    const tbody = document.getElementById('globalInventoryBody');
    tbody.innerHTML = '<tr><td colspan="3">Loading Global Stock...</td></tr>';

    try {
        // Backend က summary API ကို လှမ်းခေါ်ပါမည်
        const result = await apiRequest('/global-inventory/summary', { method: 'GET' });
        
        if (result && result.status === 200 && result.data) {
            globalInventory = result.data;
            renderGlobalTable(globalInventory);
        } else {
            tbody.innerHTML = '<tr><td colspan="3">No global inventory found.</td></tr>';
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="3">Error loading global inventory.</td></tr>';
        console.error('Error loading global inventory:', error);
    }
}

function renderGlobalTable(data) {
    const tbody = document.getElementById('globalInventoryBody');
    
    if (!data || data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3">No blood available in Global Stock.</td></tr>';
        return;
    }

    tbody.innerHTML = data.map(item => `
        <tr>
            <td><span class="badge">${item.blood_group}</span></td>
            <td>${item.rh_factor}</td>
            <td style="font-weight: bold; color: #28a745;">${item.total_ml} ml</td>
        </tr>
    `).join('');
}

// ============================================
// ➕ ၂။ Global Stock သို့ သွေးအသစ် ထည့်သွင်းခြင်း
// ============================================
async function handleAddBlood(e) {
    e.preventDefault(); // Form refresh ဖြစ်ခြင်းကို တားရန်
    
    const bloodGroup = document.getElementById('newBloodGroup').value;
    const rhFactor = document.getElementById('newRhFactor').value;
    const quantity = parseInt(document.getElementById('newQuantity').value);

    if (!bloodGroup || !rhFactor || !quantity || quantity <= 0) {
        alert("Please enter valid details.");
        return;
    }

    try {
        const payload = {
            blood_group: bloodGroup,
            rh_factor: rhFactor,
            quantity_ml: quantity,
            source_hospital_id: null, // Global ကိုယ်တိုင်ထည့်တာမို့ Null
            source_request_id: null   // Request ကလာတာမဟုတ်လို့ Null
        };

        const result = await apiRequest('/global-inventory/', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        if (result && (result.status === 200 || result.status === 201)) {
            alert('✅ Blood added to Global Stock successfully!');
            closeAddBloodModal(); // Modal ပိတ်ရန်
            document.getElementById('addBloodForm').reset(); // Form အလွတ်ပြန်ထားရန်
            loadGlobalInventory(); // ဇယားကို Data အသစ်ပြရန် Refresh လုပ်မည်
        } else {
            alert('❌ Error: ' + (result?.data?.detail || 'Failed to add blood.'));
        }
    } catch (error) {
        console.error('Error adding blood:', error);
        alert('❌ Network error. Please try again.');
    }
}

// ============================================
// 🏥 ၃။ Local Hospitals' Stock ကို Load လုပ်ခြင်း
// ============================================
async function loadLocalInventory() {
    const tbody = document.getElementById('inventoryBody');
    tbody.innerHTML = '<tr><td colspan="6">Loading...</td></tr>';

    try {
        const result = await apiRequest('/admin/inventory', { method: 'GET' });
        
        if (result && result.status === 200 && result.data) {
            allInventory = result.data;
            renderLocalTable(allInventory);
        } else {
            tbody.innerHTML = '<tr><td colspan="6">Error loading inventory.</td></tr>';
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="6">Error loading inventory.</td></tr>';
        console.error('Error loading inventory:', error);
    }
}

function renderLocalTable(inventory) {
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

// ============================================
// Helper Functions (Hospital Names, Dates, Filters)
// ============================================
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

    renderLocalTable(filtered);
}

function resetFilters() {
    document.getElementById('filterHospital').value = 'all';
    document.getElementById('filterBloodGroup').value = 'all';
    renderLocalTable(allInventory);
}