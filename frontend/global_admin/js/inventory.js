// ============================================
// Global Admin - All Inventory Management (FIXED: Added Global Hub Filter)
// ============================================
let allInventory = []; // Local hospitals stock
let hospitals = [];
let globalInventory = []; // Global Central stock

document.addEventListener('DOMContentLoaded', async function() {
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    // ဆေးရုံစာရင်းကို အရင်ဆုံး ပြီးအောင် Load လုပ်ပါမည်
    await loadHospitals();

    // ဇယားများကို Load လုပ်ရန်
    loadGlobalInventory();
    loadLocalInventory();

    // Filters
    document.getElementById('applyFiltersBtn').addEventListener('click', applyFilters);
    document.getElementById('resetFiltersBtn').addEventListener('click', resetFilters);
    
    // Add Blood Form Submit
    document.getElementById('addBloodForm').addEventListener('submit', handleAddBlood);
});

// ============================================
// 🏦 ၁။ Global Central Stock (Summary)
// ============================================
async function loadGlobalInventory() {
    const tbody = document.getElementById('globalInventoryBody');
    tbody.innerHTML = '<tr><td colspan="4">Loading Global Stock...</td></tr>';

    try {
        const result = await apiRequest('/global-inventory/summary', { method: 'GET' });
        
        if (result && result.status === 200 && result.data) {
            globalInventory = result.data;
            renderGlobalTable(globalInventory);
        } else {
            tbody.innerHTML = '<tr><td colspan="4">No global inventory found.</td></tr>';
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="4">Error loading global inventory.</td></tr>';
        console.error('Error loading global inventory:', error);
    }
}

function renderGlobalTable(data) {
    const tbody = document.getElementById('globalInventoryBody');
    
    if (!data || data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4">No blood available in Global Stock.</td></tr>';
        return;
    }

    tbody.innerHTML = data.map(item => {
        const componentDisplay = (item.blood_component || 'Whole_Blood').replace('_', ' ').toUpperCase();
        
        return `
        <tr>
            <td><span class="badge">${item.blood_group}</span></td>
            <td>${item.rh_factor}</td>
            <td><span class="badge" style="background-color: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; font-size: 11px;">${componentDisplay}</span></td>
            <td style="font-weight: bold; color: #28a745;">${item.total_ml} ml</td>
        </tr>
    `}).join('');
}

// ============================================
// ➕ ၂။ Add Blood to Global Stock
// ============================================
async function handleAddBlood(e) {
    e.preventDefault(); 
    
    const supplier = document.getElementById('newSupplier').value;
    const bloodGroup = document.getElementById('newBloodGroup').value;
    const rhFactor = document.getElementById('newRhFactor').value;
    const bloodComponent = document.getElementById('newBloodComponent').value; 
    const numberOfUnits = parseInt(document.getElementById('newNumberOfUnits').value) || 1;
    const quantityMl = parseInt(document.getElementById('newQuantity').value);
    const expiryDate = document.getElementById('newExpiryDate').value;

    if (!supplier || !bloodGroup || !rhFactor || !quantityMl || quantityMl <= 0 || !expiryDate) {
        alert("Please fill in all required fields correctly.");
        return;
    }

    try {
        const payload = {
            supplier: supplier,
            blood_group: bloodGroup,
            rh_factor: rhFactor,
            blood_component: bloodComponent, 
            quantity_ml: quantityMl,
            number_of_units: numberOfUnits,
            expiry_date: expiryDate ? new Date(expiryDate).toISOString() : null,
            status: "Available",
            source_hospital_id: null, 
            source_request_id: null   
        };

        const result = await apiRequest('/global-inventory/', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        if (result && (result.status === 200 || result.status === 201)) {
            alert(`✅ Successfully added ${numberOfUnits} blood unit(s) to Global Stock!`);
            closeAddBloodModal(); 
            document.getElementById('addBloodForm').reset(); 
            loadGlobalInventory(); 
            loadLocalInventory(); 
        } else {
            alert('❌ Error: ' + (result?.data?.detail || 'Failed to add blood.'));
        }
    } catch (error) {
        console.error('Error adding blood:', error);
        alert('❌ Network error. Please try again.');
    }
}

// ============================================
// 🏥 ၃။ Local Hospitals' Stock (Detailed Table)
// ============================================
async function loadLocalInventory() {
    const tbody = document.getElementById('inventoryBody');
    tbody.innerHTML = '<tr><td colspan="9">Loading...</td></tr>';

    try {
        const result = await apiRequest('/admin/inventory', { method: 'GET' });
        
        if (result && result.status === 200 && result.data) {
            allInventory = result.data;
            renderLocalTable(allInventory);
        } else {
            tbody.innerHTML = '<tr><td colspan="9">Error loading inventory.</td></tr>';
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="9">Error loading inventory.</td></tr>';
        console.error('Error loading inventory:', error);
    }
}

function renderLocalTable(inventory) {
    const tbody = document.getElementById('inventoryBody');
    
    if (inventory.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding: 20px;">No inventory found.</td></tr>';
        return;
    }

    tbody.innerHTML = inventory.map(item => {
        const componentDisplay = (item.blood_component || 'Whole_Blood').replace('_', ' ').toUpperCase();
        
        const unitIdHtml = item.unit_id 
            ? `<span class="badge" style="background:#e0f2fe; color:#0369a1; border: 1px solid #bae6fd; font-weight:bold; font-size:11px;">${item.unit_id}</span>` 
            : `<span style="color:#94a3b8;">-</span>`;

        const supplierName = item.supplier ? item.supplier : 'Local Hospital';

        return `
        <tr>
            <td><strong>${item.hospital_id ? getHospitalName(item.hospital_id) : 'Global Hub'}</strong></td>
            <td><span style="color: #475569;">${supplierName}</span></td>
            <td>${unitIdHtml}</td> 
            <td><span class="badge">${item.blood_group}</span></td>
            <td>${item.rh_factor}</td>
            <td><span class="badge" style="background-color: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; font-size: 11px;">${componentDisplay}</span></td>
            <td><strong>${item.quantity_ml} ml</strong></td>
            <td>${item.expiry_date ? formatDate(item.expiry_date) : '-'}</td>
            <td><span class="status-badge status-${(item.status || 'Available').toLowerCase()}">${item.status || 'Available'}</span></td>
        </tr>
    `}).join('');
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
            if(select) {
                select.innerHTML = '<option value="all">ဆေးရုံအားလုံး</option>';
                
                // 🟢 Global Hub ကို Dropdown တွင် သီးသန့် ထည့်သွင်းခြင်း
                const globalOption = document.createElement('option');
                globalOption.value = 'global';
                globalOption.textContent = 'Global Hub (ကမ္ဘာ့ဗဟို)';
                globalOption.style.fontWeight = 'bold'; // ခွဲခြားသိသာစေရန် Bold လုပ်ထားပါသည်
                select.appendChild(globalOption);

                // ကျန်ရှိသော Local ဆေးရုံများကို ထည့်သွင်းခြင်း
                hospitals.forEach(h => {
                    const option = document.createElement('option');
                    option.value = h.hospital_id;
                    option.textContent = h.name;
                    select.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Error loading hospitals:', error);
    }
}

function getHospitalName(hospitalId) {
    if (!hospitalId) return 'Global Hub';
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

    // 🟢 Filter တွင် Global Hub ကို ရွေးချယ်ခဲ့လျှင် hospital_id မရှိသော (null ဖြစ်သော) Data များကိုသာ ပြသမည်
    if (hospitalFilter === 'global') {
        filtered = filtered.filter(d => !d.hospital_id);
    } else if (hospitalFilter !== 'all') {
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