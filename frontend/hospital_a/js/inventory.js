// ============================================
// Inventory Management (UPDATED with Splitting Logic & Traceability)
// ============================================
let editingInventoryId = null;
let currentEditingComponent = "Whole_Blood"; // 🟢 Edit လုပ်နေသော သွေးအမျိုးအစားကို မှတ်သားထားရန်

document.addEventListener('DOMContentLoaded', function() {
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    loadInventory();

    // Modal events
    const modal = document.getElementById('inventoryModal');
    const addBtn = document.getElementById('addInventoryBtn');
    const closeBtn = document.querySelector('.close');

    if (addBtn) addBtn.addEventListener('click', () => openInventoryModal());
    if (closeBtn) closeBtn.addEventListener('click', closeInventoryModal);

    window.addEventListener('click', (e) => {
        if (e.target === modal) closeInventoryModal();
    });

    // Form submit
    const form = document.getElementById('inventoryForm');
    if (form) form.addEventListener('submit', handleInventorySubmit);
});

// ============================================
// Load Inventory
// ============================================
async function loadInventory() {
    const tbody = document.getElementById('inventoryBody');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="9" style="text-align: center;">Loading...</td></tr>';

    try {
        const result = await apiRequest('/inventory/', { method: 'GET' });
        
        if (result && result.status === 200 && result.data) {
            if (result.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="9" style="text-align: center;">No inventory records found.</td></tr>';
                return;
            }
            
            tbody.innerHTML = result.data.map(item => {
                // History Column
                let historyHtml = '<span style="color: #94a3b8;">-</span>';
                if (item.status === 'Used' && item.blood_request_id) {
                    const shortReqId = item.blood_request_id.substring(0, 8).toUpperCase();
                    historyHtml = `<span class="badge" style="background:#e2e8f0; color:#475569; font-size:11px; padding: 4px 6px; border-radius: 4px;" title="Request ID: ${item.blood_request_id}">REQ: ${shortReqId}</span>`;
                }

                // Donor Column
                let donorHtml = '<span style="color: #94a3b8;">-</span>';
                if (item.donor_id) {
                    const shortDonorId = item.donor_id.substring(0, 8).toUpperCase();
                    donorHtml = `<span class="badge" style="background:#e0e7ff; color:#3730a3; font-size:11px; padding: 4px 6px; border-radius: 4px;" title="Donor ID: ${item.donor_id}">DNR: ${shortDonorId}</span>`;
                }

                return `
                    <tr>
                        <td>${donorHtml}</td>
                        <td><strong>${item.blood_group}</strong></td>
                        <td>${item.rh_factor}</td>
                        <td><span class="badge" style="background-color: #f1f5f9; color: #334155; border: 1px solid #cbd5e1;">${item.blood_component || 'Whole_Blood'}</span></td>
                        <td>${item.quantity_ml}</td>
                        <td>${formatDate(item.expiry_date)}</td>
                        <td><span class="status-badge status-${item.status.toLowerCase()}">${item.status}</span></td>
                        <td>${historyHtml}</td>
                        <td>
                            ${item.status === 'Quarantined' ? 
                                `<button class="btn btn-info btn-sm" onclick="openSplitModal('${item.id}', ${item.quantity_ml})" title="သွေးခွဲထုတ်မည်">⚗️</button>` 
                                : ''
                            }
                            ${item.status === 'Used' ? 
                                '' 
                                : `<button class="btn btn-warning btn-sm" onclick="editInventory('${item.id}')">✏️</button>
                                   <button class="btn btn-danger btn-sm" onclick="deleteInventory('${item.id}')">🗑️</button>`
                            }
                        </td>
                    </tr>
                `;
            }).join('');
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: red;">Error loading inventory.</td></tr>';
        console.error('Error loading inventory:', error);
    }
}

// ============================================
// Open/Close Inventory Modal
// ============================================
function openInventoryModal(inventoryData = null) {
    const modal = document.getElementById('inventoryModal');
    const title = document.getElementById('modalTitle');
    const form = document.getElementById('inventoryForm');
    const errorEl = document.getElementById('inventoryFormError');
    
    errorEl.style.display = 'none';
    form.reset();
    editingInventoryId = null;
    currentEditingComponent = "Whole_Blood"; // Default reset

    if (inventoryData) {
        title.textContent = 'Edit Inventory';
        document.getElementById('inventoryId').value = inventoryData.id;
        document.getElementById('invBloodGroup').value = inventoryData.blood_group;
        document.getElementById('invRhFactor').value = inventoryData.rh_factor;
        document.getElementById('invQuantity').value = inventoryData.quantity_ml;
        document.getElementById('invExpiryDate').value = inventoryData.expiry_date;
        document.getElementById('invStatus').value = inventoryData.status;
        
        editingInventoryId = inventoryData.id;
        // 🟢 Edit လုပ်ချိန်တွင် မူလ Component အမည်ကို မှတ်သားထားပါသည်
        currentEditingComponent = inventoryData.blood_component || "Whole_Blood"; 
    } else {
        title.textContent = 'Add New Inventory';
        document.getElementById('invStatus').value = 'Available';
    }

    modal.classList.add('show');
}

function closeInventoryModal() {
    document.getElementById('inventoryModal').classList.remove('show');
    document.getElementById('inventoryForm').reset();
    document.getElementById('inventoryFormError').style.display = 'none';
    editingInventoryId = null;
    currentEditingComponent = "Whole_Blood";
}

// ============================================
// Edit & Delete Inventory
// ============================================
async function editInventory(id) {
    try {
        const result = await apiRequest(`/inventory/${id}`, { method: 'GET' });
        if (result && result.status === 200 && result.data) {
            openInventoryModal(result.data);
        }
    } catch (error) {
        alert('Error loading inventory data.');
    }
}

async function deleteInventory(id) {
    if (!confirm('Are you sure you want to delete this inventory record?')) return;

    try {
        const result = await apiRequest(`/inventory/${id}`, { method: 'DELETE' });
        if (result && (result.status === 204 || result.status === 200)) {
            loadInventory();
        } else {
            alert('Error deleting inventory record.');
        }
    } catch (error) {
        alert('Network error. Please check your connection.');
    }
}

// ============================================
// Handle Inventory Form Submit
// ============================================
async function handleInventorySubmit(e) {
    e.preventDefault();
    
    const errorEl = document.getElementById('inventoryFormError');
    errorEl.style.display = 'none';

    const inventoryData = {
        blood_group: document.getElementById('invBloodGroup').value,
        rh_factor: document.getElementById('invRhFactor').value,
        quantity_ml: parseInt(document.getElementById('invQuantity').value),
        expiry_date: document.getElementById('invExpiryDate').value,
        status: document.getElementById('invStatus').value,
        blood_component: currentEditingComponent // 🟢 မှတ်သားထားသော မူလ Component ကိုသာ ပြန်ပို့ပေးပါမည်
    };

    if (!inventoryData.blood_group || !inventoryData.rh_factor) {
        errorEl.textContent = 'Blood group and Rh factor are required.';
        errorEl.style.display = 'block';
        return;
    }

    try {
        let result;
        if (editingInventoryId) {
            result = await apiRequest(`/inventory/${editingInventoryId}`, {
                method: 'PUT',
                body: JSON.stringify(inventoryData)
            });
        } else {
            result = await apiRequest('/inventory/', {
                method: 'POST',
                body: JSON.stringify(inventoryData)
            });
        }

        if (result && (result.status === 201 || result.status === 200)) {
            closeInventoryModal();
            loadInventory();
        } else {
            errorEl.textContent = result?.data?.detail || 'Error saving inventory.';
            errorEl.style.display = 'block';
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.style.display = 'block';
    }
}

// ============================================
// Component Splitting Logic 
// ============================================
let splittingInvId = null;

function openSplitModal(id, originalMl) {
    const modal = document.getElementById('splitModal');
    const errorEl = document.getElementById('splitFormError');
    
    errorEl.style.display = 'none';
    document.getElementById('splitForm').reset();
    
    splittingInvId = id;
    document.getElementById('splitInvId').value = id;
    document.getElementById('originalQuantityDisplay').textContent = originalMl;
    
    modal.classList.add('show');
}

document.querySelectorAll('.split-close').forEach(btn => {
    btn.addEventListener('click', () => {
        document.getElementById('splitModal').classList.remove('show');
    });
});

document.getElementById('splitForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const errorEl = document.getElementById('splitFormError');
    errorEl.style.display = 'none';

    const redCells = parseInt(document.getElementById('splitRedCells').value) || 0;
    const plasma = parseInt(document.getElementById('splitPlasma').value) || 0;
    const platelets = parseInt(document.getElementById('splitPlatelets').value) || 0;

    const originalMl = parseInt(document.getElementById('originalQuantityDisplay').textContent);
    const totalSplit = redCells + plasma + platelets;

    if (totalSplit > originalMl) {
        errorEl.textContent = `ခွဲထုတ်မည့် စုစုပေါင်းပမာဏ (${totalSplit}ml) သည် မူလပမာဏ (${originalMl}ml) ထက် ကျော်လွန်နေပါသည်။`;
        errorEl.style.display = 'block';
        return;
    }

    if (totalSplit === 0) {
        errorEl.textContent = "အနည်းဆုံး သွေးအစိတ်အပိုင်း တစ်ခုခုကို ခွဲထုတ်ပါ။";
        errorEl.style.display = 'block';
        return;
    }

    const splitData = {
        red_cells_ml: redCells,
        plasma_ml: plasma,
        platelets_ml: platelets
    };

    try {
        const result = await apiRequest(`/inventory/${splittingInvId}/split`, {
            method: 'POST',
            body: JSON.stringify(splitData)
        });

        if (result && (result.status === 200 || result.status === 201)) {
            document.getElementById('splitModal').classList.remove('show');
            loadInventory();
            alert("သွေးအစိတ်အပိုင်းများ အောင်မြင်စွာ ခွဲထုတ်ပြီးပါပြီ။");
        } else {
            errorEl.textContent = result?.data?.detail || 'Error splitting inventory.';
            errorEl.style.display = 'block';
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.style.display = 'block';
    }
});

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